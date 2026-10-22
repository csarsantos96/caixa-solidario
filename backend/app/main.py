"""Authenticated API for a single event operator. All money values are integer cents."""
import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import delete, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from .catalog import CATALOG
from .config import Settings
from .database import Base, build_engine
from .models import Event, DisplayState, LoginSession, Product, Sale
from .receipts import receipt_text, receipt_html
from .schemas import EventInput, DisplayInput, LoginInput, ProductInput, SaleInput, StatusInput
from .weights import weight_from_name

COOKIE = "caixa_session"
def now_iso():
    return datetime.now(timezone.utc).isoformat()

def product_dict(p):
    return {"id": p.id, "name": p.name, "category": p.category, "price": p.price,
            "cost": p.cost, "weight_grams": p.weight_grams, "active": int(p.active)}

def sale_dict(s):
    return {"id": s.id, "createdAt": s.created_at, "event": s.event,
            "items": json.dumps(s.items, ensure_ascii=False), "total": s.total,
            "cost": s.cost, "status": s.status, "method": s.method,
            "email": s.email, "customer": s.customer, "fee": s.fee, "emailedAt": s.emailed_at}

def create_app(settings: Settings | None = None, *, testing=False):
    cfg = settings or Settings()
    cfg.validate_password()
    engine = build_engine(cfg)
    sessions = sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def lifespan(app):
        # Production schema is owned by Alembic; only tests create temporary tables.
        if testing:
            Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Bilhete Solidário API", version="1.0.0", lifespan=lifespan)
    app.state.engine, app.state.sessions = engine, sessions
    attempts = defaultdict(deque)

    def db():
        with sessions() as session:
            yield session

    def catalog(session):
        saved = {p.id: product_dict(p) for p in session.scalars(select(Product))}
        return [dict(p) for p in CATALOG if p["id"] not in saved] + list(saved.values())

    def request_hash(payload):
        return hashlib.sha256(json.dumps(payload.model_dump(), sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    @app.exception_handler(HTTPException)
    async def expected_error(request, exc):
        return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return JSONResponse({"error": "Confira os campos: valores, quantidades e e-mail devem ser válidos."}, status_code=422)

    @app.middleware("http")
    async def protect(request: Request, call_next):
        public = {"/api/health", "/api/login"}
        if request.url.path.startswith("/api/"):
            if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("x-csrf-protection") != "1":
                return JSONResponse({"error": "Solicitação não autorizada."}, status_code=403)
            if request.url.path not in public:
                token = request.cookies.get(COOKIE, "")
                hashed = hashlib.sha256(token.encode()).hexdigest()
                with sessions() as session:
                    auth = session.get(LoginSession, hashed)
                    if not token or not auth or auth.expires_at <= int(time.time()):
                        return JSONResponse({"error": "Entre novamente para acessar o caixa."}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health", include_in_schema=False)
    def health(session: Session = Depends(db)):
        session.execute(text("SELECT 1"))
        return {"status": "ok"}

    @app.post("/api/login")
    def login(payload: LoginInput, request: Request, response: Response, session: Session = Depends(db)):
        key = request.client.host if request.client else "unknown"
        q = attempts[key]
        current = time.monotonic()
        while q and q[0] < current - 60:
            q.popleft()
        if len(q) >= 10:
            raise HTTPException(429, "Muitas tentativas. Aguarde um minuto.")
        q.append(current)
        valid_name = hmac.compare_digest(payload.username.encode(), cfg.admin_username.encode())
        valid_password = hmac.compare_digest(payload.password.encode(), cfg.admin_password.get_secret_value().encode())
        if not (valid_name and valid_password):
            raise HTTPException(401, "Usuário ou senha inválidos.")
        token = secrets.token_urlsafe(32)
        session.execute(delete(LoginSession).where(LoginSession.expires_at <= int(time.time())))
        session.add(LoginSession(token_hash=hashlib.sha256(token.encode()).hexdigest(),
                                 expires_at=int(time.time()) + cfg.session_hours * 3600))
        session.commit()
        response.set_cookie(COOKIE, token, max_age=cfg.session_hours * 3600, httponly=True,
                            secure=cfg.cookie_secure, samesite="strict", path="/")
        return {"ok": True, "username": cfg.admin_username}

    @app.get("/api/session")
    def current_user():
        return {"username": cfg.admin_username}

    @app.post("/api/logout")
    def logout(request: Request, response: Response, session: Session = Depends(db)):
        hashed = hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest()
        session.execute(delete(LoginSession).where(LoginSession.token_hash == hashed))
        session.commit()
        response.delete_cookie(COOKIE, path="/")
        return {"ok": True}

    @app.get("/api/data")
    def data(event: str | None = None, session: Session = Depends(db)):
        return {"products": catalog(session),
                "sales": [sale_dict(s) for s in session.scalars(
                    (select(Sale).where(Sale.event == event) if event is not None else select(Sale))
                    .order_by(Sale.created_at.desc()))],
                "events": sorted(set(session.scalars(select(Event.name))) | set(session.scalars(select(Sale.event))) | {"Varejo que dá resultado"}),
                "emailReady": bool(cfg.resend_api_key.get_secret_value() and cfg.receipt_from)}

    @app.post("/api/events")
    def create_event(payload: EventInput, session: Session = Depends(db)):
        # Names are stable identifiers; historic sale snapshots are never renamed.
        if not session.get(Event, payload.name):
            session.add(Event(name=payload.name))
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
        return {"ok": True, "name": payload.name}

    @app.post("/api/products")
    def save_product(payload: ProductInput, session: Session = Depends(db)):
        if payload.price <= 0:
            raise HTTPException(422, "Informe um preço de venda maior que zero.")
        value = payload.model_dump()
        value["active"] = bool(value["active"])
        product = session.get(Product, payload.id)
        if product:
            for k, v in value.items():
                setattr(product, k, v)
        else:
            session.add(Product(**value))
        session.commit()
        return {"ok": True, "id": payload.id}

    @app.post("/api/sales")
    def create_sale(payload: SaleInput, session: Session = Depends(db)):
        fingerprint = request_hash(payload)
        previous = session.get(Sale, payload.id)
        if previous:
            if previous.request_hash != fingerprint:
                raise HTTPException(409, "Esse código já pertence a outra venda. Atualize a página.")
            return {"ok": True, "id": previous.id}
        # Lock prices while building the immutable sale snapshot in PostgreSQL.
        selected = session.scalars(select(Product).where(Product.id.in_([i.id for i in payload.items])).with_for_update()).all()
        available = {p.id: p for p in selected}
        items = []
        for i in payload.items:
            p = available.get(i.id)
            if not p or not p.active or p.price <= 0:
                raise HTTPException(422, "Produto indisponível ou sem preço. Atualize o catálogo.")
            items.append({"id": p.id, "name": p.name, "price": p.price, "cost": p.cost, "qty": i.qty,
                          "weight_grams": p.weight_grams or weight_from_name(p.name)})
        total = sum(i["price"] * i["qty"] for i in items)
        cost = sum(i["cost"] * i["qty"] for i in items)
        if total > 2_000_000_000 or cost > 2_000_000_000:
            raise HTTPException(422, "O valor da venda ultrapassa o limite permitido.")
        if payload.fee > total:
            raise HTTPException(422, "A taxa não pode superar o total da venda.")
        fee = payload.fee
        if payload.automatic_fees and payload.method in ("Pix", "Débito", "Crédito"):
            rate = {"Pix": 50, "Débito": 150, "Crédito": 381}[payload.method]
            if payload.method == "Crédito":
                # Gross up so the processor's discount preserves the item subtotal.
                subtotal = total
                total = (subtotal * 10000 + (10000 - rate) // 2) // (10000 - rate)
                fee = total - subtotal
            else:
                fee = (total * rate + 5000) // 10000
        sale = Sale(id=payload.id, created_at=now_iso(), event=payload.event, items=items,
                    total=total, cost=cost, fee=fee, status=payload.status,
                    method=payload.method, email=payload.email, customer=payload.customer,
                    request_hash=fingerprint)
        session.add(sale)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            previous = session.get(Sale, payload.id)
            if not previous or previous.request_hash != fingerprint:
                raise HTTPException(409, "Conflito no registro da venda. Atualize a página.")
        return {"ok": True, "id": payload.id}

    @app.patch("/api/sales/{sale_id}/status")
    def change_status(sale_id: str, payload: StatusInput, session: Session = Depends(db)):
        sale = session.scalar(select(Sale).where(Sale.id == sale_id).with_for_update())
        if not sale:
            raise HTTPException(404, "Venda não encontrada.")
        if sale.status == "cancelled" or (payload.status == "paid" and sale.status != "pending"):
            raise HTTPException(409, "Alteração de situação não permitida.")
        sale.status = payload.status
        session.commit()
        return {"ok": True}

    @app.get("/api/sales/{sale_id}/receipt", response_class=PlainTextResponse)
    def receipt(sale_id: str, session: Session = Depends(db)):
        sale = session.get(Sale, sale_id)
        if not sale or sale.status != "paid":
            raise HTTPException(404, "Recibo disponível somente para venda paga.")
        return receipt_text(sale)

    @app.post("/api/sales/{sale_id}/email")
    def email_receipt(sale_id: str, session: Session = Depends(db)):
        sale = session.scalar(select(Sale).where(Sale.id == sale_id).with_for_update())
        if not sale or sale.status != "paid" or not sale.email:
            raise HTTPException(422, "Informe um e-mail na venda e confirme o recebimento primeiro.")
        if not (cfg.resend_api_key.get_secret_value() and cfg.receipt_from):
            raise HTTPException(503, "Envio automático não configurado. Use a opção manual.")
        if sale.emailed_at:
            return {"ok": True, "alreadySent": True}
        try:
            with httpx.Client(timeout=20) as client:
                result = client.post("https://api.resend.com/emails", headers={
                    "Authorization": f"Bearer {cfg.resend_api_key.get_secret_value()}",
                    "Idempotency-Key": f"receipt-{sale.id}"}, json={"from": cfg.receipt_from,
                    "to": [sale.email], "subject": f"Recibo {sale.id[:8]} • {sale.event}", "text": receipt_text(sale), "html": receipt_html(sale)})
                result.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(502, "O provedor não confirmou o envio. Confira a configuração ou tente novamente.")
        sale.emailed_at = now_iso()
        session.commit()
        return {"ok": True}

    @app.get("/api/display")
    def display(session: Session = Depends(db)):
        public_products = [{k: p[k] for k in ("id", "name", "category", "price")}
                           for p in catalog(session) if p["active"] and p["price"] > 0]
        state = session.get(DisplayState, "main")
        fresh = state and int(time.time() * 1000) - state.updated_at < 90_000
        by_id = {p["id"]: p for p in public_products}
        items = [{**by_id[i["id"]], "qty": i["qty"]} for i in state.items if i["id"] in by_id] if fresh else []
        return {"products": public_products, "items": items,
                "event": state.event if state else "Varejo que dá resultado", "updatedAt": state.updated_at if state else 0}

    @app.post("/api/display")
    def update_display(payload: DisplayInput, session: Session = Depends(db)):
        if abs(int(time.time() * 1000) - payload.updatedAt) > 300_000:
            raise HTTPException(422, "Confira o relógio do computador e tente novamente.")
        value = {"id": "main", "event": payload.event, "items": [i.model_dump() for i in payload.items], "updated_at": payload.updatedAt}
        # Dialect upserts make updates atomic, including the first concurrent write.
        if engine.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        statement = insert(DisplayState).values(**value)
        statement = statement.on_conflict_do_update(index_elements=[DisplayState.id],
                    set_=value, where=DisplayState.updated_at <= payload.updatedAt)
        session.execute(statement)
        session.commit()
        return {"ok": True}

    return app

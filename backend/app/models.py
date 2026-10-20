from sqlalchemy import BigInteger, Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(60))
    price: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40), index=True)
    event: Mapped[str] = mapped_column(String(120))
    items: Mapped[list] = mapped_column(JSON)
    total: Mapped[int] = mapped_column(Integer)
    cost: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), index=True)
    method: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(254), default="")
    customer: Mapped[str] = mapped_column(String(120), default="")
    fee: Mapped[int] = mapped_column(Integer, default=0)
    emailed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    request_hash: Mapped[str] = mapped_column(String(64))

class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[int] = mapped_column(BigInteger)

class DisplayState(Base):
    __tablename__ = "display_state"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    event: Mapped[str] = mapped_column(String(120))
    items: Mapped[list] = mapped_column(JSON)
    updated_at: Mapped[int] = mapped_column(BigInteger)

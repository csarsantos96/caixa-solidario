import json
import time
import httpx
from pydantic import SecretStr
from sqlalchemy import select
from app.models import LoginSession, Sale, DisplayState

def sale(**overrides):
    return {'id':'sale-1','items':[{'id':'rice','qty':3}],'event':'Evento teste','status':'pending','method':'Pix','fee':50,'email':'cliente@example.test','customer':'Cliente',**overrides}

def test_auth_and_csrf(client):
    assert client.get('/api/data').status_code==401
    assert client.get('/api/display').status_code==401
    assert client.get('/api/health').status_code==200
    client.headers.pop('X-CSRF-Protection')
    assert client.post('/api/login',json={'username':'admin','password':'test-password-at-least-12'}).status_code==403

def test_login_cookie_logout(auth):
    assert auth.get('/api/session').json()['username']=='admin'
    assert auth.post('/api/logout').status_code==200
    assert auth.get('/api/data').status_code==401

def test_login_wrong_password_and_rate_limit(client):
    for _ in range(10):
        assert client.post('/api/login',json={'username':'admin','password':'wrong'}).status_code==401
    assert client.post('/api/login',json={'username':'admin','password':'wrong'}).status_code==429

def test_expired_session(auth,app):
    with app.state.sessions() as db:
        token=db.scalar(select(LoginSession));token.expires_at=0;db.commit()
    assert auth.get('/api/data').status_code==401

def test_catalog_prices_and_snapshots(auth,rice):
    catalog=auth.get('/api/data').json()['products']
    assert len(catalog)==18
    assert len([x for x in catalog if x['price']==0])==17
    assert auth.post('/api/sales',json=sale()).status_code==200
    saved=auth.get('/api/data').json()['sales'][0]
    assert saved['total']==2250 and saved['cost']==1530 and saved['fee']==50
    assert json.loads(saved['items'])[0]['name']=='Arroz 1 kg'
    assert auth.post('/api/products',json={**rice,'price':1000,'cost':800}).status_code==200
    assert auth.get('/api/data').json()['sales'][0]['total']==2250

def test_idempotent_retry_and_conflict(auth,rice):
    assert auth.post('/api/sales',json=sale()).status_code==200
    assert auth.post('/api/sales',json=sale()).status_code==200
    assert len(auth.get('/api/data').json()['sales'])==1
    assert auth.post('/api/sales',json=sale(method='Crédito')).status_code==409

def test_server_rejects_price_tampering(auth,rice):
    r=auth.post('/api/sales',json=sale(items=[{'id':'rice','qty':1,'price':1}]))
    assert r.status_code==422

def test_invalid_cart_and_email(auth,rice):
    for items in ([{'id':'rice','qty':0}],[{'id':'rice','qty':True}],[{'id':'rice','qty':1.5}],[{'id':'rice','qty':1},{'id':'rice','qty':1}],[],[{'id':'unknown','qty':1}]):
        assert auth.post('/api/sales',json=sale(items=items)).status_code==422
    assert auth.post('/api/sales',json=sale(email='invalid')).status_code==422
    assert auth.post('/api/sales',json=sale(fee=99999)).status_code==422

def test_invalid_products(auth,rice):
    for changes in ({'price':0},{'price':-5},{'cost':-1},{'name':''},{'price':1.5}):
        assert auth.post('/api/products',json={**rice,**changes}).status_code==422

def test_archived_and_unconfigured_product(auth,rice):
    assert auth.post('/api/sales',json=sale(items=[{'id':'catalog-01','qty':1}])).status_code==422
    auth.post('/api/products',json={**rice,'active':0})
    assert auth.post('/api/sales',json=sale()).status_code==422

def test_status_flow_and_receipt(auth,rice):
    auth.post('/api/sales',json=sale())
    assert auth.get('/api/sales/sale-1/receipt').status_code==404
    assert auth.patch('/api/sales/sale-1/status',json={'status':'paid'}).status_code==200
    r=auth.get('/api/sales/sale-1/receipt')
    assert r.status_code==200 and 'CS-sale-1' in r.text and 'R$ 22,50' in r.text
    assert auth.patch('/api/sales/sale-1/status',json={'status':'paid'}).status_code==409
    assert auth.patch('/api/sales/sale-1/status',json={'status':'cancelled'}).status_code==200
    assert auth.patch('/api/sales/sale-1/status',json={'status':'paid'}).status_code==409
    assert auth.get('/api/sales/sale-1/receipt').status_code==404

def test_email_not_configured(auth,rice):
    auth.post('/api/sales',json=sale(status='paid'))
    assert auth.get('/api/data').json()['emailReady'] is False
    assert auth.post('/api/sales/sale-1/email').status_code==503

def test_email_failure_success_and_retry(auth,rice,settings,monkeypatch):
    auth.post('/api/sales',json=sale(status='paid'))
    settings.resend_api_key=SecretStr('fake-test-key');settings.receipt_from='teste@example.test'
    result_code=502;calls=[]
    class Provider:
        def __init__(self,**kw):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def post(self,url,**kw):
            calls.append(kw)
            return httpx.Response(result_code,request=httpx.Request('POST',url))
    monkeypatch.setattr('app.main.httpx.Client',Provider)
    assert auth.post('/api/sales/sale-1/email').status_code==502
    assert auth.get('/api/data').json()['sales'][0]['emailedAt'] is None
    result_code=200
    assert auth.post('/api/sales/sale-1/email').status_code==200
    assert calls[-1]['headers']['Idempotency-Key']=='receipt-sale-1'
    assert calls[-1]['json']['to']==['cliente@example.test']
    assert 'BILHETE SOLIDÁRIO' in calls[-1]['json']['html']
    assert '3 × Arroz 1 kg' in calls[-1]['json']['html']
    assert 'R$ 22,50' in calls[-1]['json']['html']
    assert 'CS-sale-1' in calls[-1]['json']['html']
    assert 'RECIBO DE VENDA' in calls[-1]['json']['text']
    assert auth.post('/api/sales/sale-1/email').json()['alreadySent'] is True
    assert len(calls)==2

def test_display_catalog_cart_and_no_private_fields(auth,rice):
    d=auth.get('/api/display').json()
    assert len(d['products'])==1 and d['items']==[]
    assert 'cost' not in d['products'][0]
    stamp=int(time.time()*1000)
    assert auth.post('/api/display',json={'event':'Teste','items':[{'id':'rice','qty':2}],'updatedAt':stamp}).status_code==200
    d=auth.get('/api/display').json()
    assert d['items'][0]['price']==750 and d['items'][0]['qty']==2
    assert not any(x in json.dumps(d) for x in ('customer','email','cost'))
    auth.post('/api/display',json={'event':'Antigo','items':[],'updatedAt':stamp-1000})
    assert auth.get('/api/display').json()['event']=='Teste'

def test_display_expiry_and_invalid_payload(auth,rice,app):
    stamp=int(time.time()*1000)
    auth.post('/api/display',json={'event':'Teste','items':[{'id':'rice','qty':1}],'updatedAt':stamp})
    with app.state.sessions() as db:
        state=db.get(DisplayState,'main');state.updated_at=stamp-91000;db.commit()
    assert auth.get('/api/display').json()['items']==[]
    assert auth.post('/api/display',json={'event':'Teste','items':[{'id':'rice','qty':0}],'updatedAt':stamp}).status_code==422
    assert auth.post('/api/display',json={'event':'Teste','items':[],'updatedAt':stamp-600000}).status_code==422

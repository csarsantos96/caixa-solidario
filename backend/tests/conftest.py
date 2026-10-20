import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from app.config import Settings
from app.database import Base
from app.main import create_app

@pytest.fixture
def settings(tmp_path):
    url=os.environ.get('TEST_DATABASE_URL',f'sqlite:///{tmp_path / "test.db"}')
    if not url.startswith('sqlite') and not any(x in (make_url(url).database or '') for x in ('_ci','_test')):
        raise RuntimeError('TEST_DATABASE_URL deve apontar para um banco de teste (_ci ou _test).')
    return Settings(database_url=url,admin_username='admin',admin_password='test-password-at-least-12',cookie_secure=False,resend_api_key='',receipt_from='')

@pytest.fixture
def app(settings):
    return create_app(settings,testing=True)

@pytest.fixture
def client(app):
    with TestClient(app) as c:
        with app.state.sessions() as db:
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(delete(table))
            db.commit()
        c.headers['X-CSRF-Protection']='1'
        yield c

@pytest.fixture
def auth(client):
    r=client.post('/api/login',json={'username':'admin','password':'test-password-at-least-12'})
    assert r.status_code==200
    return client

@pytest.fixture
def rice(auth):
    product={'id':'rice','name':'Arroz 1 kg','category':'Alimentos','price':750,'cost':510,'active':1}
    assert auth.post('/api/products',json=product).status_code==200
    return product

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import Settings

class Base(DeclarativeBase):
    pass

def build_engine(settings: Settings):
    options = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, connect_args=options, pool_pre_ping=True)

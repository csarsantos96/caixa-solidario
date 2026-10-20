from alembic import context
from app.config import Settings
from app.database import Base, build_engine
from app import models

config = context.config
settings = Settings()
target_metadata = Base.metadata
if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle":"named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = build_engine(settings)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()

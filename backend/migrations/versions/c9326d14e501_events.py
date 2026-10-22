"""Persist events even before their first sale."""
from alembic import op
import sqlalchemy as sa

revision = 'c9326d14e501'
down_revision = 'b725e1a49c03'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('events', sa.Column('name', sa.String(120), primary_key=True))
    op.execute(sa.text("INSERT INTO events (name) SELECT DISTINCT event FROM sales "
                       "UNION SELECT 'Varejo que dá resultado'"))


def downgrade():
    op.drop_table('events')

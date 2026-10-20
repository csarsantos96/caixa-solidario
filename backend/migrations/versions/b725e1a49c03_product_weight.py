"""Store the weight of one product unit in grams."""
from alembic import op
import sqlalchemy as sa

revision = 'b725e1a49c03'
down_revision = 'f81f08b6ae1c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('weight_grams', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('products', 'weight_grams')

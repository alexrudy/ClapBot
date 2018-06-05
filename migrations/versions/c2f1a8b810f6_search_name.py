"""search_name

Revision ID: c2f1a8b810f6
Revises: 196c6fba2562
Create Date: 2018-06-05 04:13:29.631981

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c2f1a8b810f6'
down_revision = '196c6fba2562'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('housingsearch', 'description')
    op.add_column('housingsearch', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('housingsearch', sa.Column('description', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('housingsearch', 'name')
    op.drop_column('housingsearch', 'description')
    op.add_column('housingsearch', sa.Column('description', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###
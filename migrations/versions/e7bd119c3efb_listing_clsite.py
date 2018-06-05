"""listing_clsite

Revision ID: e7bd119c3efb
Revises: 74d33e3d3180
Create Date: 2018-06-05 04:25:46.804389

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7bd119c3efb'
down_revision = '74d33e3d3180'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('listing', sa.Column('cl_area', sa.Integer(), nullable=True))
    op.add_column('listing', sa.Column('cl_category', sa.Integer(), nullable=True))
    op.add_column('listing', sa.Column('cl_site', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'listing', 'clsite', ['cl_site'], ['id'])
    op.create_foreign_key(None, 'listing', 'clcategory', ['cl_category'], ['id'])
    op.create_foreign_key(None, 'listing', 'clarea', ['cl_area'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'listing', type_='foreignkey')
    op.drop_constraint(None, 'listing', type_='foreignkey')
    op.drop_constraint(None, 'listing', type_='foreignkey')
    op.drop_column('listing', 'cl_site')
    op.drop_column('listing', 'cl_category')
    op.drop_column('listing', 'cl_area')
    # ### end Alembic commands ###
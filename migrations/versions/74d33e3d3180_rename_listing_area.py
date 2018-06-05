"""rename_listing_area

Revision ID: 74d33e3d3180
Revises: c2f1a8b810f6
Create Date: 2018-06-05 04:21:46.588930

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '74d33e3d3180'
down_revision = 'c2f1a8b810f6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('listing', 'area', new_column_name='home_area')


def downgrade():
    op.alter_column('listing', 'home_area', new_column_name='area')

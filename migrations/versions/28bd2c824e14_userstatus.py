"""Add a user-status column

Revision ID: 28bd2c824e14
Revises:
Create Date: 2018-06-03 06:10:40.784072

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '28bd2c824e14'
down_revision = '6c96742d9817'
branch_labels = None
depends_on = None


def upgrade():

    if op.get_bind().engine.name == 'postgresql':
        userstatus = ENUM(
            'registered', 'active', 'deactivated', name='userstatus')
        userstatus.create(op.get_bind())

    op.add_column(
        'users',
        sa.Column(
            'status',
            sa.Enum('registered', 'active', 'deactivated', name='userstatus'),
            nullable=False))


def downgrade():
    op.drop_column('users', 'status')
    if op.get_bind().engine.name == 'postgresql':
        op.execute("DROP TYPE userstatus;")

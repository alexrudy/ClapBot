"""Listing Expiration

Revision ID: 6c96742d9817
Revises: 6d3ede72791b
Create Date: 2018-06-02 20:19:15.196165

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6c96742d9817'
down_revision = '6d3ede72791b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('listingexpirationcheck',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('listing_id', sa.Integer(), nullable=True),
                    sa.Column('created', sa.DateTime(), nullable=True),
                    sa.Column('response_status', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['listing_id'],
                        ['listing.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.add_column('listing', sa.Column(
        'expired', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('listing', 'expired')
    op.drop_table('listingexpirationcheck')
    # ### end Alembic commands ###
"""base database setup

Revision ID: 6d3ede72791b
Revises: 
Create Date: 2018-05-14 02:23:35.674994

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d3ede72791b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('boundingbox',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('lat_min', sa.Float(), nullable=True),
    sa.Column('lon_min', sa.Float(), nullable=True),
    sa.Column('lat_max', sa.Float(), nullable=True),
    sa.Column('lon_max', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('image',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('full', sa.LargeBinary(), nullable=True),
    sa.Column('thumbnail', sa.LargeBinary(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('url')
    )
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('transitstop',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stop_id', sa.String(), nullable=True),
    sa.Column('agency', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lon', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('listing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('available', sa.Date(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('lon', sa.Float(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('cl_id', sa.BigInteger(), nullable=True),
    sa.Column('area', sa.String(), nullable=True),
    sa.Column('transit_stop_id', sa.Integer(), nullable=True),
    sa.Column('bedrooms', sa.Integer(), nullable=True),
    sa.Column('bathrooms', sa.Integer(), nullable=True),
    sa.Column('size', sa.Float(), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('page', sa.Text(), nullable=True),
    sa.Column('notified', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['transit_stop_id'], ['transitstop.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cl_id'),
    sa.UniqueConstraint('url')
    )
    op.create_table('images',
    sa.Column('image_id', sa.Integer(), nullable=True),
    sa.Column('listing_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['image_id'], ['image.id'], ),
    sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], )
    )
    op.create_table('tags',
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.Column('listing_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], )
    )
    op.create_table('userlistinginfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('listing_id', sa.Integer(), nullable=True),
    sa.Column('rejected', sa.Boolean(), nullable=True),
    sa.Column('starred', sa.Boolean(), nullable=True),
    sa.Column('contacted', sa.Boolean(), nullable=True),
    sa.Column('score', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['listing_id'], ['listing.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('userlistinginfo')
    op.drop_table('tags')
    op.drop_table('images')
    op.drop_table('listing')
    op.drop_table('transitstop')
    op.drop_table('tag')
    op.drop_table('image')
    op.drop_table('boundingbox')
    # ### end Alembic commands ###

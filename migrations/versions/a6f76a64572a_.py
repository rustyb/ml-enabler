"""empty message

Revision ID: a6f76a64572a
Revises: 0ad24de85333
Create Date: 2020-06-05 09:44:34.942925

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6f76a64572a'
down_revision = '0ad24de85333'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('prediction_tiles', 'quadkey_geom',
               existing_type=geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326),
               nullable=False)
    op.drop_index('idx_prediction_tiles_centroid', table_name='prediction_tiles')
    op.drop_column('prediction_tiles', 'valid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('prediction_tiles', sa.Column('valid', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.create_index('idx_prediction_tiles_centroid', 'prediction_tiles', ['centroid'], unique=False)
    op.alter_column('prediction_tiles', 'quadkey_geom',
               existing_type=geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326),
               nullable=True)
    # ### end Alembic commands ###

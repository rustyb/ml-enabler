"""empty message

Revision ID: 021fe21a3358
Revises: 391dd108d76d
Create Date: 2020-09-02 21:16:53.619233

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '021fe21a3358'
down_revision = '391dd108d76d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('predictions', 'chip_name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('predictions', sa.Column('chip_name', sa.TEXT(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###

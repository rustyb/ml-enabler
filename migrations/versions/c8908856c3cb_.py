"""empty message

Revision ID: c8908856c3cb
Revises: 29ec61cd7944
Create Date: 2020-10-06 09:58:13.362651

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c8908856c3cb'
down_revision = '29ec61cd7944'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ml_models', sa.Column('access', sa.String(), nullable=True))
    op.execute("UPDATE ml_models SET access = 'public'")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ml_models', 'access')
    # ### end Alembic commands ###

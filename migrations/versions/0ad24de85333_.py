"""empty message

Revision ID: 0ad24de85333
Revises: 10992f54d4be
Create Date: 2020-03-16 12:56:53.851131

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0ad24de85333'
down_revision = '10992f54d4be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('imagery',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['ml_models.id'], name='fk_models'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('imagery')
    # ### end Alembic commands ###
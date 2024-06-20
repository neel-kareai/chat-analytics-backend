"""add_chart_table

Revision ID: d1045725ab03
Revises: bfe9133f7ba2
Create Date: 2024-06-20 21:53:58.703893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1045725ab03'
down_revision: Union[str, None] = 'bfe9133f7ba2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('charts',
    sa.Column('uuid', sa.UUID(), nullable=False),
    sa.Column('chat_uuid', sa.UUID(), nullable=False),
    sa.Column('chart_type', sa.String(), nullable=False),
    sa.Column('code', sa.Text(), nullable=True),
    sa.Column('data', sa.JSON(), nullable=True),
    sa.Column('caption', sa.String(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['chat_uuid'], ['chat_history.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('charts')
    # ### end Alembic commands ###
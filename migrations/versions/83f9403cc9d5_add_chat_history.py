"""add_chat_history

Revision ID: 83f9403cc9d5
Revises: bcbf60b0cf4c
Create Date: 2024-06-16 03:34:49.847834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83f9403cc9d5'
down_revision: Union[str, None] = 'bcbf60b0cf4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_history',
    sa.Column('uuid', sa.UUID(), nullable=False),
    sa.Column('customer_uuid', sa.UUID(), nullable=False),
    sa.Column('query_type', sa.String(), nullable=False),
    sa.Column('data_source_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['customer_uuid'], ['customers.uuid'], ),
    sa.PrimaryKeyConstraint('uuid'),
    sa.UniqueConstraint('uuid')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chat_history')
    # ### end Alembic commands ###

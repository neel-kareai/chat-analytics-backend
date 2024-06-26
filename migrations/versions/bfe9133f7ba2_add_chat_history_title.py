"""add chat_history.title

Revision ID: bfe9133f7ba2
Revises: 83f9403cc9d5
Create Date: 2024-06-17 03:17:33.349153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfe9133f7ba2'
down_revision: Union[str, None] = '83f9403cc9d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chat_history', sa.Column('title', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'chat_history', ['uuid'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'chat_history', type_='unique')
    op.drop_column('chat_history', 'title')
    # ### end Alembic commands ###

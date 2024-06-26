"""add_last_login_customer_tabel

Revision ID: dea2bdf4444b
Revises: 33e572a32548
Create Date: 2024-06-07 15:31:29.604676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dea2bdf4444b'
down_revision: Union[str, None] = '33e572a32548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('customers', sa.Column('last_login', sa.TIMESTAMP(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('customers', 'last_login')
    # ### end Alembic commands ###

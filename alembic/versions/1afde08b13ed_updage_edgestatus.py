"""updage edgestatus

Revision ID: 1afde08b13ed
Revises: 37668cdf645b
Create Date: 2026-05-06 17:23:16.869282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1afde08b13ed'
down_revision: Union[str, Sequence[str], None] = '37668cdf645b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'edge_status',
        sa.Column('stability', sa.String(), nullable=False, server_default='MODERATE'),
    )
    op.alter_column('edge_status', 'stability', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('edge_status', 'stability')

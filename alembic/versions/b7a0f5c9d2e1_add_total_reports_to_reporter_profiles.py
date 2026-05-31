"""add total_reports to reporter_profiles

Revision ID: b7a0f5c9d2e1
Revises: 1afde08b13ed
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7a0f5c9d2e1"
down_revision: Union[str, Sequence[str], None] = "9c21c3bb1f47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "reporter_profiles",
        sa.Column("total_reports", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("reporter_profiles", "total_reports", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("reporter_profiles", "total_reports")
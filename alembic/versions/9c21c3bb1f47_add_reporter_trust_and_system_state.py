"""add reporter trust and system state

Revision ID: 9c21c3bb1f47
Revises: 1afde08b13ed
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c21c3bb1f47"
down_revision: Union[str, Sequence[str], None] = "1afde08b13ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "reporter_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default=sa.text("0.5")),
        sa.Column("last_updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.alter_column("reporter_profiles", "trust_score", server_default=None)

    op.create_table(
        "system_state",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("system_state")
    op.drop_table("reporter_profiles")
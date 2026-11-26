"""proveedor e identidad de la sesion

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-25 23:19:28.828806

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("sessions", sa.Column("identity_id", sa.Uuid(), nullable=False))
    op.create_foreign_key(
        "sessions_identity_id_fkey",
        "sessions",
        "user_identities",
        ["identity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.add_column("user_identities", sa.Column("provider", sa.String(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user_identities", "provider")
    op.drop_constraint("sessions_identity_id_fkey", "sessions", type_="foreignkey")
    op.drop_column("sessions", "identity_id")

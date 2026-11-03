"""add maintenance
  records

Revision ID: 3c9cdc0412e8
Revises: dacd6c6f094c
Create Date: 2026-10-28 14:02:54.444995

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c9cdc0412e8"
down_revision: str | Sequence[str] | None = "dacd6c6f094c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("asset_id", sa.BigInteger(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_maintenance_records_asset_id", "maintenance_records", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_maintenance_records_asset_id", table_name="maintenance_records")
    op.drop_table("maintenance_records")

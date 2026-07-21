"""add is_verified to users

Revision ID: cdbbd1f86738
Revises: 9df94d8b18d6
Create Date: 2026-07-21 18:57:05.951784

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cdbbd1f86738"
down_revision: Union[str, None] = "9df94d8b18d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_verified")

"""add check constraint for schedule owner matches kind

Revision ID: 9a31bc875b3f
Revises: d26712fa76fc
Create Date: 2026-07-22 01:56:03.485447

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a31bc875b3f"
down_revision: Union[str, None] = "d26712fa76fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_schedule_owner_matches_kind",
        "schedules",
        "(kind = 'SHARED' AND owner_id IS NULL) OR (kind = 'PERSONAL' AND owner_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_schedule_owner_matches_kind", "schedules", type_="check")

"""rename schedule student_id to owner_id

Revision ID: e8f21e1acae0
Revises: cdbbd1f86738
Create Date: 2026-07-22 01:03:57.318730

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8f21e1acae0"
down_revision: Union[str, None] = "cdbbd1f86738"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("schedules", "student_id", new_column_name="owner_id")
    op.alter_column("schedule_completions", "student_id", new_column_name="owner_id")


def downgrade() -> None:
    op.alter_column("schedule_completions", "owner_id", new_column_name="student_id")
    op.alter_column("schedules", "owner_id", new_column_name="student_id")

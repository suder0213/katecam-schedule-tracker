"""add cascade delete to schedule and team member fks

Revision ID: d26712fa76fc
Revises: e8f21e1acae0
Create Date: 2026-07-22 01:43:45.101512

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d26712fa76fc"
down_revision: Union[str, None] = "e8f21e1acae0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK_SPECS = [
    ("schedules_student_id_fkey", "schedules", "users", ["owner_id"], ["user_id"]),
    (
        "schedule_completions_schedule_id_fkey",
        "schedule_completions",
        "schedules",
        ["schedule_id"],
        ["schedule_id"],
    ),
    (
        "schedule_completions_student_id_fkey",
        "schedule_completions",
        "users",
        ["owner_id"],
        ["user_id"],
    ),
    ("team_members_team_id_fkey", "team_members", "teams", ["team_id"], ["team_id"]),
    ("team_members_user_id_fkey", "team_members", "users", ["user_id"], ["user_id"]),
]


def upgrade() -> None:
    for name, source, referent, local_cols, remote_cols in _FK_SPECS:
        op.drop_constraint(name, source, type_="foreignkey")
        op.create_foreign_key(name, source, referent, local_cols, remote_cols, ondelete="CASCADE")


def downgrade() -> None:
    for name, source, referent, local_cols, remote_cols in _FK_SPECS:
        op.drop_constraint(name, source, type_="foreignkey")
        op.create_foreign_key(name, source, referent, local_cols, remote_cols)

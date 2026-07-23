"""add schedule_proposals table

Revision ID: cc8cc5d6708a
Revises: 108b41d55395
Create Date: 2026-07-23 10:28:51.680922

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc8cc5d6708a"
down_revision: Union[str, None] = "108b41d55395"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schedule_proposals",
        sa.Column("proposal_id", sa.UUID(), nullable=False),
        sa.Column("raw_text_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("contents", sa.String(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "APPROVED", "REJECTED", name="proposal_status"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["raw_text_id"], ["crawl_texts.raw_text_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("proposal_id"),
    )


def downgrade() -> None:
    op.drop_table("schedule_proposals")

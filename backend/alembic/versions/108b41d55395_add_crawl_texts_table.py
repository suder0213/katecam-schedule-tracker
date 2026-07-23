"""add crawl_texts table

Revision ID: 108b41d55395
Revises: 9a31bc875b3f
Create Date: 2026-07-23 09:56:04.541776

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "108b41d55395"
down_revision: Union[str, None] = "9a31bc875b3f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crawl_texts",
        sa.Column("raw_text_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.Enum("NOTION", "DISCORD", name="crawl_source"), nullable=False),
        sa.Column("channel", sa.String(), nullable=True),
        sa.Column("raw_text", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(source = 'DISCORD' AND channel IS NOT NULL) "
            "OR (source = 'NOTION' AND channel IS NULL)",
            name="ck_crawl_text_channel_matches_source",
        ),
        sa.PrimaryKeyConstraint("raw_text_id"),
    )


def downgrade() -> None:
    op.drop_table("crawl_texts")

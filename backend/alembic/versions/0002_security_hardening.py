"""security hardening: token_version, refresh_tokens, bank account composite unique

Revision ID: 0002_security_hardening
Revises: 0001_initial
Create Date: 2026-05-07

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_security_hardening"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    op.drop_constraint("bank_accounts_teller_account_id_key", "bank_accounts", type_="unique")
    op.create_unique_constraint(
        "uq_bank_accounts_user_teller_account",
        "bank_accounts",
        ["user_id", "teller_account_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_bank_accounts_user_teller_account", "bank_accounts", type_="unique")
    op.create_unique_constraint(
        "bank_accounts_teller_account_id_key",
        "bank_accounts",
        ["teller_account_id"],
    )
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_column("users", "token_version")

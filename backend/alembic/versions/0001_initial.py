"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-06

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("age_bucket", sa.String(10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "last_active_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False
        ),
    )
    op.create_index("idx_users_age_bucket", "users", ["age_bucket"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "bank_accounts",
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
        sa.Column("teller_account_id", sa.String(255), nullable=False, unique=True),
        sa.Column("teller_access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("institution_name", sa.String(255), nullable=True),
        sa.Column("account_type", sa.String(50), nullable=True),
        sa.Column("account_subtype", sa.String(50), nullable=True),
        sa.Column("last_four", sa.String(10), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index("idx_bank_accounts_user_id", "bank_accounts", ["user_id"])

    op.create_table(
        "balances",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(15, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "previous_amount",
            sa.Numeric(15, 2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    op.create_table(
        "balance_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "snapshot_date", name="uq_balance_history_user_date"
        ),
    )
    op.create_index(
        "idx_balance_history_user_date",
        "balance_history",
        ["user_id", sa.text("snapshot_date DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_balance_history_user_date", table_name="balance_history")
    op.drop_table("balance_history")
    op.drop_table("balances")
    op.drop_index("idx_bank_accounts_user_id", table_name="bank_accounts")
    op.drop_table("bank_accounts")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("idx_users_age_bucket", table_name="users")
    op.drop_table("users")

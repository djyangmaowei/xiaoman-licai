"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("target_weight", sa.Numeric(8, 6), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_asset_class"), "products", ["asset_class"], unique=False)
    op.create_index(op.f("ix_products_code"), "products", ["code"], unique=True)
    op.create_table(
        "fund_flows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("flow_type", sa.String(length=32), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("unit_nav", sa.Numeric(18, 4), nullable=False),
        sa.Column("shares_delta", sa.Numeric(18, 4), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fund_flows_flow_type"), "fund_flows", ["flow_type"], unique=False)
    op.create_index(op.f("ix_fund_flows_trade_date"), "fund_flows", ["trade_date"], unique=False)
    op.create_table(
        "daily_valuations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("valuation_date", sa.Date(), nullable=False),
        sa.Column("cash", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_assets", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_shares", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_nav", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_daily_valuations_valuation_date"),
        "daily_valuations",
        ["valuation_date"],
        unique=True,
    )
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trade_type", sa.String(length=32), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("fee", sa.Numeric(18, 2), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_trade_date"), "trades", ["trade_date"], unique=False)
    op.create_index(op.f("ix_trades_trade_type"), "trades", ["trade_type"], unique=False)
    op.create_table(
        "price_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_price_points_price_date"), "price_points", ["price_date"], unique=False)
    op.create_index(op.f("ix_price_points_product_id"), "price_points", ["product_id"], unique=False)
    op.create_index(op.f("ix_price_points_status"), "price_points", ["status"], unique=False)
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alert_date", sa.Date(), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_alert_date"), "alerts", ["alert_date"], unique=False)
    op.create_index(op.f("ix_alerts_alert_type"), "alerts", ["alert_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_alert_type"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_alert_date"), table_name="alerts")
    op.drop_table("alerts")
    op.drop_index(op.f("ix_price_points_status"), table_name="price_points")
    op.drop_index(op.f("ix_price_points_product_id"), table_name="price_points")
    op.drop_index(op.f("ix_price_points_price_date"), table_name="price_points")
    op.drop_table("price_points")
    op.drop_index(op.f("ix_trades_trade_type"), table_name="trades")
    op.drop_index(op.f("ix_trades_trade_date"), table_name="trades")
    op.drop_table("trades")
    op.drop_index(op.f("ix_daily_valuations_valuation_date"), table_name="daily_valuations")
    op.drop_table("daily_valuations")
    op.drop_index(op.f("ix_fund_flows_trade_date"), table_name="fund_flows")
    op.drop_index(op.f("ix_fund_flows_flow_type"), table_name="fund_flows")
    op.drop_table("fund_flows")
    op.drop_index(op.f("ix_products_code"), table_name="products")
    op.drop_index(op.f("ix_products_asset_class"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

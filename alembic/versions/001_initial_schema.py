"""initial reporting schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("product_id", sa.Integer(), primary_key=True),
        sa.Column("product_name", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "managers",
        sa.Column("manager_id", sa.Integer(), primary_key=True),
        sa.Column("manager_name", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"]),
        sa.ForeignKeyConstraint(["manager_id"], ["managers.manager_id"]),
    )
    op.create_index("ix_sales_id", "sales", ["id"], unique=False)
    op.create_index("ix_sales_date", "sales", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sales_date", table_name="sales")
    op.drop_index("ix_sales_id", table_name="sales")
    op.drop_table("sales")
    op.drop_table("managers")
    op.drop_table("products")

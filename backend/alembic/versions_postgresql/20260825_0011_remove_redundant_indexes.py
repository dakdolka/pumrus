"""Remove indexes duplicated by unique constraints.

Revision ID: 20260825_0011
Revises: 20260825_0010
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260825_0011"
down_revision: Union[str, Sequence[str], None] = "20260825_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_media_asset_public_id", table_name="media_asset")
    op.drop_index("ix_payment_order_public_id", table_name="payment_order")


def downgrade() -> None:
    op.create_index(
        "ix_payment_order_public_id",
        "payment_order",
        ["public_id"],
    )
    op.create_index(
        "ix_media_asset_public_id",
        "media_asset",
        ["public_id"],
    )

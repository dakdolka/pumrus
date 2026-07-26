"""Configure practice batches and convert dictionary exercises to vowel fill.

Revision ID: 20260726_0007
Revises: 20260725_0006
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260726_0007"
down_revision: Union[str, Sequence[str], None] = "20260725_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE exercise_set
        SET configuration =
            COALESCE(configuration, '{}'::jsonb)
            || '{"sessionSize": 50, "pageSize": 5}'::jsonb
        """
    )
    op.execute(
        """
        UPDATE exercise_version
        SET interaction_type = 'vowel_fill'
        WHERE interaction_type = 'text_input'
          AND interaction_config->>'variant' = 'masked_letters'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE exercise_version
        SET interaction_type = 'text_input'
        WHERE interaction_type = 'vowel_fill'
        """
    )
    op.execute(
        """
        UPDATE exercise_set
        SET configuration = COALESCE(configuration, '{}'::jsonb)
            - 'sessionSize' - 'pageSize'
        """
    )

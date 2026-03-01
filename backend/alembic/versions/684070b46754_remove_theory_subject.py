"""remove theory subject

Revision ID: 684070b46754
Revises: 
Create Date: 2026-03-01 17:50:56.898905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '684070b46754'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. theory_type: снимаем FK и убираем subject_key
    with op.batch_alter_table("theory_type", schema=None) as batch_op:
        try:
            batch_op.drop_constraint("theory_type_ibfk_1", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_column("subject_key")
        except Exception:
            pass

    # 2. theory: убираем subject_id
    with op.batch_alter_table("theory", schema=None) as batch_op:
        try:
            batch_op.drop_constraint("theory_ibfk_1", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_column("subject_id")
        except Exception:
            pass

    # 3. task_theory_group: убираем subject_id
    with op.batch_alter_table("task_theory_group", schema=None) as batch_op:
        try:
            batch_op.drop_constraint("task_theory_group_ibfk_1", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_column("subject_id")
        except Exception:
            pass

    # 4. theory_subject: дропаем таблицу, если больше не нужна
    try:
        op.drop_table("theory_subject")
    except Exception:
        pass


def downgrade():
    # Восстановление структуры (минимальное, если вдруг понадобится откат)

    # 1. theory_subject
    op.create_table(
        "theory_subject",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Enum(name="TheorySubject"), nullable=False, unique=True),
    )

    # 2. theory_type.subject_key
    with op.batch_alter_table("theory_type", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject_key", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "theory_type_subject_key_fkey",
            "theory_subject",
            ["subject_key"],
            ["id"],
        )

    # 3. theory.subject_id
    with op.batch_alter_table("theory", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject_id", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "theory_subject_id_fkey",
            "theory_subject",
            ["subject_id"],
            ["id"],
        )

    # 4. task_theory_group.subject_id
    with op.batch_alter_table("task_theory_group", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject_id", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "task_theory_group_subject_id_fkey",
            "theory_subject",
            ["subject_id"],
            ["id"],
        )
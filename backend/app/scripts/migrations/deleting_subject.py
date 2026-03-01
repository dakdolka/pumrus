# ревизия: remove_subject_columns

from alembic import op
import sqlalchemy as sa


def upgrade():
    # если больше не нужна таблица theory_subject
    op.drop_table("theory_subject")

    # если в других таблицах были FK на subject_id – удаляем колонку
    # пример:
    with op.batch_alter_table("task", schema=None) as batch_op:
        if sa.inspect(op.get_bind()).dialect.has_table(op.get_bind(), "task"):
            # если в task была колонка subject_id – удаляем
            try:
                batch_op.drop_constraint("task_subject_id_fkey", type_="foreignkey")
            except Exception:
                pass
            try:
                batch_op.drop_column("subject_id")
            except Exception:
                pass

    with op.batch_alter_table("theory", schema=None) as batch_op:
        try:
            batch_op.drop_constraint("theory_subject_id_fkey", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_column("subject_id")
        except Exception:
            pass


def downgrade():
    # откат (минимальный, если понадобится)
    op.create_table(
        "theory_subject",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
    )
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject_id", sa.Integer, nullable=True))
    with op.batch_alter_table("theory", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subject_id", sa.Integer, nullable=True))

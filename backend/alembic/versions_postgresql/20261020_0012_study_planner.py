"""Personal course plans and durable Telegram reminder queue."""
from alembic import op
import sqlalchemy as sa

revision = "20261020_0012"
down_revision = "20260825_0011"
branch_labels = None
depends_on = None


def timestamps():
    return [sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]


def upgrade():
    op.create_table(
        "study_plan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("schedule", sa.JSON(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("user_id", "request_key", name="uq_study_plan_request"),
        sa.CheckConstraint("status IN ('active', 'paused')", name="ck_study_plan_status"),
    )
    op.create_index("ix_study_plan_user_id", "study_plan", ["user_id"])
    op.create_table(
        "study_reminder",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("study_plan.id", ondelete="CASCADE")),
        sa.Column("request_key", sa.String(64)),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("target_path", sa.String(256), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("weekdays", sa.JSON(), nullable=False),
        sa.Column("local_time", sa.String(5), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_notify_at", sa.DateTime(timezone=True)),
        sa.Column("last_sent_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("delivery_status", sa.String(24), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.String(36)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("user_id", "request_key", name="uq_study_reminder_request"),
        sa.CheckConstraint("status IN ('active', 'paused', 'completed')", name="ck_study_reminder_status"),
        sa.CheckConstraint("attempts >= 0", name="ck_study_reminder_attempts"),
    )
    op.create_index("ix_study_reminder_plan_id", "study_reminder", ["plan_id"])
    op.create_index("ix_study_reminder_due", "study_reminder", ["status", "next_notify_at"])
    op.create_index("ix_study_reminder_user_due", "study_reminder", ["user_id", "due_at"])


def downgrade():
    op.drop_table("study_reminder")
    op.drop_table("study_plan")

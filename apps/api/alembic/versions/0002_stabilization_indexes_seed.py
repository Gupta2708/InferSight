"""stabilization indexes and provider seeds

Revision ID: 0002_stabilization_indexes_seed
Revises: 0001_initial_schema
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = "0002_stabilization_indexes_seed"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
        if_not_exists=True,
    )
    op.create_index("ix_inference_logs_created_at", "inference_logs", ["created_at"], if_not_exists=True)

    provider_configs = sa.table(
        "provider_configs",
        sa.column("id", sa.String),
        sa.column("provider", sa.String),
        sa.column("model", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("supports_streaming", sa.Boolean),
        sa.column("input_cost_per_1k_tokens", sa.Float),
        sa.column("output_cost_per_1k_tokens", sa.Float),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    seed_rows = [
        ("00000000-0000-0000-0000-000000000101", "mock", "mock-fast", True, True, 0.0, 0.0),
        ("00000000-0000-0000-0000-000000000102", "mock", "mock-slow", True, True, 0.0, 0.0),
        ("00000000-0000-0000-0000-000000000103", "mock", "mock-error", True, True, 0.0, 0.0),
        ("00000000-0000-0000-0000-000000000104", "openai", "gpt-4.1-mini", False, True, 0.0004, 0.0016),
        ("00000000-0000-0000-0000-000000000105", "gemini", "gemini-flash", False, True, 0.000075, 0.0003),
    ]
    connection = op.get_bind()
    existing = {
        (row.provider, row.model)
        for row in connection.execute(sa.select(provider_configs.c.provider, provider_configs.c.model))
    }
    now = datetime.now(timezone.utc)
    missing_rows = [
        {
            "id": id_,
            "provider": provider,
            "model": model,
            "enabled": enabled,
            "supports_streaming": streaming,
            "input_cost_per_1k_tokens": input_cost,
            "output_cost_per_1k_tokens": output_cost,
            "created_at": now,
            "updated_at": now,
        }
        for id_, provider, model, enabled, streaming, input_cost, output_cost in seed_rows
        if (provider, model) not in existing
    ]
    if missing_rows:
        op.bulk_insert(provider_configs, missing_rows)


def downgrade() -> None:
    op.execute(
        "DELETE FROM provider_configs WHERE id IN ("
        "'00000000-0000-0000-0000-000000000101',"
        "'00000000-0000-0000-0000-000000000102',"
        "'00000000-0000-0000-0000-000000000103',"
        "'00000000-0000-0000-0000-000000000104',"
        "'00000000-0000-0000-0000-000000000105')"
    )
    op.drop_index("ix_inference_logs_created_at", table_name="inference_logs", if_exists=True)
    op.drop_index("ix_messages_conversation_created", table_name="messages", if_exists=True)

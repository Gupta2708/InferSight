"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _uuid():
    return sa.String(length=36)


def _json():
    return sa.JSON()


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_conversations_status", "conversations", ["status"])
    op.create_index("ix_conversations_last_message_at", "conversations", ["last_message_at"])

    op.create_table(
        "messages",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("conversation_id", _uuid(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(64)),
        sa.Column("model", sa.String(128)),
        sa.Column("trace_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
    )
    for col in ["conversation_id", "status", "provider", "model", "trace_id"]:
        op.create_index(f"ix_messages_{col}", "messages", [col])

    op.create_table(
        "provider_configs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("supports_streaming", sa.Boolean(), nullable=False),
        sa.Column("input_cost_per_1k_tokens", sa.Float(), nullable=False),
        sa.Column("output_cost_per_1k_tokens", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "model", name="uq_provider_model"),
    )
    op.create_index("ix_provider_configs_provider", "provider_configs", ["provider"])
    op.create_index("ix_provider_configs_model", "provider_configs", ["model"])

    op.create_table(
        "inference_traces",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("conversation_id", _uuid()),
        sa.Column("message_id", _uuid()),
        sa.Column("parent_trace_id", sa.String(64)),
        sa.Column("replayed_from_trace_id", sa.String(64)),
        sa.Column("comparison_run_id", _uuid()),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("trace_id"),
    )
    for col in ["trace_id", "conversation_id", "message_id", "parent_trace_id", "replayed_from_trace_id", "comparison_run_id", "status", "started_at"]:
        op.create_index(f"ix_inference_traces_{col}", "inference_traces", [col])

    op.create_table(
        "inference_spans",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("span_id", sa.String(64), nullable=False),
        sa.Column("parent_span_id", sa.String(64)),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for col in ["trace_id", "span_id", "parent_span_id", "name", "status"]:
        op.create_index(f"ix_inference_spans_{col}", "inference_spans", [col])
    op.create_index("ix_spans_trace_created", "inference_spans", ["trace_id", "created_at"])

    op.create_table(
        "inference_logs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("conversation_id", _uuid()),
        sa.Column("message_id", _uuid()),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=False),
        sa.Column("stream", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("time_to_first_token_ms", sa.Integer()),
        sa.Column("tokens_per_second", sa.Float()),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_input_cost", sa.Float(), nullable=False),
        sa.Column("estimated_output_cost", sa.Float(), nullable=False),
        sa.Column("estimated_total_cost", sa.Float(), nullable=False),
        sa.Column("input_preview", sa.Text(), nullable=False),
        sa.Column("output_preview", sa.Text(), nullable=False),
        sa.Column("error_type", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("retryable", sa.Boolean(), nullable=False),
        sa.Column("request_snapshot_json", _json(), nullable=False),
        sa.Column("safe_metadata_json", _json(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("trace_id"),
    )
    for col in ["trace_id", "conversation_id", "message_id", "provider", "model", "status", "latency_ms", "error_type"]:
        op.create_index(f"ix_inference_logs_{col}", "inference_logs", [col])
    op.create_index("ix_logs_provider_model_created", "inference_logs", ["provider", "model", "created_at"])
    op.create_index("ix_logs_status_created", "inference_logs", ["status", "created_at"])

    op.create_table("stream_events", sa.Column("id", _uuid(), primary_key=True), sa.Column("trace_id", sa.String(64), nullable=False), sa.Column("sequence_number", sa.Integer(), nullable=False), sa.Column("event_type", sa.String(32), nullable=False), sa.Column("delta_text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_stream_events_trace_id", "stream_events", ["trace_id"])
    op.create_index("ix_stream_events_event_type", "stream_events", ["event_type"])
    op.create_index("ix_stream_trace_sequence", "stream_events", ["trace_id", "sequence_number"])

    op.create_table("provider_errors", sa.Column("id", _uuid(), primary_key=True), sa.Column("trace_id", sa.String(64), nullable=False), sa.Column("provider", sa.String(64), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("error_type", sa.String(64), nullable=False), sa.Column("error_message", sa.Text(), nullable=False), sa.Column("retryable", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for col in ["trace_id", "provider", "model", "error_type"]:
        op.create_index(f"ix_provider_errors_{col}", "provider_errors", [col])

    op.create_table("pii_redaction_events", sa.Column("id", _uuid(), primary_key=True), sa.Column("trace_id", sa.String(64), nullable=False), sa.Column("field_name", sa.String(64), nullable=False), sa.Column("pii_type", sa.String(64), nullable=False), sa.Column("redacted_count", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_pii_redaction_events_trace_id", "pii_redaction_events", ["trace_id"])

    op.create_table("ingestion_events", sa.Column("id", _uuid(), primary_key=True), sa.Column("event_id", sa.String(80), nullable=False), sa.Column("trace_id", sa.String(64), nullable=False), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("retry_count", sa.Integer(), nullable=False), sa.Column("payload_json", _json(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("processed_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("event_id", name="uq_ingestion_events_event_id"))
    op.create_index("ix_ingestion_events_trace_id", "ingestion_events", ["trace_id"])
    op.create_index("ix_ingestion_events_status", "ingestion_events", ["status"])

    op.create_table("dead_letter_events", sa.Column("id", _uuid(), primary_key=True), sa.Column("event_id", sa.String(80), nullable=False), sa.Column("trace_id", sa.String(64), nullable=False), sa.Column("event_type", sa.String(64), nullable=False), sa.Column("failure_reason", sa.Text(), nullable=False), sa.Column("payload_json", _json(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_dead_letter_events_event_id", "dead_letter_events", ["event_id"])
    op.create_index("ix_dead_letter_events_trace_id", "dead_letter_events", ["trace_id"])

    op.create_table("comparison_runs", sa.Column("id", _uuid(), primary_key=True), sa.Column("conversation_id", _uuid()), sa.Column("source_message_id", _uuid()), sa.Column("prompt", sa.Text(), nullable=False), sa.Column("context_mode", sa.String(16), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)))
    for col in ["conversation_id", "source_message_id", "status"]:
        op.create_index(f"ix_comparison_runs_{col}", "comparison_runs", [col])

    op.create_table("comparison_results", sa.Column("id", _uuid(), primary_key=True), sa.Column("comparison_run_id", _uuid(), nullable=False), sa.Column("trace_id", sa.String(64), nullable=False), sa.Column("provider", sa.String(64), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("latency_ms", sa.Integer()), sa.Column("time_to_first_token_ms", sa.Integer()), sa.Column("total_tokens", sa.Integer(), nullable=False), sa.Column("estimated_total_cost", sa.Float(), nullable=False), sa.Column("output_preview", sa.Text(), nullable=False), sa.Column("error_type", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for col in ["comparison_run_id", "trace_id", "provider", "model", "status", "error_type"]:
        op.create_index(f"ix_comparison_results_{col}", "comparison_results", [col])


def downgrade() -> None:
    for table in [
        "comparison_results",
        "comparison_runs",
        "dead_letter_events",
        "ingestion_events",
        "pii_redaction_events",
        "provider_errors",
        "stream_events",
        "inference_logs",
        "inference_spans",
        "inference_traces",
        "provider_configs",
        "messages",
        "conversations",
    ]:
        op.drop_table(table)


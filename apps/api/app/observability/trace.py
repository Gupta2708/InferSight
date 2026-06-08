import uuid


def new_trace_id() -> str:
    return f"trace_{uuid.uuid4().hex}"


def new_span_id() -> str:
    return f"span_{uuid.uuid4().hex[:16]}"


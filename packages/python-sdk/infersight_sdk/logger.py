from uuid import uuid4


def event_id() -> str:
    return f"evt_{uuid4().hex}"


from app.db.models import Base
from app.db.session import engine
from app.llm.errors import sanitize_error_message
from app.main import app


def test_app_imports_and_routes_exist():
    Base.metadata.create_all(bind=engine)
    routes = {route.path for route in app.routes}
    assert "/api/conversations/{conversation_id}/messages/stream" in routes
    assert "/api/ingest/inference" in routes
    assert "/api/comparisons" in routes


def test_error_sanitizer_redacts_urls_and_keys():
    message = (
        "Client error '404 Not Found' for url "
        "'https://generativelanguage.googleapis.com/v1beta/models/mock-fast:generateContent?key=AIzaSecret'"
    )
    cleaned = sanitize_error_message(message)
    assert "AIzaSecret" not in cleaned
    assert "generativelanguage.googleapis.com" not in cleaned
    assert "[redacted-url]" in cleaned

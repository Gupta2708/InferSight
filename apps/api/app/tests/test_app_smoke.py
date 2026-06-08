from app.db.models import Base
from app.db.session import engine
from app.main import app


def test_app_imports_and_routes_exist():
    Base.metadata.create_all(bind=engine)
    routes = {route.path for route in app.routes}
    assert "/api/conversations/{conversation_id}/messages/stream" in routes
    assert "/api/ingest/inference" in routes
    assert "/api/comparisons" in routes


import httpx


class InferSightClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def ingest_inference(self, event: dict) -> dict:
        response = httpx.post(f"{self.base_url}/api/ingest/inference", json=event, timeout=10)
        response.raise_for_status()
        return response.json()


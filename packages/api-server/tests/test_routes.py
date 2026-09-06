"""Smoke tests for the FastAPI app."""

from fastapi.testclient import TestClient

from api_server.main import app

client = TestClient(app)


def test_list_agents() -> None:
    response = client.get("/agents")
    assert response.status_code == 200
    assert response.json() == {"agents": []}


def test_health_check() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
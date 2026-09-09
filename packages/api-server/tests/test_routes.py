"""Smoke tests for the FastAPI app."""

from unittest.mock import AsyncMock, patch

from api_server.main import app
from fastapi.testclient import TestClient


def test_list_agents() -> None:
    """List agents endpoint should return an empty list when no agents are registered."""
    with TestClient(app) as client:
        response = client.get("/agents")
        assert response.status_code == 200
        assert response.json() == {"agents": []}


def test_health_check() -> None:
    """OpenAPI schema should be available."""
    with TestClient(app) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200


def test_rag_query_endpoint() -> None:
    """RAG query endpoint should accept a question and return an answer."""
    mock_response = AsyncMock()
    mock_response.content = "AI is artificial intelligence."

    # Mock both the embeddings (used by VectorRetriever) and the LLM
    with (
        patch("rag_pipeline.retriever.OpenAIEmbeddings") as mock_embeddings,
        patch("rag_pipeline.pipeline.ChatOpenAI") as mock_llm,
    ):
        mock_embeddings.return_value = AsyncMock()
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

        # Mock the similarity search to return empty chunks (no retrieval needed)
        with patch("rag_pipeline.retriever.VectorRetriever.similarity_search") as mock_search:
            mock_search.return_value = []

            with TestClient(app) as client:
                response = client.post("/rag/query", json={"question": "What is AI?"})
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert data["question"] == "What is AI?"

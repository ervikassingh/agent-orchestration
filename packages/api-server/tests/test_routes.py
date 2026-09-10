"""Smoke tests for the FastAPI app."""

from unittest.mock import AsyncMock, patch

from main import app
from fastapi.testclient import TestClient


def test_agents_list_endpoint() -> None:
    """Agents list endpoint should return discoverable agent metadata."""
    with TestClient(app) as client:
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["agents"] == [
            {
                "name": "orchestrator",
                "description": "Runs the LangGraph agent orchestration workflow.",
            }
        ]


def test_agents_run_endpoint() -> None:
    """Agents run endpoint should accept input and return output."""
    with patch("routes.agents.build_graph") as mock_build:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "messages": [AsyncMock(content="Hello! How can I help you?")]
        }
        mock_build.return_value = mock_graph

        with TestClient(app) as client:
            response = client.post("/agents/run", json={"messages": [{"content": "Hi"}]})
            assert response.status_code == 200
            data = response.json()
            assert "output" in data
            assert "messages" in data


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
        patch("retriever.OpenAIEmbeddings") as mock_embeddings,
        patch("pipeline.ChatOpenAI") as mock_llm,
    ):
        mock_embeddings.return_value = AsyncMock()
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

        # Mock the similarity search to return empty chunks (no retrieval needed)
        with patch("retriever.VectorRetriever.similarity_search") as mock_search:
            mock_search.return_value = []

            with TestClient(app) as client:
                response = client.post("/rag/query", json={"question": "What is AI?"})
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert data["question"] == "What is AI?"

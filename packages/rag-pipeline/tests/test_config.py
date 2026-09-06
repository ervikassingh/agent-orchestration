"""Basic tests for the RAG pipeline config."""

from rag_pipeline import RAGConfig


def test_default_config() -> None:
    config = RAGConfig()
    assert config.embedding_model == "text-embedding-3-small"
    assert config.chunk_size == 1000
    assert config.k_retrieval == 4
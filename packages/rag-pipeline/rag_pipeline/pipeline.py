"""Configuration and pipeline for RAG operations."""

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


class RAGConfig(BaseModel):
    """Configuration for the RAG pipeline."""

    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    k_retrieval: int = 4
    collection_name: str = "agent-docs"
    persist_directory: str = "./data/vectorstore"


@dataclass
class Chunk:
    """A single text chunk with metadata."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_id: str = ""


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""

    chunks: list[Chunk]
    query: str
    scores: list[float] = field(default_factory=list)


class RAGPipeline:
    """
    End-to-end RAG pipeline.

    Handles: document loading → chunking → embedding → storing → retrieval → generation.
    """

    def __init__(self, config: RAGConfig | None = None) -> None:
        self.config = config or RAGConfig()
        self._vectorstore = None

    async def ingest_document(self, file_path: str) -> int:
        """Load, chunk, embed, and store a document. Returns chunk count."""
        raise NotImplementedError  # TODO: implement in lesson

    async def query(self, question: str) -> str:
        """Retrieve relevant context and generate an answer."""
        raise NotImplementedError  # TODO: implement in lesson

    async def retrieve(self, question: str) -> RetrievalResult:
        """Retrieve relevant chunks without generation."""
        raise NotImplementedError  # TODO: implement in lesson
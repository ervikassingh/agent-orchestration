"""Vector store retriever using Chroma and OpenAI embeddings."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


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


class VectorRetriever:
    """
    Wraps a Chroma vector store with OpenAI embeddings.

    Provides similarity search and text ingestion.
    """

    def __init__(
        self,
        collection_name: str = "agent-docs",
        persist_directory: str = "./data/vectorstore",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        self._embeddings = OpenAIEmbeddings(model=embedding_model)
        self._store = Chroma(
            collection_name=collection_name,
            embedding_function=self._embeddings,
            persist_directory=persist_directory,
        )

    async def similarity_search(self, query: str, k: int = 4) -> list[Chunk]:
        """Perform pure vector similarity search, returning the top-k chunks."""
        docs = await self._store.asimilarity_search(query, k=k)
        return [
            Chunk(
                text=doc.page_content,
                metadata=dict(doc.metadata) if doc.metadata else {},
                chunk_id=doc.id or "",
            )
            for doc in docs
        ]

    async def hybrid_search(self, query: str, k: int = 4) -> RetrievalResult:
        """Fall back to similarity search (pure vector) for now."""
        chunks = await self.similarity_search(query, k=k)
        return RetrievalResult(chunks=chunks, query=query, scores=[])

    async def add_texts(
        self,
        texts: Sequence[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> list[str]:
        """Add texts (and optional metadata) to the vector store. Returns IDs."""
        ids = await self._store.aadd_texts(
            texts=list(texts),
            metadatas=metadatas or [{}] * len(texts),
        )
        return ids

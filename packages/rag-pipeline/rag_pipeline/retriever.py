"""Vector store retriever abstraction."""

from collections.abc import Sequence

from rag_pipeline.pipeline import Chunk, RetrievalResult


class VectorRetriever:
    """
    Wraps a Chroma / FAISS vector store with hybrid search capabilities.
    """

    def __init__(self, collection_name: str = "agent-docs") -> None:
        self.collection_name = collection_name
        self._store = None

    async def similarity_search(self, query: str, k: int = 4) -> list[Chunk]:
        """Perform pure vector similarity search."""
        raise NotImplementedError  # TODO: implement in lesson

    async def hybrid_search(self, query: str, k: int = 4) -> RetrievalResult:
        """Perform hybrid search (vector + keyword)."""
        raise NotImplementedError  # TODO: implement in lesson

    async def add_texts(
        self, texts: Sequence[str], metadatas: list[dict] | None = None
    ) -> list[str]:
        """Add texts to the vector store."""
        raise NotImplementedError  # TODO: implement in lesson
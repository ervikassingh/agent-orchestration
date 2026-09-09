"""Configuration and pipeline for RAG operations."""

import os

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from rag_pipeline.retriever import Chunk, RetrievalResult, VectorRetriever

__all__ = ["RAGConfig", "RAGPipeline", "Chunk", "RetrievalResult"]


class RAGConfig(BaseModel):
    """Configuration for the RAG pipeline."""

    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    k_retrieval: int = 4
    collection_name: str = "agent-docs"
    persist_directory: str = "./data/vectorstore"
    llm_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.3


class RAGPipeline:
    """
    End-to-end RAG pipeline.

    Handles: document loading → chunking → embedding → storing → retrieval → generation.
    """

    def __init__(self, config: RAGConfig | None = None) -> None:
        self.config = config or RAGConfig()
        self._vectorstore: VectorRetriever | None = None

    @property
    def retriever(self) -> VectorRetriever:
        """Lazy-initialised vector retriever."""
        if self._vectorstore is None:
            self._vectorstore = VectorRetriever(
                collection_name=self.config.collection_name,
                persist_directory=self.config.persist_directory,
                embedding_model=self.config.embedding_model,
            )
        return self._vectorstore

    async def ingest_document(self, file_path: str) -> int:
        """Load, chunk, embed, and store a document. Returns chunk count."""
        if not os.path.isfile(file_path):
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        # Load the document using LangChain's document loaders
        docs: list[Document]
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader  # noqa: PLC0415

            loader = PyPDFLoader(file_path)
            docs = await loader.aload()
        elif ext in {".txt", ".md", ".rst"}:
            from langchain_community.document_loaders import TextLoader  # noqa: PLC0415

            loader = TextLoader(file_path, encoding="utf-8")
            docs = await loader.aload()
        else:
            msg = f"Unsupported file extension: {ext}. Supported: .pdf, .txt, .md, .rst"
            raise ValueError(msg)

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        # Add to vector store
        texts = [c.page_content for c in chunks]
        metadatas = [dict(c.metadata) for c in chunks]
        ids = await self.retriever.add_texts(texts, metadatas)

        return len(ids)

    async def query(self, question: str) -> str:
        """Retrieve relevant context and generate an answer."""
        # Retrieve relevant chunks
        chunks = await self.retriever.similarity_search(question, k=self.config.k_retrieval)

        if not chunks:
            return "I could not find any relevant information in the knowledge base."

        context = "\n\n".join(f"[{i+1}] {c.text}" for i, c in enumerate(chunks))

        prompt = (
            "You are a helpful research assistant. Answer the question based solely on the "
            "provided context. If the context does not contain enough information, say so.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        llm = ChatOpenAI(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
        )
        response = await llm.ainvoke(prompt)

        return response.content if hasattr(response, "content") else str(response)

    async def retrieve(self, question: str) -> RetrievalResult:
        """Retrieve relevant chunks without generation."""
        chunks = await self.retriever.similarity_search(question, k=self.config.k_retrieval)
        return RetrievalResult(chunks=chunks, query=question)

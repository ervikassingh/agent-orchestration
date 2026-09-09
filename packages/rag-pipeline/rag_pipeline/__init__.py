"""
rag-pipeline — Retrieval-Augmented Generation pipeline.

Provides:
- Document loaders (PDF, text, web)
- Text chunking strategies
- Embedding & vector store management
- Retriever with hybrid search
- RAG chain factory
"""

from rag_pipeline.pipeline import RAGConfig, RAGPipeline
from rag_pipeline.retriever import VectorRetriever

__all__ = [
    "RAGPipeline",
    "RAGConfig",
    "VectorRetriever",
]

__version__ = "0.1.0"

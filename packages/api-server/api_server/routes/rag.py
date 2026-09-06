"""RAG-related API routes."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/query")
async def rag_query(question: str) -> dict:
    """Query the RAG pipeline with a question."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/ingest")
async def ingest_document(file_path: str) -> dict:
    """Ingest a document into the vector store."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
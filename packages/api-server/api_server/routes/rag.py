"""RAG-related API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class RAGQueryInput(BaseModel):
    """Input for a RAG query."""

    question: str


class RAGIngestInput(BaseModel):
    """Input for document ingestion."""

    file_path: str


@router.post("/query")
async def rag_query(input_data: RAGQueryInput, request: Request) -> dict[str, Any]:
    """Query the RAG pipeline with a question."""
    pipeline = request.app.state.rag_pipeline
    answer = await pipeline.query(input_data.question)
    return {"answer": answer, "question": input_data.question}


@router.post("/ingest")
async def ingest_document(input_data: RAGIngestInput, request: Request) -> dict[str, Any]:
    """Ingest a document into the vector store."""
    pipeline = request.app.state.rag_pipeline
    try:
        chunk_count = await pipeline.ingest_document(input_data.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {input_data.file_path}",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    return {
        "message": f"Ingested {chunk_count} chunks",
        "chunk_count": chunk_count,
        "file_path": input_data.file_path,
    }

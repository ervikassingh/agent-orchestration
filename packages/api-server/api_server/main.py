"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_server.routes import agents, rag


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    # TODO: initialise registry, vector store, etc.
    yield


app = FastAPI(
    title="Agent Orchestration Service",
    description="A learning-oriented agent orchestration service powered by LangChain & LangGraph",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/agents", tags=["Agents"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
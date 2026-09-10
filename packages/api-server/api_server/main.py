"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rag_pipeline import RAGConfig, RAGPipeline
from tool_library import ToolRegistry

from .routes import agents, rag


def _use_uvicorn_logging() -> None:
    """Route application loggers through Uvicorn's default handler/formatter."""
    uvicorn_logger = logging.getLogger("uvicorn")
    for name in ("api_server", "orchestrator"):
        app_logger = logging.getLogger(name)
        app_logger.setLevel(logging.INFO)
        if uvicorn_logger.handlers:
            app_logger.handlers = uvicorn_logger.handlers
            app_logger.propagate = False


_use_uvicorn_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    tool_registry = ToolRegistry()
    rag_config = RAGConfig()
    rag_pipeline = RAGPipeline(config=rag_config)

    app.state.tool_registry = tool_registry
    app.state.rag_pipeline = rag_pipeline

    yield


app = FastAPI(
    title="Agent Orchestration Service",
    description="An agent orchestration service powered by LangChain & LangGraph",
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

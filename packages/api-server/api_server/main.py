"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core_agent.registry import AgentRegistry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rag_pipeline.pipeline import RAGConfig, RAGPipeline
from tool_library.registry import ToolRegistry

from api_server.routes import agents, rag


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown events."""
    # Initialise registries and RAG pipeline
    agent_registry = AgentRegistry()
    tool_registry = ToolRegistry()
    rag_config = RAGConfig()
    rag_pipeline = RAGPipeline(config=rag_config)

    app.state.agent_registry = agent_registry
    app.state.tool_registry = tool_registry
    app.state.rag_pipeline = rag_pipeline

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

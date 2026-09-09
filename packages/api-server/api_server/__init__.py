"""
api-server — FastAPI server for agent orchestration.

Endpoints:
- POST /agents/{name}/run    — Run an agent
- POST /agents/{name}/stream — Stream agent output
- GET  /agents               — List registered agents
- POST /rag/query            — Query the RAG pipeline
- POST /rag/ingest           — Ingest a document
"""

from api_server.main import app

__all__ = ["app"]

__version__ = "0.1.0"

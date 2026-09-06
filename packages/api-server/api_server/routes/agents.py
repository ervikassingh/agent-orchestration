"""Agent-related API routes."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
async def list_agents() -> dict:
    """List all registered agents."""
    # TODO: wire up AgentRegistry
    return {"agents": []}


@router.post("/{name}/run")
async def run_agent(name: str, input_data: dict) -> dict:
    """Run an agent by name with the given input."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{name}/stream")
async def stream_agent(name: str, input_data: dict) -> dict:
    """Stream agent output via SSE."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
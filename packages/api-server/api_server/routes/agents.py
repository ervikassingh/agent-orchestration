"""Agent-related API routes."""

from core_agent.base import AgentConfig
from core_agent.graph import AgentGraph, AgentState
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class RunAgentInput(BaseModel):
    """Input for running or streaming an agent."""

    messages: list[dict] = []
    context: dict = {}


@router.get("")
async def list_agents(request: Request) -> dict:
    """List all registered agents."""
    registry = request.app.state.agent_registry
    agents_info = [
        {"name": name, "description": ""}
        for name in registry.list_agents()
    ]
    return {"agents": agents_info}


@router.post("/{name}/run")
async def run_agent(name: str, input_data: RunAgentInput, request: Request) -> dict:
    """Run an agent by name with the given input."""
    registry = request.app.state.agent_registry

    try:
        agent_cls = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {name!r}") from None

    config = AgentConfig(name=name)
    agent_cls(config=config)  # validate instantiation
    agent_graph = AgentGraph()

    state = AgentState(
        messages=input_data.messages,
        context=input_data.context,
    )
    result = await agent_graph.run(state)

    return {
        "agent": name,
        "output": result.agent_outputs.get(name, ""),
        "messages": [m.model_dump() if hasattr(m, "model_dump") else m for m in result.messages],
        "success": result.error is None,
        "error": result.error,
    }


@router.post("/{name}/stream")
async def stream_agent(name: str, input_data: RunAgentInput, request: Request) -> StreamingResponse:
    """Stream agent output via SSE."""
    registry = request.app.state.agent_registry

    try:
        agent_cls = registry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {name!r}") from None

    config = AgentConfig(name=name)
    agent_cls(config=config)  # validate instantiation
    agent_graph = AgentGraph()

    state = AgentState(
        messages=input_data.messages,
        context=input_data.context,
    )

    async def event_stream():
        async for event in agent_graph.stream(state):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

"""Agent-related API routes."""

from core_agent.base import AgentConfig
from core_agent.graph import OrchestratorState, build_orchestrator_graph
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

router = APIRouter()


class RunAgentInput(BaseModel):
    """Input for running or streaming an agent."""

    messages: list[dict] = []
    context: dict = {}


def _messages_from_input(input_data: RunAgentInput) -> list[HumanMessage]:
    """Convert raw message dicts into LangChain HumanMessage instances."""
    return [
        HumanMessage(content=m.get("content", ""))
        for m in input_data.messages
    ]


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

    graph = build_orchestrator_graph()
    state = OrchestratorState(
        messages=_messages_from_input(input_data),
        context=input_data.context,
    )
    result = await graph.ainvoke(state)

    # LangGraph returns a dict; normalise back to a serialisable response.
    messages = result.get("messages", []) if isinstance(result, dict) else result.messages
    last_content = ""
    for msg in reversed(messages):
        if getattr(msg, "content", None):
            last_content = msg.content
            break

    return {
        "agent": name,
        "output": last_content,
        "messages": [m.model_dump() if hasattr(m, "model_dump") else m for m in messages],
        "success": True,
        "error": None,
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

    graph = build_orchestrator_graph()
    state = OrchestratorState(
        messages=_messages_from_input(input_data),
        context=input_data.context,
    )

    async def event_stream():
        async for event in graph.astream_events(state, version="v2"):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

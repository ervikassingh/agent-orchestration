"""Agent-related API routes."""

import inspect

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from graph import State, build_graph
from pydantic import BaseModel

router = APIRouter()


class RunAgentInput(BaseModel):
    """Input for running or streaming the orchestrator."""

    messages: list[dict] = []


def _messages_from_input(input_data: RunAgentInput) -> list[HumanMessage]:
    """Convert raw message dicts into LangChain HumanMessage instances."""
    return [
        HumanMessage(content=m.get("content", ""))
        for m in input_data.messages
    ]


@router.post("/run")
async def run_agent(input_data: RunAgentInput) -> dict:
    """Run the orchestrator with the given input."""
    graph = build_graph()
    state = State(messages=_messages_from_input(input_data))
    result = await graph.ainvoke(state)

    # LangGraph returns a dict; normalise back to a serialisable response.
    messages = result.get("messages", []) if isinstance(result, dict) else result.messages
    last_content = ""
    for msg in reversed(messages):
        if getattr(msg, "content", None):
            last_content = msg.content
            break

    serialised_messages = []
    for message in messages:
        content = getattr(message, "content", None)
        if inspect.isawaitable(content):
            content = ""
        if isinstance(content, str):
            serialised_messages.append({"content": content})
        elif hasattr(message, "model_dump"):
            dumped = message.model_dump()
            serialised_messages.append({"content": ""} if inspect.isawaitable(dumped) else dumped)
        else:
            serialised_messages.append({"content": content or ""})

    return {
        "output": last_content,
        "messages": serialised_messages,
    }


@router.post("/stream")
async def stream_agent(input_data: RunAgentInput) -> StreamingResponse:
    """Stream orchestrator output via SSE."""
    graph = build_graph()
    state = State(messages=_messages_from_input(input_data))

    async def event_stream():
        async for event in graph.astream_events(state, version="v1"):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

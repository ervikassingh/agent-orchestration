"""Agent-related API routes."""

import inspect
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from graph import State, build_graph
from openai import OpenAIError
from pydantic import BaseModel
from settings import settings

router = APIRouter()


class RunAgentInput(BaseModel):
    """Input for running or streaming the orchestrator."""

    messages: list[dict] = []


@router.get("")
async def list_agents() -> dict:
    """Return the agents available to the web UI."""
    return {
        "agents": [
            {
                "name": "orchestrator",
                "description": "Runs the LangGraph agent orchestration workflow.",
            }
        ]
    }


def _messages_from_input(input_data: RunAgentInput) -> list[BaseMessage]:
    """Convert raw message dicts into LangChain message instances."""
    messages = []
    for message in input_data.messages:
        content = message.get("content", "")
        role = message.get("role", "user")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    return messages


@router.post("/run")
async def run_agent(input_data: RunAgentInput) -> dict:
    """Run the orchestrator with the given input."""
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured. Add it to .env and restart the API.",
        )

    graph = build_graph()
    state = State(messages=_messages_from_input(input_data))
    try:
        result = await graph.ainvoke(state)
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"The configured LLM provider rejected the request: {exc}",
        ) from exc

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
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured. Add it to .env and restart the API.",
        )

    graph = build_graph()
    state = State(messages=_messages_from_input(input_data))

    async def event_stream():
        try:
            async for event in graph.astream_events(state, version="v1"):
                if event.get("event") != "on_chat_model_stream":
                    continue

                content = event.get("data", {}).get("chunk", {}).content
                if isinstance(content, str) and content:
                    yield f"data: {json.dumps({'token': content})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except OpenAIError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

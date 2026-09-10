"""Agent-related API routes."""

import inspect
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from graph import State, build_graph
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from openai import OpenAIError
from pydantic import BaseModel
from settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class RunAgentInput(BaseModel):
    """Input for running or streaming the orchestrator."""

    messages: list[dict[str, Any]] = []


@router.get("")
async def list_agents() -> dict[str, Any]:
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
    messages: list[BaseMessage] = []
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
async def run_agent(input_data: RunAgentInput) -> dict[str, Any]:
    """Run the orchestrator with the given input."""
    logger.info("agent_request_started endpoint=run input_messages=%d", len(input_data.messages))
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
        logger.exception("agent_request_failed endpoint=run provider_error=%s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"The configured LLM provider rejected the request: {exc}",
        ) from exc

    # LangGraph returns a dict; normalise back to a serialisable response.
    messages = result.get("messages", []) if isinstance(result, dict) else result.messages
    tool_outputs = (
        result.get("tool_outputs", {}) if isinstance(result, dict) else result.tool_outputs
    )
    logger.info(
        "agent_request_completed endpoint=run iterations=%s tools_used=%s",
        result.get("iterations") if isinstance(result, dict) else result.iterations,
        [output.get("name") for output in tool_outputs.values()],
    )
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
    logger.info("agent_request_started endpoint=stream input_messages=%d", len(input_data.messages))
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured. Add it to .env and restart the API.",
        )

    graph = build_graph()
    state = State(messages=_messages_from_input(input_data))

    async def event_stream() -> AsyncIterator[str]:
        try:
            async for message_chunk, _metadata in graph.astream(state, stream_mode="messages"):
                content = getattr(message_chunk, "content", "")
                if isinstance(content, str) and content:
                    yield f"data: {json.dumps({'token': content})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
            logger.info("agent_request_completed endpoint=stream")
        except OpenAIError as exc:
            logger.exception("agent_request_failed endpoint=stream provider_error=%s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

"""LangGraph-based tool-calling orchestrator."""

import logging
from typing import Annotated, Any, Literal

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from .settings import settings
from .tool_adapter import build_langchain_tools

logger = logging.getLogger(__name__)


class State(BaseModel):
    """State for the tool-calling orchestration loop."""

    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    tool_outputs: dict[str, Any] = Field(default_factory=dict)
    iterations: int = 0
    max_iterations: int = Field(default_factory=lambda: settings.MAX_TOOL_ITERATIONS)
    error: str | None = None


def _get_llm() -> ChatOpenAI:
    """Lazily construct the ChatOpenAI client so module import doesn't require credentials."""
    return ChatOpenAI(
        model=settings.MODEL,
        temperature=settings.TEMPERATURE,
        max_completion_tokens=settings.MAX_TOKENS,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
    )


_tools = build_langchain_tools()

_SYSTEM_PROMPT = (
    "You are a helpful AI assistant with access to the following tools:\n\n"
    "- **rag_query**: Query the internal knowledge base for information about "
    "documents, research, or stored data.\n"
    "- **web_surf**: Fetch content from a URL on the internet. Use this to get "
    "live information from the web.\n"
    "- **send_email**: Send an email to one or more recipients.\n\n"
    "When a user asks a question:\n"
    "1. If it requires knowledge stored in documents, use **rag_query**.\n"
    "2. If it requires live information from the internet, use **web_surf**.\n"
    "3. If the user asks you to send a message, use **send_email**.\n\n"
    "You can use multiple tools in sequence if needed. Always explain what you are doing."
)


async def orchestrator_node(state: State) -> dict[str, Any]:
    """Call the LLM with the current conversation and tools."""
    messages = state.messages or []

    # Inject system prompt once at the start
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=_SYSTEM_PROMPT), *messages]

    llm = _get_llm()
    llm_with_tools = llm.bind_tools(_tools)
    logger.info(
        "agent_step=llm_call iteration=%d message_count=%d tools_available=%s",
        state.iterations + 1,
        len(messages),
        [tool.name for tool in _tools],
    )
    response = await llm_with_tools.ainvoke(messages)
    logger.info(
        "agent_step=llm_response iteration=%d tool_calls=%s",
        state.iterations + 1,
        [call.get("name") for call in getattr(response, "tool_calls", [])],
    )

    return {
        "messages": [response],
        "iterations": state.iterations + 1,
    }


async def tools_node(state: State) -> dict[str, Any]:
    """Execute tool calls and collect results."""
    last_message = state.messages[-1] if state.messages else None
    tool_calls = getattr(last_message, "tool_calls", [])
    logger.info(
        "agent_step=tool_execution iteration=%d tool_calls=%s",
        state.iterations,
        [
            {"name": call.get("name"), "id": call.get("id")}
            for call in tool_calls
        ],
    )
    tool_node = ToolNode(_tools)
    result = await tool_node.ainvoke(state)

    # Extract tool outputs into the state dictionary, keyed by tool_call_id
    # so repeated calls to the same tool don't overwrite each other.
    tool_outputs: dict[str, Any] = {}
    for msg in result.get("messages", []):
        if hasattr(msg, "name") and msg.name:
            output = msg.content
            output_metadata = {
                "content_length": len(output) if isinstance(output, str) else None,
            }
            if isinstance(output, dict):
                output_metadata.update(
                    {
                        "source": output.get("source"),
                        "length": output.get("length"),
                    }
                )
            logger.info(
                "tool_used name=%s iteration=%d success=true metadata=%s",
                msg.name,
                state.iterations,
                output_metadata,
            )
            tool_outputs[msg.tool_call_id] = {
                "name": msg.name,
                "content": output,
            }

    return {
        "messages": result.get("messages", []),
        "tool_outputs": {**state.tool_outputs, **tool_outputs},
    }


# ---------------------------------------------------------------------------
# Conditional edge logic
# ---------------------------------------------------------------------------


def should_continue(state: State) -> Literal["tools", "__end__"]:
    """Decide whether to continue the tool loop or finish."""
    if state.iterations >= state.max_iterations:
        return "__end__"

    last_message = state.messages[-1] if state.messages else None
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "__end__"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_graph() -> CompiledStateGraph[State, None, State, State]:
    """Build and compile the tool-calling orchestration graph."""
    workflow = StateGraph(State)

    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tools", tools_node)

    workflow.set_entry_point("orchestrator")
    workflow.add_conditional_edges("orchestrator", should_continue)
    workflow.add_edge("tools", "orchestrator")

    return workflow.compile()

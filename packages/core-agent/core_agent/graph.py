"""LangGraph-based agent orchestration graph."""

from typing import Any, Literal

from langgraph.graph import END, StateGraph, StateGraph
from pydantic import BaseModel


class AgentState(BaseModel):
    """Shared state that flows through the agent graph."""

    messages: list[dict[str, Any]] = []
    current_agent: str = ""
    agent_outputs: dict[str, str] = {}
    context: dict[str, Any] = {}
    error: str | None = None


def build_agent_graph() -> StateGraph:
    """
    Build the base LangGraph state machine for agent orchestration.

    Returns a compiled graph ready to invoke or extend.
    """
    workflow = StateGraph(AgentState)

    # Nodes will be added by subclasses / users of the framework
    workflow.set_entry_point("__start__")
    workflow.add_edge("__start__", END)

    return workflow.compile()


class AgentGraph:
    """High-level wrapper around the compiled LangGraph."""

    def __init__(self) -> None:
        self.graph = build_agent_graph()

    async def run(self, initial_state: AgentState) -> AgentState:
        """Execute the graph with an initial state."""
        return await self.graph.ainvoke(initial_state)

    async def stream(self, initial_state: AgentState):
        """Stream graph execution events."""
        async for event in self.graph.astream_events(initial_state, version="v2"):
            yield event
"""Tests for the LangGraph orchestrator graph."""

import pytest
from core_agent.graph import (
    AgentGraph,
    AgentState,
    OrchestratorState,
    build_agent_graph,
    build_orchestrator_graph,
    should_continue,
)
from langchain_core.messages import AIMessage, HumanMessage


def test_agent_state_defaults() -> None:
    """AgentState should have sensible defaults."""
    state = AgentState()
    assert state.messages == []
    assert state.current_agent == ""
    assert state.agent_outputs == {}
    assert state.context == {}
    assert state.error is None


def test_orchestrator_state_defaults() -> None:
    """OrchestratorState should have sensible defaults."""
    state = OrchestratorState()
    assert state.messages == []
    assert state.iterations == 0
    assert state.tool_outputs == {}
    assert state.error is None


def test_build_agent_graph_returns_compiled_graph() -> None:
    """build_agent_graph should return a compiled graph."""
    graph = build_agent_graph()
    assert graph is not None


def test_build_orchestrator_graph_returns_compiled_graph() -> None:
    """build_orchestrator_graph should return a compiled graph."""
    graph = build_orchestrator_graph()
    assert graph is not None


def test_agent_graph_wrapper_initialises() -> None:
    """AgentGraph wrapper should initialise without error."""
    wrapper = AgentGraph()
    assert wrapper.graph is not None


def test_should_continue_returns_end_when_no_tool_calls() -> None:
    """should_continue should return END when the last message has no tool calls."""
    msg = AIMessage(content="hello")
    state = OrchestratorState(messages=[msg], iterations=0)
    result = should_continue(state)
    assert result == "__end__"


def test_should_continue_returns_tools_when_tool_calls_present() -> None:
    """should_continue should return 'tools' when tool_calls are present."""
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "web_surf", "args": {"url": "https://example.com"}, "id": "1"}],
    )
    state = OrchestratorState(messages=[msg], iterations=0)
    result = should_continue(state)
    assert result == "tools"


def test_should_continue_returns_end_when_max_iterations_reached() -> None:
    """should_continue should return END when max iterations are reached."""
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "web_surf", "args": {}, "id": "1"}],
    )
    state = OrchestratorState(messages=[msg], iterations=10, max_iterations=10)
    result = should_continue(state)
    assert result == "__end__"


def test_should_continue_returns_end_when_no_messages() -> None:
    """should_continue should return END when there are no messages."""
    state = OrchestratorState(messages=[], iterations=0)
    result = should_continue(state)
    assert result == "__end__"


@pytest.mark.asyncio
async def test_agent_graph_run_returns_state() -> None:
    """AgentGraph.run should return an AgentState."""
    wrapper = AgentGraph()
    initial = AgentState(messages=[{"role": "user", "content": "hi"}])
    result = await wrapper.run(initial)
    assert isinstance(result, AgentState)


def test_orchestrator_state_accepts_human_message() -> None:
    """OrchestratorState should accept real BaseMessage instances."""
    msg = HumanMessage(content="hello")
    state = OrchestratorState(messages=[msg])
    assert len(state.messages) == 1
    assert state.messages[0].content == "hello"

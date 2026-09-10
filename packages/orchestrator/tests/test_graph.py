"""Tests for the LangGraph orchestrator graph."""

import logging

import pytest
from orchestrator import graph as graph_module
from orchestrator.graph import State, build_graph, orchestrator_node, should_continue, tools_node
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages


def test_state_defaults() -> None:
    """State should have sensible defaults."""
    state = State()
    assert state.messages == []
    assert state.iterations == 0
    assert state.tool_outputs == {}
    assert state.error is None


def test_build_graph_returns_compiled_graph() -> None:
    """build_graph should return a compiled graph."""
    graph = build_graph()
    assert graph is not None


def test_should_continue_returns_end_when_no_tool_calls() -> None:
    """should_continue should return END when the last message has no tool calls."""
    msg = AIMessage(content="hello")
    state = State(messages=[msg], iterations=0)
    result = should_continue(state)
    assert result == "__end__"


def test_should_continue_returns_tools_when_tool_calls_present() -> None:
    """should_continue should return 'tools' when tool_calls are present."""
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "web_surf", "args": {"url": "https://example.com"}, "id": "1"}],
    )
    state = State(messages=[msg], iterations=0)
    result = should_continue(state)
    assert result == "tools"


def test_should_continue_returns_end_when_max_iterations_reached() -> None:
    """should_continue should return END when max iterations are reached."""
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "web_surf", "args": {}, "id": "1"}],
    )
    state = State(messages=[msg], iterations=10, max_iterations=10)
    result = should_continue(state)
    assert result == "__end__"


def test_should_continue_returns_end_when_no_messages() -> None:
    """should_continue should return END when there are no messages."""
    state = State(messages=[], iterations=0)
    result = should_continue(state)
    assert result == "__end__"


@pytest.mark.asyncio
async def test_state_accepts_human_message() -> None:
    """State should accept real BaseMessage instances."""
    msg = HumanMessage(content="hello")
    state = State(messages=[msg])
    assert len(state.messages) == 1
    assert state.messages[0].content == "hello"


def test_state_preserves_tool_call_history() -> None:
    """Tool results must remain paired with the assistant tool call."""
    assistant = AIMessage(
        content="",
        tool_calls=[{"name": "web_surf", "args": {"url": "https://example.com"}, "id": "1"}],
    )
    tool_result = ToolMessage(content="page content", tool_call_id="1", name="web_surf")

    merged_messages = add_messages([assistant], [tool_result])

    assert merged_messages == [assistant, tool_result]

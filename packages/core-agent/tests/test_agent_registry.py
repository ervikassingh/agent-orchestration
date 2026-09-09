"""Tests for the agent registry."""

import pytest
from core_agent.base import AgentResult, BaseAgent
from core_agent.registry import AgentRegistry


class DummyAgent(BaseAgent):
    """Minimal agent for testing."""

    async def run(self, input_data: dict) -> AgentResult:
        return AgentResult(agent_name=self.config.name, output="ok")

    async def stream(self, input_data: dict):  # type: ignore[override]
        yield "ok"


def test_register_and_retrieve() -> None:
    registry = AgentRegistry()
    registry.register("dummy", DummyAgent)
    assert "dummy" in registry
    assert registry.get("dummy") is DummyAgent


def test_register_non_agent_raises() -> None:
    registry = AgentRegistry()
    with pytest.raises(TypeError):
        registry.register("bad", str)  # type: ignore[arg-type]


def test_get_unknown_agent_raises() -> None:
    registry = AgentRegistry()
    with pytest.raises(KeyError):
        registry.get("nope")


def test_list_agents() -> None:
    registry = AgentRegistry()
    registry.register("a", DummyAgent)
    registry.register("b", DummyAgent)
    assert set(registry.list_agents()) == {"a", "b"}

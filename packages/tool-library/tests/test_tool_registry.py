"""Tests for the tool registry."""

import pytest
from base import BaseTool, ToolConfig, ToolResult
from registry import ToolRegistry


class DummyTool(BaseTool):
    """Minimal tool for testing."""

    async def run(self, input_data: dict) -> ToolResult:
        return ToolResult(tool_name=self.config.name, output="ok")


def test_register_and_retrieve() -> None:
    registry = ToolRegistry()
    registry.register("dummy", DummyTool)
    assert "dummy" in registry
    assert registry.get("dummy") is DummyTool


def test_register_non_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(TypeError):
        registry.register("bad", str)  # type: ignore[arg-type]


def test_get_unknown_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get("nope")


def test_list_tools() -> None:
    registry = ToolRegistry()
    registry.register("a", DummyTool)
    registry.register("b", DummyTool)
    assert set(registry.list_tools()) == {"a", "b"}


def test_default_config() -> None:
    config = ToolConfig(name="dummy")
    assert config.timeout_seconds == 30.0
    assert config.max_retries == 2

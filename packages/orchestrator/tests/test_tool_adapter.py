"""Tests for the tool adapter that bridges BaseTool to LangChain StructuredTool."""

import pytest
from langchain_core.tools import StructuredTool
from base import BaseTool, ToolConfig, ToolResult
from tools.email_tool import EmailTool
from tools.rag_tool import RAGTool
from tools.web_tool import WebSurfTool

from tool_adapter import (
    EmailSchema,
    RAGSchema,
    WebSurfSchema,
    build_langchain_tools,
    tool_to_langchain,
)


class DummyTool(BaseTool):
    """Minimal tool for testing the adapter."""

    async def run(self, input_data: dict) -> ToolResult:
        return ToolResult(
            tool_name=self.config.name,
            output=f"got: {input_data}",
        )


def test_tool_to_langchain_returns_structured_tool() -> None:
    """Adapter should return a LangChain StructuredTool."""
    tool = DummyTool(ToolConfig(name="dummy", description="A dummy tool"))
    lc_tool = tool_to_langchain(tool)
    assert isinstance(lc_tool, StructuredTool)
    assert lc_tool.name == "dummy"
    assert lc_tool.description == "A dummy tool"


def test_tool_to_langchain_uses_registered_schema() -> None:
    """Adapter should use the registered schema for known tool names."""
    rag_tool = RAGTool()
    lc_tool = tool_to_langchain(rag_tool)
    assert lc_tool.args_schema is RAGSchema

    web_tool = WebSurfTool()
    lc_tool = tool_to_langchain(web_tool)
    assert lc_tool.args_schema is WebSurfSchema

    email_tool = EmailTool()
    lc_tool = tool_to_langchain(email_tool)
    assert lc_tool.args_schema is EmailSchema


def test_tool_to_langchain_unknown_schema_falls_back() -> None:
    """Unknown tool names should still produce a valid StructuredTool."""
    tool = DummyTool(ToolConfig(name="unknown_tool", description="Unknown"))
    lc_tool = tool_to_langchain(tool)
    assert isinstance(lc_tool, StructuredTool)
    assert lc_tool.name == "unknown_tool"


@pytest.mark.asyncio
async def test_tool_to_langchain_arun_returns_output() -> None:
    """The wrapped coroutine should return the tool's output on success."""
    tool = DummyTool(ToolConfig(name="dummy", description="dummy"))
    lc_tool = tool_to_langchain(tool)

    # Invoke the underlying coroutine directly
    result = await lc_tool.coroutine(query="hello")  # type: ignore[attr-defined]
    assert "got:" in result


@pytest.mark.asyncio
async def test_tool_to_langchain_arun_raises_on_error() -> None:
    """The wrapped coroutine should raise RuntimeError on tool failure."""

    class FailingTool(BaseTool):
        async def run(self, input_data: dict) -> ToolResult:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error="boom",
            )

    tool = FailingTool(ToolConfig(name="failing", description="fails"))
    lc_tool = tool_to_langchain(tool)

    with pytest.raises(RuntimeError, match="boom"):
        await lc_tool.coroutine(x=1)  # type: ignore[attr-defined]


def test_build_langchain_tools_returns_all_builtins() -> None:
    """build_langchain_tools should return all three built-in tools."""
    tools = build_langchain_tools()
    assert len(tools) == 3
    names = {t.name for t in tools}
    assert names == {"rag_query", "web_surf", "send_email"}
    for t in tools:
        assert isinstance(t, StructuredTool)

"""Bridge between custom BaseTool implementations and LangChain's StructuredTool."""

from typing import Any

from base import BaseTool
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from tools.email_tool import EmailTool
from tools.rag_tool import RAGTool
from tools.web_tool import WebSurfTool


class RAGSchema(BaseModel):
    """Input schema for the RAG query tool."""

    query: str = Field(description="The query to search the knowledge base with")


class WebSurfSchema(BaseModel):
    """Input schema for the web surfing tool."""

    url: str = Field(description="The URL to fetch content from")
    max_chars: int = Field(default=8000, description="Maximum characters to return")


class EmailSchema(BaseModel):
    """Input schema for the email sending tool."""

    to: str = Field(description="Recipient email address(es), comma-separated")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body text")


_SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "rag_query": RAGSchema,
    "web_surf": WebSurfSchema,
    "send_email": EmailSchema,
}


def tool_to_langchain(tool_instance: BaseTool) -> StructuredTool:
    """
    Wrap a ``BaseTool`` instance as a LangChain ``StructuredTool``.

    The tool's input schema is looked up from ``_SCHEMA_MAP`` using
    ``tool_instance.config.name``. If no schema is registered, a generic
    dict-based schema is used.
    """
    schema = _SCHEMA_MAP.get(tool_instance.config.name)

    async def _arun(**kwargs: Any) -> Any:
        result = await tool_instance.arun(kwargs)
        if result.success:
            return result.output
        msg = result.error or "Unknown tool error"
        raise RuntimeError(msg)

    return StructuredTool.from_function(
        name=tool_instance.config.name,
        description=tool_instance.config.description,
        coroutine=_arun,
        args_schema=schema,
    )


def build_langchain_tools() -> list[StructuredTool]:
    """Instantiate all built-in tools and wrap them for LangChain use."""
    tools: list[BaseTool] = [
        RAGTool(),
        WebSurfTool(),
        EmailTool(),
    ]
    return [tool_to_langchain(t) for t in tools]

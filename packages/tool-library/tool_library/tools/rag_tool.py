"""RAG query tool — queries the RAG pipeline via HTTP."""

import httpx

from tool_library.base import BaseTool, ToolConfig, ToolResult


class RAGTool(BaseTool):
    """Query the RAG pipeline for information retrieval."""

    def __init__(self) -> None:
        config = ToolConfig(
            name="rag_query",
            description="Query the RAG system for information from the knowledge base",
            timeout_seconds=30.0,
        )
        super().__init__(config)

    async def run(self, input_data: dict) -> ToolResult:
        query: str = input_data.get("query", "")
        if not query:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error="Missing required parameter: 'query'",
            )

        rag_api_url = "http://localhost:8000/rag/query"

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(rag_api_url, json={"question": query})
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError:
            # RAG service not available — return a graceful fallback
            return ToolResult(
                tool_name=self.config.name,
                output={
                    "answer": (
                        "I could not connect to the knowledge base. "
                        "Please make sure the RAG pipeline is running."
                    ),
                    "source": "fallback",
                },
                metadata={"error": "RAG service unavailable", "query": query},
            )
        except httpx.TimeoutException:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error="RAG query timed out",
            )
        except httpx.HTTPStatusError as exc:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"RAG service returned HTTP {exc.response.status_code}: {exc.response.text}",
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"RAG query failed: {exc}",
            )

        return ToolResult(
            tool_name=self.config.name,
            output=data,
            metadata={"query": query},
        )

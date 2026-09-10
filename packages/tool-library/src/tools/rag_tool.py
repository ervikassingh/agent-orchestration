"""RAG query tool — queries the RAG pipeline via HTTP."""

import httpx

from base import BaseTool, ToolConfig, ToolResult


class RAGTool(BaseTool):
    """Query the RAG pipeline for information retrieval."""

    def __init__(self) -> None:
        super().__init__(ToolConfig(name="rag_query", description="Query the RAG system for information from the knowledge base"))

    async def run(self, input_data: dict) -> ToolResult:
        query = input_data.get("query", "")
        if not query:
            return ToolResult(self.config.name, None, success=False, error="Missing required parameter: 'query'")
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post("http://localhost:8000/rag/query", json={"question": query})
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError:
            return ToolResult(self.config.name, {"answer": "I could not connect to the knowledge base.", "source": "fallback"}, metadata={"error": "RAG service unavailable", "query": query})
        except httpx.TimeoutException:
            return ToolResult(self.config.name, None, success=False, error="RAG query timed out")
        except httpx.HTTPStatusError as exc:
            return ToolResult(self.config.name, None, success=False, error=f"RAG service returned HTTP {exc.response.status_code}: {exc.response.text}")
        except Exception as exc:
            return ToolResult(self.config.name, None, success=False, error=f"RAG query failed: {exc}")
        return ToolResult(self.config.name, data, metadata={"query": query})

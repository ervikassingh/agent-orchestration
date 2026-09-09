"""Web surfing tool — fetches and extracts content from URLs."""

import re

import httpx

from tool_library.base import BaseTool, ToolConfig, ToolResult


class WebSurfTool(BaseTool):
    """Fetch and extract readable text content from a web page."""

    def __init__(self) -> None:
        config = ToolConfig(
            name="web_surf",
            description="Fetch content from a URL and return the readable text",
            timeout_seconds=30.0,
        )
        super().__init__(config)

    async def run(self, input_data: dict) -> ToolResult:
        url: str = input_data.get("url", "")
        if not url:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error="Missing required parameter: 'url'",
            )

        max_chars: int = input_data.get("max_chars", 8000)

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; AgentOrchestration/1.0; "
                            "+https://github.com/ervikassingh/agent-orchestration)"
                        ),
                    },
                    follow_redirects=True,
                )
                response.raise_for_status()
        except httpx.TimeoutException:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"Request to {url} timed out after {self.config.timeout_seconds}s",
            )
        except httpx.HTTPStatusError as exc:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"HTTP {exc.response.status_code} fetching {url}",
            )
        except httpx.RequestError as exc:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"Request failed: {exc}",
            )

        # Strip HTML tags, scripts, and styles
        text = response.text
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[...truncated]"

        return ToolResult(
            tool_name=self.config.name,
            output={"content": text, "source": url, "length": len(text)},
            metadata={"url": url, "truncated": len(text) > max_chars},
        )

"""Web surfing tool — fetches and extracts content from URLs."""

import re

import httpx

from base import BaseTool, ToolConfig, ToolResult


class WebSurfTool(BaseTool):
    """Fetch and extract readable text content from a web page."""

    def __init__(self) -> None:
        super().__init__(ToolConfig(name="web_surf", description="Fetch content from a URL and return the readable text"))

    async def run(self, input_data: dict) -> ToolResult:
        url = input_data.get("url", "")
        if not url:
            return ToolResult(self.config.name, None, success=False, error="Missing required parameter: 'url'")
        max_chars = input_data.get("max_chars", 8000)
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
        except httpx.TimeoutException:
            return ToolResult(self.config.name, None, success=False, error=f"Request to {url} timed out")
        except httpx.HTTPStatusError as exc:
            return ToolResult(self.config.name, None, success=False, error=f"HTTP {exc.response.status_code} fetching {url}")
        except httpx.RequestError as exc:
            return ToolResult(self.config.name, None, success=False, error=f"Request failed: {exc}")
        text = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<[^>]+>", " ", response.text, flags=re.DOTALL)
        text = re.sub(r"\s+", " ", text).strip()
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars] + "\n\n[...truncated]"
        return ToolResult(self.config.name, {"content": text, "source": url, "length": len(text)}, metadata={"url": url, "truncated": truncated})

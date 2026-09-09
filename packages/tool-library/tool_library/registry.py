"""Tool registry — discover and instantiate tools by name."""

from tool_library.base import BaseTool


class ToolRegistry:
    """
    Global registry of available tool types.

    Usage::

        registry = ToolRegistry()
        registry.register("web-search", WebSearchTool)
        tool = registry.get("web-search")(config)
    """

    def __init__(self) -> None:
        self._tools: dict[str, type[BaseTool]] = {}

    def register(self, name: str, tool_cls: type[BaseTool]) -> None:
        """Register a tool class under a human-readable name."""
        if not issubclass(tool_cls, BaseTool):
            msg = f"{tool_cls.__name__} must subclass BaseTool"
            raise TypeError(msg)
        self._tools[name] = tool_cls

    def get(self, name: str) -> type[BaseTool]:
        """Retrieve a tool class by name."""
        if name not in self._tools:
            msg = f"Unknown tool: {name!r}. Available: {list(self._tools)}"
            raise KeyError(msg)
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """Return the names of all registered tools."""
        return list(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

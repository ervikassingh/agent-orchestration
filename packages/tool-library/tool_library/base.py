"""Base tool abstraction used across all tool implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Configuration shared by all tools."""

    name: str
    description: str = ""
    timeout_seconds: float = 30.0
    max_retries: int = 2
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class ToolResult:
    """Standardised result from any tool execution."""

    tool_name: str
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class BaseTool(ABC):
    """Abstract base class for all tools in the orchestration system."""

    def __init__(self, config: ToolConfig) -> None:
        self.config = config

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the tool with the given input data."""

    async def arun(self, input_data: dict[str, Any]) -> ToolResult:
        """Run the tool with retry handling."""
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                return await self.run(input_data)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
        return ToolResult(
            tool_name=self.config.name,
            output=None,
            success=False,
            error=str(last_error),
        )

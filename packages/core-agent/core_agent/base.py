"""Base agent abstraction used across all agent implementations."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration shared by all agents."""

    name: str
    description: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: str = "You are a helpful AI assistant."
    tools: list[str] = field(default_factory=list)  # noqa: PLW0901


@dataclass
class AgentResult:
    """Standardised result from any agent execution."""

    agent_name: str
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


class BaseAgent(ABC):
    """Abstract base class for all agents in the orchestration system."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the agent with the given input data."""

    @abstractmethod
    async def stream(self, input_data: dict[str, Any]) -> AsyncIterator[str]:
        """Stream tokens from the agent execution."""
        ...
        yield  # pragma: no cover

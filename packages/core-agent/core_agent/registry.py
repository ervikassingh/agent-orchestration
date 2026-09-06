"""Agent registry — discover and instantiate agents by name."""

from collections.abc import AsyncIterator
from typing import Any

from core_agent.base import BaseAgent, AgentConfig, AgentResult


class AgentRegistry:
    """
    Global registry of available agent types.

    Usage::

        registry = AgentRegistry()
        registry.register("researcher", ResearcherAgent)
        agent = registry.get("researcher")(config)
    """

    def __init__(self) -> None:
        self._agents: dict[str, type[BaseAgent]] = {}

    def register(self, name: str, agent_cls: type[BaseAgent]) -> None:
        """Register an agent class under a human-readable name."""
        if not issubclass(agent_cls, BaseAgent):
            msg = f"{agent_cls.__name__} must subclass BaseAgent"
            raise TypeError(msg)
        self._agents[name] = agent_cls

    def get(self, name: str) -> type[BaseAgent]:
        """Retrieve an agent class by name."""
        if name not in self._agents:
            msg = f"Unknown agent: {name!r}. Available: {list(self._agents)}"
            raise KeyError(msg)
        return self._agents[name]

    def list_agents(self) -> list[str]:
        """Return the names of all registered agents."""
        return list(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents
"""
core-agent — Agent orchestration engine using LangChain & LangGraph.

Provides:
- Base agent abstraction and registry
- State graph orchestration (LangGraph)
- Tool execution framework
- Agent communication patterns
"""

from core_agent.base import AgentConfig, AgentResult, BaseAgent
from core_agent.graph import (
    AgentGraph,
    AgentState,
    OrchestratorState,
    build_agent_graph,
    build_orchestrator_graph,
)
from core_agent.registry import AgentRegistry
from core_agent.settings import OrchestratorSettings, settings
from core_agent.tool_adapter import build_langchain_tools, tool_to_langchain

__all__ = [
    "AgentState",
    "OrchestratorState",
    "AgentGraph",
    "build_agent_graph",
    "build_orchestrator_graph",
    "BaseAgent",
    "AgentConfig",
    "AgentResult",
    "AgentRegistry",
    "OrchestratorSettings",
    "settings",
    "tool_to_langchain",
    "build_langchain_tools",
]

__version__ = "0.1.0"

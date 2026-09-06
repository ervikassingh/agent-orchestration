"""
core-agent — Agent orchestration engine using LangChain & LangGraph.

Provides:
- Base agent abstraction and registry
- State graph orchestration (LangGraph)
- Tool execution framework
- Agent communication patterns
"""

from core_agent.graph import AgentState, AgentGraph, build_agent_graph
from core_agent.base import BaseAgent, AgentConfig, AgentResult
from core_agent.registry import AgentRegistry

__all__ = [
    "AgentState",
    "AgentGraph",
    "build_agent_graph",
    "BaseAgent",
    "AgentConfig",
    "AgentResult",
    "AgentRegistry",
]

__version__ = "0.1.0"
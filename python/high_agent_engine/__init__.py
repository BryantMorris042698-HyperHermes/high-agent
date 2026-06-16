"""high_agent_engine — Graph_x_0x0 Python Mirror.

Exports all public types: graph engine, regime system, metrics,
skills, repos, LLM client, neural chat agent, and swarm orchestrator.
"""

from high_agent_engine.graph import (
    DirectedGraph,
    GraphSnapshot,
    Node,
    Edge,
    SegmentedRegimeDetector,
)
from high_agent_engine.regime import (
    Regime,
    RegimeCoeffs,
    RegimeTransition,
    HYSTERESIS_MARGIN,
)
from high_agent_engine.engine import RegimeEngine, Metrics
from high_agent_engine.metrics import (
    History,
    Trend,
    PhiColor,
    RegimeMetrics,
)
from high_agent_engine.skills import Skill, SkillManager
from high_agent_engine.repos import Repo, RepoManager
from high_agent_engine.ollama import OllamaClient
from high_agent_engine.crawler import CodebaseCrawler
from high_agent_engine.daemon import Daemon

# ── LLM & Neural Chat (lazy imports — avoid hard deps) ────────────────────────

def _llm_available() -> bool:
    try:
        import requests  # noqa: F401
        return True
    except ImportError:
        return False


def get_llm_client(**kwargs):
    """Lazily import and return LLMClient. Requires 'requests' package."""
    if not _llm_available():
        raise RuntimeError(
            "LLM support requires 'requests'. Install with:\n"
            "  pip install high-agent[ollama]\n"
            "  # or\n"
            "  pip install requests"
        )
    from high_agent_engine.llm import LLMClient
    return LLMClient(**kwargs)


def get_neural_agent(**kwargs):
    """Lazily import and return NeuralAgent."""
    if not _llm_available():
        raise RuntimeError(
            "Neural chat requires 'requests'. Install with:\n"
            "  pip install high-agent[ollama]"
        )
    from high_agent_engine.chat import NeuralAgent
    return NeuralAgent(**kwargs)


def get_agent_swarm(engine=None, llm_client=None):
    """Lazily import and return Swarm."""
    if not _llm_available():
        raise RuntimeError(
            "Agent swarm requires 'requests'. Install with:\n"
            "  pip install high-agent[ollama]"
        )
    from high_agent_engine.agent import Swarm
    from high_agent_engine.engine import RegimeEngine
    return Swarm(engine or RegimeEngine(), llm_client)


__version__ = "0.2.0"
__all__ = [
    # Graph core
    "DirectedGraph",
    "GraphSnapshot",
    "Node",
    "Edge",
    "SegmentedRegimeDetector",
    # Regime system
    "Regime",
    "RegimeCoeffs",
    "RegimeTransition",
    "HYSTERESIS_MARGIN",
    # Engine
    "RegimeEngine",
    # Metrics
    "Metrics",
    "History",
    "Trend",
    "PhiColor",
    "RegimeMetrics",
    # Skills
    "Skill",
    "SkillManager",
    # Repos
    "Repo",
    "RepoManager",
    # LLM/Ollama
    "OllamaClient",
    # Crawler & Daemon
    "CodebaseCrawler",
    "Daemon",
    # Lazy-loaded (require 'requests')
    "get_llm_client",
    "get_neural_agent",
    "get_agent_swarm",
]
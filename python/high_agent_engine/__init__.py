"""high_agent_engine — Python mirror of Graph_x_0x0 Rust core.

Exports all public types from the graph engine, regime system,
metrics, skills, repos, and supporting utilities.
"""

from high_agent_engine.graph import (
    DirectedGraph,
    GraphSnapshot,
    Node,
    Edge,
)
from high_agent_engine.regime import (
    Regime,
    RegimeCoeffs,
    RegimeTransition,
    HYSTERESIS_MARGIN,
)
from high_agent_engine.engine import RegimeEngine
from high_agent_engine.ollama import OllamaClient
from high_agent_engine.crawler import CodebaseCrawler
from high_agent_engine.daemon import Daemon
from high_agent_engine.metrics import (
    Metrics,
    History,
    Trend,
    PhiColor,
    RegimeMetrics,
)
from high_agent_engine.skills import Skill, SkillManager
from high_agent_engine.repos import Repo, RepoManager

__version__ = "0.1.0"
__all__ = [
    # Graph core
    "DirectedGraph",
    "GraphSnapshot",
    "Node",
    "Edge",
    # Regime system
    "Regime",
    "RegimeCoeffs",
    "RegimeTransition",
    "HYSTERESIS_MARGIN",
    # Engine
    "RegimeEngine",
    # Ollama
    "OllamaClient",
    # Crawler & Daemon
    "CodebaseCrawler",
    "Daemon",
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
]

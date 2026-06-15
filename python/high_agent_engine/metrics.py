"""Metrics — aggregates from graph snapshots for TUI display."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from high_agent_engine.graph import GraphSnapshot
from high_agent_engine.regime import Regime, RegimeTransition


class Trend(Enum):
    """Trend direction for a metric."""
    UP = "+"
    DOWN = "-"
    STABLE = "~"


@dataclass
class PhiColor:
    """Color classification for Φ(G) value."""
    GREEN = "green"   # > 0
    YELLOW = "yellow" # -2 < x <= 0
    RED = "red"       # <= -2

    @classmethod
    def for_phi(cls, phi: float) -> str:
        if phi > 0.0:
            return cls.GREEN.value
        elif phi > -2.0:
            return cls.YELLOW.value
        else:
            return cls.RED.value

    @classmethod
    def for_display(cls, phi: float) -> str:
        c = cls.for_phi(phi)
        if c == cls.GREEN.value:
            return f"\033[92m{phi:+.4f}\033[0m"
        elif c == cls.YELLOW.value:
            return f"\033[93m{phi:+.4f}\033[0m"
        else:
            return f"\033[91m{phi:+.4f}\033[0m"


@dataclass
class RegimeMetrics:
    """Per-regime metrics summary."""
    regime: Regime
    phi: float
    q_contribution: float
    coupling_contribution: float
    complexity_contribution: float

    def as_dict(self) -> dict:
        return {
            "regime": self.regime.name,
            "phi": self.phi,
            "q_contribution": self.q_contribution,
            "coupling_contribution": self.coupling_contribution,
            "complexity_contribution": self.complexity_contribution,
        }


@dataclass
class Metrics:
    """
    Aggregated metrics for TUI display.
    Produced from a GraphSnapshot + regime context.
    """
    phi: float
    q: float                    # Newman-Girvan modularity
    coupling: float             # Č(G) mean inter-module coupling
    mean_cyclomatic: float     # mean(V)
    mean_quality: float        # mean code quality
    n_nodes: int
    n_edges: int
    regime: Regime
    deviation_detected: bool = False
    deviation_direction: Optional[str] = None
    phi_color: str = "green"

    @classmethod
    def from_snapshot(cls, snap: GraphSnapshot, regime: Regime,
                      deviation_detected: bool = False,
                      deviation_direction: Optional[str] = None) -> "Metrics":
        return cls(
            phi=snap.phi,
            q=snap.q,
            coupling=snap.coupling,
            mean_cyclomatic=snap.mean_cyclomatic,
            mean_quality=snap.mean_quality,
            n_nodes=snap.n_nodes,
            n_edges=snap.n_edges,
            regime=regime,
            deviation_detected=deviation_detected,
            deviation_direction=deviation_direction,
            phi_color=PhiColor.for_phi(snap.phi),
        )

    def as_dict(self) -> dict:
        return {
            "phi": self.phi,
            "q": self.q,
            "coupling": self.coupling,
            "mean_cyclomatic": self.mean_cyclomatic,
            "mean_quality": self.mean_quality,
            "n_nodes": self.n_nodes,
            "n_edges": self.n_edges,
            "regime": self.regime.name,
            "deviation_detected": self.deviation_detected,
            "deviation_direction": self.deviation_direction,
            "phi_color": self.phi_color,
        }

    def phi_display(self) -> str:
        return PhiColor.for_display(self.phi)

    def q_trend(self, prev: Optional["Metrics"]) -> Trend:
        if prev is None:
            return Trend.STABLE
        if self.q > prev.q + 0.01:
            return Trend.UP
        elif self.q < prev.q - 0.01:
            return Trend.DOWN
        return Trend.STABLE

    def coupling_trend(self, prev: Optional["Metrics"]) -> Trend:
        if prev is None:
            return Trend.STABLE
        if self.coupling < prev.coupling - 0.01:
            return Trend.UP   # Lower coupling = better = up
        elif self.coupling > prev.coupling + 0.01:
            return Trend.DOWN
        return Trend.STABLE

    def complexity_trend(self, prev: Optional["Metrics"]) -> Trend:
        if prev is None:
            return Trend.STABLE
        if self.mean_cyclomatic < prev.mean_cyclomatic - 0.1:
            return Trend.UP   # Lower complexity = better = up
        elif self.mean_cyclomatic > prev.mean_cyclomatic + 0.1:
            return Trend.DOWN
        return Trend.STABLE


@dataclass 
class History:
    """History of snapshots for the History tab."""
    entries: List[Metrics] = field(default_factory=list)
    max_entries: int = 100

    def push(self, m: Metrics) -> None:
        self.entries.insert(0, m)
        if len(self.entries) > self.max_entries:
            self.entries.pop()

    def to_display_list(self) -> List[dict]:
        return [m.as_dict() for m in self.entries]

    def __len__(self) -> int:
        return len(self.entries)

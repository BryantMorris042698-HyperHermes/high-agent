"""RegimeEngine — mirrors Rust core.rs."""

from __future__ import annotations
import json
import time
from .graph import DirectedGraph, GraphSnapshot, Node, Edge
from .regime import Regime, RegimeTransition, HYSTERESIS_MARGIN

class Metrics:
    def __init__(self, snapshot: GraphSnapshot, regime: str):
        self.phi = snapshot.phi
        self.q = snapshot.q
        self.coupling = snapshot.coupling
        self.mean_v = snapshot.mean_v
        self.max_v = snapshot.max_v
        self.quality = snapshot.quality
        self.n_nodes = snapshot.n_nodes
        self.n_edges = snapshot.n_edges
        self.n_modules = snapshot.n_modules
        self.regime = regime
        self.timestamp = f"{time.time():.9f}"

    def to_json(self) -> str:
        return json.dumps({
            "phi": self.phi, "q": self.q, "coupling": self.coupling,
            "mean_v": self.mean_v, "max_v": self.max_v, "quality": self.quality,
            "n_nodes": self.n_nodes, "n_edges": self.n_edges, "n_modules": self.n_modules,
            "regime": self.regime, "regime_str": self.regime,
            "phi_formatted": f"{self.phi:+.4f}",
            "phi_color": "green" if self.phi > 0 else "yellow" if self.phi > -2 else "red",
            "phi_trend": "stable", "timestamp": self.timestamp,
        }, indent=2)

    def write_state(self, path: str = "~/.high-agent/state.json"):
        path = path.replace("~", __import__("os").getenv("HOME", "."))
        import os; os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())


class RegimeEngine:
    def __init__(self):
        self.graph = DirectedGraph()
        self.current_regime = Regime.default()
        self.detector = None
        self.metrics = None
        self.history = []
        self.transitions = []
        self.state_file = "~/.high-agent/state.json"

    def seed_graph(self) -> None:
        self.graph.seed()
        self.update_metrics()

    def update_metrics(self) -> None:
        snapshot = self.graph.snapshot_full(self.current_regime)
        self.metrics = Metrics(snapshot, self.current_regime)
        self.history.append(vars(self.metrics))

    def sweep_regimes(self) -> list:
        return [(r, self.graph.phi_regime(r)) for r in Regime.all()]

    def best_regime(self) -> tuple:
        results = self.sweep_regimes()
        return max(results, key=lambda x: x[1])

    def switch_regime(self, regime: str) -> str:
        old = self.current_regime
        self.current_regime = regime
        self.update_metrics()
        t = RegimeTransition(old, regime, "Manual switch", self.graph.phi_regime(old), self.metrics.phi)
        self.transitions.append(t)
        return old

    def detect_and_evaluate(self) -> tuple:
        if self.detector is None:
            from .graph import SegmentedRegimeDetector
            self.detector = SegmentedRegimeDetector(10, 2.0)

        snapshot = self.graph.snapshot_full(self.current_regime)
        alert = self.detector.feed(snapshot)

        best_r, best_phi = self.best_regime()
        current_phi = self.graph.phi_regime(self.current_regime)

        transition = None
        if best_r != self.current_regime and (best_phi - current_phi) > HYSTERESIS_MARGIN:
            transition = RegimeTransition(
                self.current_regime, best_r,
                f"Φ improved by {best_phi - current_phi:.4f} > hysteresis {HYSTERESIS_MARGIN}",
                current_phi, best_phi
            )
            self.current_regime = best_r
            self.transitions.append(transition)

        self.update_metrics()
        return transition, alert

    def process_task(self, task: str) -> None:
        if task == "refactor":
            violations = self.graph.coupling_violations()
            if violations:
                self.graph.remove_edge(violations[0].from_, violations[0].to)
        elif task == "feature":
            nid = f"fn_feature_{self.graph.n_nodes()}"
            n = Node(nid, "features", "features/mod.py")
            n.cyclomatic = 3.0
            n.quality = 0.7
            self.graph.add_node(n)
        elif task == "test":
            for node in self.graph.nodes.values():
                node.quality = min(1.0, node.quality + 0.05)
        elif task == "complexity":
            for node in self.graph.nodes.values():
                node.cyclomatic = max(1.0, node.cyclomatic * 0.9)
        self.update_metrics()

    def simulate_deviation(self) -> None:
        if self.current_regime == "simple":
            for n in self.graph.nodes.values():
                n.quality = min(1.0, n.quality + 0.05)
        elif self.current_regime == "advanced":
            violations = self.graph.coupling_violations()
            if len(violations) > 1:
                self.graph.remove_edge(violations[1].from_, violations[1].to)
        else:
            for n in self.graph.nodes.values():
                n.cyclomatic = max(1.0, n.cyclomatic * 0.95)
        self.update_metrics()
        self.detect_and_evaluate()

    def theory_explain(self) -> str:
        coeffs = Regime.coeffs(self.current_regime)
        s = self.graph.snapshot_full(self.current_regime)
        return f"""═══════════════════════════════════════════════════════════
              THEORY MODE — Mathematical Foundation
═══════════════════════════════════════════════════════════
OBJECTIVE:  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
CURRENT REGIME: {self.current_regime} ({Regime.description(self.current_regime)})
COEFFICIENTS: α={coeffs.alpha}, β={coeffs.beta}, γ={coeffs.gamma}
LIVE METRICS:
  Φ(G)  = {s.phi:+.4f}
  Q(G)  = {s.q:.4f}  (modularity)
  Č(G)  = {s.coupling:.4f}  (coupling)
  mean(V) = {s.mean_v:.2f}  (cyclomatic)
COMPONENT BREAKDOWN:
  α·Q(G)  = {coeffs.alpha * s.q:+.4f}
  β·Č(G)  = {coeffs.beta * s.coupling:+.4f}
  γ·mean(V) = {coeffs.gamma * s.mean_v:+.4f}
  ─────────────────────────────────
  Φ(G)  = {s.phi:+.4f}
═══════════════════════════════════════════════════════════"""

    def load_from_json(self, json_str: str) -> None:
        self.graph = DirectedGraph.from_json(json_str)
        self.update_metrics()

    def write_state(self) -> None:
        if self.metrics:
            self.metrics.write_state(self.state_file)

    def ai_analyze(self, client) -> str:
        prompt = f"""Analyze this codebase graph for architectural issues:
Nodes: {self.metrics.n_nodes} functions across {self.metrics.n_modules} modules
Edges: {self.metrics.n_edges} dependencies
Metrics: Φ={self.metrics.phi:.4f}, Q={self.metrics.q:.4f}, Č={self.metrics.coupling:.4f}, V={self.metrics.mean_v:.2f}
Regime: {self.current_regime}
Hot spots: {[n.id for n in self.graph.hot_spots(5.0)]}
Coupling violations: {len(self.graph.coupling_violations())} cross-module edges
Provide specific refactoring suggestions."""
        return client.generate(prompt) if client else prompt
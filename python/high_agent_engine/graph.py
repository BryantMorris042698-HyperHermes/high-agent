"""Graph core — mirrors the Rust graph.rs for Python environments (Termux, rapid prototyping)."""

from __future__ import annotations
import json
from collections import defaultdict
from typing import Optional, Dict, List, Tuple, Set

class Node:
    def __init__(self, id: str, module: str, file: str):
        self.id = id
        self.module = module
        self.file = file
        self.cyclomatic: float = 1.0
        self.quality: float = 0.5
        self.lines: int = 0
        self.doc: Optional[str] = None

    def __repr__(self):
        return f"Node({self.id}, module={self.module}, V={self.cyclomatic:.1f}, q={self.quality:.2f})"

class Edge:
    def __init__(self, frm: str, to: str):
        self.from_ = frm
        self.to = to
        self.weight: float = 1.0
        self.edge_type: str = "call"

    def __repr__(self):
        return f"Edge({self.from_} → {self.to}, w={self.weight:.1f})"

class DirectedGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def add_node(self, node: Node) -> Node:
        if node.id not in self.nodes:
            self.nodes[node.id] = node
        return self.nodes[node.id]

    def add_edge(self, edge: Edge) -> None:
        if edge.from_ in self.nodes and edge.to in self.nodes:
            self.edges.append(edge)

    def remove_node(self, id: str) -> Optional[Node]:
        self.edges = [e for e in self.edges if e.from_ != id and e.to != id]
        return self.nodes.pop(id, None)

    def remove_edge(self, frm: str, to: str) -> None:
        self.edges = [e for e in self.edges if not (e.from_ == frm and e.to == to)]

    def n_nodes(self) -> int: return len(self.nodes)
    def n_edges(self) -> int: return len(self.edges)

    def modules(self) -> Set[str]:
        return {n.module for n in self.nodes.values()}

    def nodes_in_module(self, module: str) -> List[Node]:
        return [n for n in self.nodes.values() if n.module == module]

    def _get_degree(self, node_id: str) -> Tuple[float, float]:
        out_w = sum(e.weight for e in self.edges if e.from_ == node_id)
        in_w = sum(e.weight for e in self.edges if e.to == node_id)
        return out_w, in_w

    def modularity(self) -> float:
        n = self.n_nodes()
        if n < 2: return 1.0
        mods = self.modules()
        m = len(self.edges)
        if m < 1: return 1.0

        q = 0.0
        for mod in mods:
            nodes_in = self.nodes_in_module(mod)
            k_c = sum(sum(e.weight for e in self.edges if e.from_ == n.id) +
                      sum(e.weight for e in self.edges if e.to == n.id) for n in nodes_in)
            l_c = sum(e.weight for e in self.edges
                      if self.nodes.get(e.from_) and self.nodes.get(e.to)
                      and self.nodes[e.from_].module == mod and self.nodes[e.to].module == mod)
            q += (l_c / m) - ((k_c / (2 * m)) ** 2)
        return max(-1.0, min(1.0, q))

    def mean_coupling(self) -> float:
        n = self.n_nodes()
        if n < 1: return 0.0
        cross = sum(e.weight for e in self.edges
                    if self.nodes.get(e.from_) and self.nodes.get(e.to)
                    and self.nodes[e.from_].module != self.nodes[e.to].module)
        return cross / n

    def total_cyclomatic(self) -> float:
        return sum(n.cyclomatic for n in self.nodes.values())

    def mean_cyclomatic(self) -> float:
        n = self.n_nodes()
        return self.total_cyclomatic() / n if n > 0 else 0.0

    def max_cyclomatic(self) -> float:
        return max((n.cyclomatic for n in self.nodes.values()), default=0.0)

    def mean_quality(self) -> float:
        n = self.n_nodes()
        return sum(n.quality for n in self.nodes.values()) / n if n > 0 else 0.0

    def multi_objective(self, alpha: float, beta: float, gamma: float) -> float:
        q = self.modularity()
        c = self.mean_coupling()
        v = self.mean_cyclomatic()
        return alpha * q - beta * c - gamma * v

    def phi_regime(self, regime: str) -> float:
        coeffs = {"simple": (0.8, 0.9, 0.2), "advanced": (1.2, 0.5, 0.3), "hybrid": (1.0, 0.6, 0.4)}
        a, b, g = coeffs.get(regime.lower(), (1.0, 0.6, 0.4))
        return self.multi_objective(a, b, g)

    def snapshot(self) -> "GraphSnapshot":
        return GraphSnapshot(
            phi=0.0,
            q=self.modularity(),
            coupling=self.mean_coupling(),
            mean_v=self.mean_cyclomatic(),
            max_v=self.max_cyclomatic(),
            quality=self.mean_quality(),
            n_nodes=self.n_nodes(),
            n_edges=self.n_edges(),
            n_modules=len(self.modules()),
        )

    def snapshot_full(self, regime: str) -> "GraphSnapshot":
        s = self.snapshot()
        s.phi = self.phi_regime(regime)
        return s

    def hot_spots(self, threshold: float) -> List[Node]:
        return [n for n in self.nodes.values() if n.cyclomatic > threshold]

    def coupling_violations(self) -> List[Edge]:
        return [e for e in self.edges
                if self.nodes.get(e.from_) and self.nodes.get(e.to)
                and self.nodes[e.from_].module != self.nodes[e.to].module]

    def node_importance(self, iterations: int = 20) -> Dict[str, float]:
        n = self.n_nodes()
        if n == 0: return {}
        node_ids = list(self.nodes.keys())
        pr = {id_: 1.0 / n for id_ in node_ids}
        damping = 0.85

        for _ in range(iterations):
            new_pr = {}
            for id_ in node_ids:
                incoming = sum(pr.get(e.from_, 0.0) * e.weight
                               for e in self.edges if e.to == id_)
                out_sum = sum(e.weight for e in self.edges if e.from_ == id_)
                new_pr[id_] = (1 - damping) / n + damping * incoming / max(out_sum, 1.0)
            pr = new_pr
        return pr

    def to_json(self) -> str:
        data = {
            "nodes": [{"id": n.id, "module": n.module, "file": n.file,
                       "cyclomatic": n.cyclomatic, "quality": n.quality, "lines": n.lines}
                      for n in self.nodes.values()],
            "edges": [{"from": e.from_, "to": e.to, "weight": e.weight, "type": e.edge_type}
                      for e in self.edges],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, s: str) -> "DirectedGraph":
        data = json.loads(s)
        g = cls()
        for nd in data.get("nodes", []):
            n = Node(nd["id"], nd["module"], nd["file"])
            n.cyclomatic = nd.get("cyclomatic", 1.0)
            n.quality = nd.get("quality", 0.5)
            n.lines = nd.get("lines", 0)
            g.add_node(n)
        for ed in data.get("edges", []):
            e = Edge(ed["from"], ed["to"])
            e.weight = ed.get("weight", 1.0)
            e.edge_type = ed.get("type", "call")
            g.add_edge(e)
        return g

    def seed(self) -> None:
        modules = [
            ("core", "src/core.py"), ("cli", "src/cli.py"), ("skills", "src/skills.py"),
            ("graph", "src/graph.py"), ("orchestrator", "src/orchestrator.py"),
            ("ollama", "src/ollama.py"), ("build", "src/build.py"),
        ]
        import time
        for module, file in modules:
            n = Node(f"fn_{module}", module, file)
            n.cyclomatic = 2.0 + (time.time() % 4.0)
            n.quality = 0.6 + (time.time() % 0.35)
            n.lines = 50 + int(time.time() % 200)
            self.add_node(n)

        edges = [
            ("fn_core", "fn_graph", 1.0), ("fn_orchestrator", "fn_core", 1.0),
            ("fn_orchestrator", "fn_graph", 0.8), ("fn_skills", "fn_core", 0.7),
            ("fn_cli", "fn_core", 1.0), ("fn_ollama", "fn_core", 0.9),
            ("fn_build", "fn_graph", 0.6), ("fn_cli", "fn_skills", 0.5),
        ]
        for frm, to, w in edges:
            e = Edge(frm, to)
            e.weight = w
            self.add_edge(e)


class GraphSnapshot:
    def __init__(self, phi: float, q: float, coupling: float, mean_v: float,
                 max_v: float, quality: float, n_nodes: int, n_edges: int, n_modules: int):
        self.phi = phi
        self.q = q
        self.coupling = coupling
        self.mean_v = mean_v
        self.max_v = max_v
        self.quality = quality
        self.n_nodes = n_nodes
        self.n_edges = n_edges
        self.n_modules = n_modules

    def __repr__(self):
        return f"Snapshot(Φ={self.phi:+.4f}, Q={self.q:.4f}, Č={self.coupling:.4f}, V={self.mean_v:.2f})"


class SegmentedRegimeDetector:
    def __init__(self, window_size: int = 10, threshold: float = 2.0):
        self.window: List[GraphSnapshot] = []
        self.window_size = window_size
        self.threshold = threshold

    def feed(self, snapshot: GraphSnapshot) -> Optional[dict]:
        if len(self.window) >= self.window_size:
            self.window.pop(0)
        self.window.append(snapshot)

        if len(self.window) < 3:
            return None

        n = len(self.window)
        mean_q = sum(s.q for s in self.window) / n
        mean_c = sum(s.coupling for s in self.window) / n
        mean_v = sum(s.mean_v for s in self.window) / n

        sigma_q = max((sum((s.q - mean_q) ** 2 for s in self.window) / n) ** 0.5, 1e-6)
        sigma_c = max((sum((s.coupling - mean_c) ** 2 for s in self.window) / n) ** 0.5, 1e-6)
        sigma_v = max((sum((s.mean_v - mean_v) ** 2 for s in self.window) / n) ** 0.5, 1e-6)

        z_q = (snapshot.q - mean_q) / sigma_q
        z_c = (snapshot.coupling - mean_c) / sigma_c
        z_v = (snapshot.mean_v - mean_v) / sigma_v

        any_dev = abs(z_q) > self.threshold or abs(z_c) > self.threshold or abs(z_v) > self.threshold
        if not any_dev:
            return None

        improving = z_q > self.threshold or z_c < -self.threshold or z_v < -self.threshold
        degrading = z_q < -self.threshold or z_c > self.threshold or z_v > self.threshold

        if improving and not degrading:
            direction = "improving"
        elif degrading and not improving:
            direction = "degrading"
        else:
            direction = "mixed"

        return {"direction": direction, "z_q": z_q, "z_coupling": z_c, "z_v": z_v}

    def clear(self):
        self.window.clear()
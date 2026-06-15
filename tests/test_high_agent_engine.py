"""Tests for high_agent_engine Python package."""

import sys
import json
sys.path.insert(0, 'python')

from high_agent_engine import (
    DirectedGraph, GraphSnapshot, Node, Edge, SegmentedRegimeDetector,
    Regime, RegimeTransition, RegimeCoeffs, HYSTERESIS_MARGIN,
    RegimeEngine, Metrics,
    OllamaClient, Daemon, CodebaseCrawler
)

def test_node_creation():
    n = Node("fn_test", "test_module", "test.py")
    assert n.id == "fn_test"
    assert n.module == "test_module"
    assert n.cyclomatic == 1.0
    assert n.quality == 0.5

def test_edge_creation():
    e = Edge("fn_a", "fn_b")
    assert e.from_ == "fn_a"
    assert e.to == "fn_b"
    assert e.weight == 1.0

def test_graph_basics():
    g = DirectedGraph()
    n1 = Node("fn_a", "mod1", "a.py")
    n2 = Node("fn_b", "mod1", "b.py")
    g.add_node(n1)
    g.add_node(n2)
    assert g.n_nodes() == 2
    g.add_edge(Edge("fn_a", "fn_b"))
    assert g.n_edges() == 1

def test_graph_modularity():
    g = DirectedGraph()
    for i in range(5):
        g.add_node(Node(f"fn_{i}", "module1", "mod1.py"))
    for i in range(5, 10):
        g.add_node(Node(f"fn_{i}", "module2", "mod2.py"))
    # Same module edges
    for i in range(4):
        g.add_edge(Edge(f"fn_{i}", f"fn_{i+1}"))
    # Cross module edge
    g.add_edge(Edge("fn_0", "fn_5"))
    q = g.modularity()
    assert -1.0 <= q <= 1.0

def test_graph_snapshot():
    g = DirectedGraph()
    g.add_node(Node("fn_a", "m", "a.py"))
    s = g.snapshot()
    assert isinstance(s, GraphSnapshot)
    assert s.n_nodes == 1

def test_regime_defaults():
    assert Regime.default() == "hybrid"
    assert "simple" in Regime.all()
    assert "advanced" in Regime.all()
    assert "hybrid" in Regime.all()

def test_regime_coeffs():
    c = Regime.coeffs("simple")
    assert isinstance(c, RegimeCoeffs)
    assert c.alpha == 0.8

def test_regime_transition():
    t = RegimeTransition("simple", "advanced", "test", 0.1, 0.2)
    assert t.from_ == "simple"
    assert t.to == "advanced"
    assert t.improvement() == 0.1

def test_regime_engine_seed():
    engine = RegimeEngine()
    engine.seed_graph()
    assert engine.graph.n_nodes() == 7
    assert engine.graph.n_edges() == 8

def test_regime_engine_metrics():
    engine = RegimeEngine()
    engine.seed_graph()
    engine.update_metrics()
    assert isinstance(engine.metrics, Metrics)
    assert engine.metrics.n_nodes == 7

def test_regime_engine_sweep():
    engine = RegimeEngine()
    engine.seed_graph()
    results = engine.sweep_regimes()
    assert len(results) == 3
    regimes = [r for r, _ in results]
    assert "simple" in regimes
    assert "advanced" in regimes
    assert "hybrid" in regimes

def test_regime_engine_switch():
    engine = RegimeEngine()
    engine.seed_graph()
    old = engine.switch_regime("simple")
    assert old == "hybrid"
    assert engine.current_regime == "simple"

def test_regime_engine_process_task():
    engine = RegimeEngine()
    engine.seed_graph()
    initial_nodes = engine.graph.n_nodes()
    engine.process_task("feature")
    assert engine.graph.n_nodes() == initial_nodes + 1

def test_regime_engine_simulate():
    engine = RegimeEngine()
    engine.seed_graph()
    engine.simulate_deviation()
    assert len(engine.history) >= 1

def test_regime_engine_to_json():
    engine = RegimeEngine()
    engine.seed_graph()
    json_str = engine.graph.to_json()
    data = json.loads(json_str)
    assert "nodes" in data
    assert "edges" in data

def test_regime_engine_from_json():
    engine = RegimeEngine()
    engine.seed_graph()
    json_str = engine.graph.to_json()
    engine2 = RegimeEngine()
    engine2.load_from_json(json_str)
    assert engine2.graph.n_nodes() == engine.graph.n_nodes()

def test_detector():
    g = DirectedGraph()
    g.add_node(Node("fn_a", "m", "a.py"))
    s = g.snapshot()
    detector = SegmentedRegimeDetector(5, 2.0)
    result = detector.feed(s)
    assert result is None  # Not enough data yet

def test_crawler_init():
    crawler = CodebaseCrawler(".")
    assert crawler.root.name == "high-agent"
    assert crawler.graph is not None

def test_ollama_client_init():
    client = OllamaClient()
    assert "localhost" in client.base_url
    assert client.default_model == "llama3.2:3b"

def test_daemon_init():
    d = Daemon(5)
    assert d.interval == 5
    assert d.engine is not None
    assert d.running == True
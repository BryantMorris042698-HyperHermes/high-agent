#!/bin/bash
# Demo script — shows Graph_x_0x0 running through its modes
# Run: bash scripts/demo.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIGH_AGENT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Graph_x_0x0 Demo — Φ(G) in Action              ║"
echo "║  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)            ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check what's available
RUST_BUILT=false
PYTHON_BUILT=false

if [ -f "$HIGH_AGENT_ROOT/rust/target/release/high-agent-tui" ]; then
    RUST_BUILT=true
    echo "[✓] Rust TUI binary found"
elif [ -f "$HIGH_AGENT_ROOT/rust/target/debug/high-agent" ]; then
    RUST_BUILT=true
    echo "[✓] Rust core binary found (debug)"
else
    echo "[ ] Rust not built — run: bash scripts/install.sh rust-tui"
fi

if command -v python3 &>/dev/null; then
    PYTHON_BUILT=true
    echo "[✓] Python3 available"
fi

echo ""

# Demo 1: Show the seed graph
demo_seed_graph() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Demo 1: Seed Graph (7 nodes, 8 edges)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cd "$HIGH_AGENT_ROOT/python"
    python3 -c "
import sys; sys.path.insert(0, '.')
from high_agent_engine import DirectedGraph, RegimeEngine, Regime, RegimeCoeffs
from high_agent_engine.graph import Node, Edge

# Build seed graph
g = DirectedGraph()
g.add_node(Node('orchestrate', 'core', 4, 0.85))
g.add_node(Node('evaluate', 'core', 3, 0.90))
g.add_node(Node('detect', 'core', 5, 0.80))
g.add_node(Node('refactor', 'cli', 2, 0.88))
g.add_node(Node('build', 'cli', 3, 0.82))
g.add_node(Node('plan', 'skills', 4, 0.87))
g.add_node(Node('summarize', 'skills', 2, 0.91))

g.add_edge(Edge('orchestrate', 'evaluate', 1.0))
g.add_edge(Edge('orchestrate', 'detect', 0.8))
g.add_edge(Edge('evaluate', 'refactor', 0.7))
g.add_edge(Edge('detect', 'plan', 0.9))
g.add_edge(Edge('refactor', 'build', 1.0))
g.add_edge(Edge('plan', 'orchestrate', 0.6))
g.add_edge(Edge('build', 'summarize', 0.5))
g.add_edge(Edge('evaluate', 'plan', 0.7))

snap = g.snapshot()
print(f'  Nodes: {snap.n_nodes}, Edges: {snap.n_edges}')
print(f'  Q(G) modularity:  {snap.q:.4f}')
print(f'  Č(G) coupling:   {snap.coupling:.4f}')
print(f'  mean(V) cycl.:   {snap.mean_cyclomatic:.2f}')
print(f'  mean quality:    {snap.mean_quality:.4f}')

for regime in [Regime.Simple, Regime.Advanced, Regime.Hybrid]:
    coeffs = RegimeCoeffs.for_regime(regime)
    phi = g.multi_objective(snap, coeffs)
    print(f'  Φ(G) [{regime.name:8s}]: {phi:+.4f}')
" 2>/dev/null || echo "[!] Python engine not available"
    echo ""
}

# Demo 2: Regime switching
demo_regime_switch() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Demo 2: Regime Switching with Hysteresis"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cd "$HIGH_AGENT_ROOT/python"
    python3 -c "
import sys; sys.path.insert(0, '.')
from high_agent_engine import DirectedGraph, RegimeEngine, Regime, RegimeTransition
from high_agent_engine.graph import Node, Edge

engine = RegimeEngine.new()
engine.set_regime(Regime.Simple)

# Simulate some graph mutations
for i in range(5):
    node_id = f'fn_{i}'
    engine.graph.add_node(Node(node_id, 'module_a', 3.0 + i * 0.5, 0.85))
    if i > 0:
        engine.graph.add_edge(Edge(f'fn_{i-1}', node_id, 1.0))

# Detect and switch
result = engine.detect_and_evaluate()
print(f'  Regime: {result[\"regime\"].name}')
print(f'  Φ(G): {result[\"phi\"]:.4f}')
print(f'  Deviation detected: {result[\"deviation_detected\"]}')
if result.get('transition'):
    t = result['transition']
    print(f'  Transition: {t[\"from\"]} → {t[\"to\"]}')
    print(f'  ΔΦ(G): {t[\"phi_delta\"]:+.4f}')
" 2>/dev/null || echo "[!] Python engine not available"
    echo ""
}

# Demo 3: Self-improving loop simulation
demo_self_improve() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Demo 3: Self-Improving Loop (3 cycles)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cd "$HIGH_AGENT_ROOT/python"
    python3 -c "
import sys; sys.path.insert(0, '.')
from high_agent_engine import DirectedGraph, RegimeEngine, Regime
from high_agent_engine.graph import Node, Edge

engine = RegimeEngine.new()
baseline = engine.current_snapshot()

for cycle in range(1, 4):
    engine.simulate_graph_mutation()
    snap = engine.current_snapshot()
    delta_phi = snap.phi - baseline.phi
    verdict = '✓ IMPROVED' if delta_phi > 0 else '✗ DEGRADED'
    print(f'  Cycle {cycle}: Φ={snap.phi:+.4f} Δ={delta_phi:+.4f} {verdict}')
" 2>/dev/null || echo "[!] Python engine not available"
    echo ""
}

# Demo 4: Agent swarm roles
demo_swarm() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Demo 4: 8-Agent Swarm — Role Assignments"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat << 'EOF'
  ┌──────────────┐
  │ Orchestrator │  Φ(G) guardian, regime switcher
  ├──────────────┤
  │   Refactor   │  Graph restructuring, coupling reduction
  ├──────────────┤
  │   Quality    │  Code review, quality scoring
  ├──────────────┤
  │    Test      │  Coverage analysis, test generation
  ├──────────────┤
  │    Skill     │  Skill discovery, load, create, delete
  ├──────────────┤
  │    Repo      │  Repository cloning, sync, analysis
  ├──────────────┤
  │    Build     │  Multi-language build orchestration
  ├──────────────┤
  │   Planner    │  Task decomposition, sub-agent routing
  └──────────────┘
EOF
    echo ""
}

# Run demos
if [ "$PYTHON_BUILT" = true ]; then
    demo_seed_graph
    demo_regime_switch
    demo_self_improve
else
    echo "[!] Python not available — skipping engine demos"
fi
demo_swarm

echo "╔══════════════════════════════════════════════════╗"
echo "║  End of Demo                                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  TUI:     cargo run --features tui"
echo "  REPL:    cd python && python high-agent-repl.py"
echo "  Daemon:  cd python && python high_agent_engine/daemon.py"

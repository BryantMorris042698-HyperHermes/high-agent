#!/bin/bash
# Termux setup script for Graph_x_0x0
# Run on Android/Termux with no Rust compilation needed

set -euo pipefail

echo "╔══════════════════════════════════════════════════╗"
echo "║  Termux Setup for Graph_x_0x0                ║"
echo "║  Python-only — no Rust compilation needed    ║"
echo "╚══════════════════════════════════════════════════╝"

# Check we're in Termux
if ! command -v pkg &>/dev/null; then
    echo "[!] This script is designed for Termux on Android"
    echo "    On desktop Linux/macOS, use: bash scripts/install.sh"
    exit 1
fi

echo ""
echo "[+] Updating Termux packages..."
pkg update -y
pkg upgrade -y

echo "[+] Installing Python..."
pkg install python python-dev -y

echo "[+] Installing pip..."
pkg install pip -y

echo "[+] Setting up the project..."
cd ~/../home 2>/dev/null || cd ~
git clone https://github.com/Graph_x_0x0/high-agent.git
cd high-agent

echo "[+] Installing Python engine..."
cd python
pip install -e .

echo "[+] Verifying installation..."
python -c "
from high_agent_engine import DirectedGraph, RegimeEngine, Regime
print('✓ Engine loaded')
g = DirectedGraph()
snap = g.snapshot()
print(f'✓ Graph ready: {snap.n_nodes} nodes, {snap.n_edges} edges')
print(f'✓ Φ(G) = {snap.phi:+.4f}')
"

echo "[+] Creating helper scripts..."
cat > ~/.shortcuts/tasks/high-agent-repl << 'EOF'
cd ~/high-agent/python
python high-agent-repl.py
EOF

cat > ~/.shortcuts/tasks/high-agent-status << 'EOF'
cd ~/high-agent/python
python -c "
from high_agent_engine import RegimeEngine, Regime
e = RegimeEngine.new()
snap = e.current_snapshot()
print(f'Φ(G)={snap.phi:+.4f} [{snap.regime.name}] Q={snap.q:.3f} Č={snap.coupling:.3f} V={snap.mean_cyclomatic:.1f}')
"
EOF

mkdir -p ~/.termux/ shortcuts/tasks 2>/dev/null
mkdir -p ~/.high-agent ~/.high-agent/skills ~/.high-agent/repos ~/.high-agent/state

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Termux Setup Complete!                       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Usage:"
echo "  REPL:    cd ~/high-agent/python && python high-agent-repl.py"
echo "  Quick:   python -c \"from high_agent_engine import RegimeEngine; print(RegimeEngine.new().current_snapshot())\""
echo "  Daemon:  cd ~/high-agent/python && python high_agent_engine/daemon.py"
echo ""
echo "Create Termux shortcuts in ~/.shortcuts/tasks/ for one-tap access."

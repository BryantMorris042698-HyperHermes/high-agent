#!/bin/bash
# Termux setup script for Agent Storm-Swarm (high-agent)
# Python-only — no Rust compilation needed. Runs on Android/Termux.

set -euo pipefail

REPO_URL="https://github.com/BryantMorris042698-HyperHermes/high-agent.git"
BRANCH="claude/agent-storm-swarm-overview-7cmp0g"
DEST="$HOME/high-agent"

echo "=================================================="
echo "  Termux Setup for Agent Storm-Swarm"
echo "  Python-only — no Rust compilation needed"
echo "=================================================="

# Check we're in Termux
if ! command -v pkg &>/dev/null; then
    echo "[!] This script is designed for Termux on Android."
    echo "    On desktop Linux/macOS, use: bash scripts/install.sh"
    exit 1
fi

echo ""
echo "[+] Updating Termux packages..."
pkg update -y
pkg upgrade -y

echo "[+] Installing Python and git..."
pkg install -y python git

echo "[+] Fetching the project into $DEST ..."
if [ -d "$DEST/.git" ]; then
    echo "    Repo already exists — updating."
    git -C "$DEST" fetch origin "$BRANCH"
    git -C "$DEST" checkout "$BRANCH"
    git -C "$DEST" pull origin "$BRANCH"
else
    git clone --branch "$BRANCH" "$REPO_URL" "$DEST"
fi
cd "$DEST"

echo "[+] Installing the Python engine..."
pip install -e python/

echo "[+] Verifying installation..."
python -c "
from high_agent_engine import RegimeEngine
e = RegimeEngine()
e.seed_graph()
m = e.metrics
print('  Engine loaded OK')
print(f'  Graph: {m.n_nodes} nodes, {m.n_edges} edges')
print(f'  Phi(G) = {m.phi:+.4f}  [{e.current_regime}]')
"

echo "[+] Creating one-tap Termux shortcuts..."
mkdir -p "$HOME/.shortcuts/tasks"
mkdir -p "$HOME/.high-agent/skills" "$HOME/.high-agent/repos" "$HOME/.high-agent/state"

cat > "$HOME/.shortcuts/tasks/high-agent-repl" << EOF
cd $DEST && python -m high_agent_engine
EOF
chmod +x "$HOME/.shortcuts/tasks/high-agent-repl"

cat > "$HOME/.shortcuts/tasks/high-agent-status" << EOF
cd $DEST && python -c "
from high_agent_engine import RegimeEngine
e = RegimeEngine(); e.seed_graph(); m = e.metrics
print(f'Phi(G)={m.phi:+.4f} [{e.current_regime}] Q={m.q:.3f} C={m.coupling:.3f} V={m.mean_v:.1f}')
"
EOF
chmod +x "$HOME/.shortcuts/tasks/high-agent-status"

echo ""
echo "=================================================="
echo "  Termux Setup Complete!"
echo "=================================================="
echo ""
echo "Usage:"
echo "  REPL:    cd $DEST && python -m high_agent_engine"
echo "  Metrics: python -m high_agent_engine metrics"
echo "  Sweep:   python -m high_agent_engine sweep"
echo "  Theory:  python -m high_agent_engine theory"
echo ""
echo "Or use the Termux:Widget app for one-tap access to:"
echo "  high-agent-repl, high-agent-status"

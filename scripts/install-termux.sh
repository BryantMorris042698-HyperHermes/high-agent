#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  HIGH-AGENTS  ─  Termux Installer
#
#  Quick one-liner (no git needed):
#    pkg install python curl -y && \
#    curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/high-agents \
#         -o $PREFIX/bin/high-agents && chmod +x $PREFIX/bin/high-agents && high-agents
#
#  Or run this full script after cloning:
#    bash scripts/install-termux.sh
#
#  After install, launch with:  high-agents
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BIN_TARGET="${PREFIX:-/usr}/bin/high-agents"

banner() {
cat << 'EOF'
╔══════════════════════════════════════════════════════╗
║   HIGH-AGENTS  ─  Termux Installer                  ║
║   Codebase Analysis Engine · Storm Swarm AIOS        ║
╚══════════════════════════════════════════════════════╝
EOF
}

log()  { echo "[+] $*"; }
warn() { echo "[!] $*"; }

banner
echo ""

# ── 1. check Termux ────────────────────────────────────────────
if ! command -v pkg &>/dev/null; then
    warn "pkg not found — this script is designed for Termux on Android."
    warn "On desktop Linux / macOS use:  bash scripts/install.sh"
    exit 1
fi

# ── 2. update & install Python ─────────────────────────────────
log "Updating Termux packages…"
pkg update -y -q
pkg upgrade -y -q

log "Installing Python…"
pkg install python -y -q

# ── 3. make the TUI script executable ──────────────────────────
log "Making high-agents executable…"
chmod +x "$REPO_DIR/high-agents"

# ── 4. symlink / copy to PATH ──────────────────────────────────
log "Installing to $BIN_TARGET…"
ln -sf "$REPO_DIR/high-agents" "$BIN_TARGET"

# ── 5. install Python engine (optional but enables live metrics)
if [ -f "$REPO_DIR/python/pyproject.toml" ]; then
    log "Installing Python engine (enables live Φ(G) metrics)…"
    pip install -e "$REPO_DIR/python" -q 2>/dev/null || \
        warn "Engine install skipped (pip error) — TUI still works in simulation mode."
fi

# ── 6. verify ──────────────────────────────────────────────────
echo ""
if command -v high-agents &>/dev/null; then
    log "high-agents installed successfully!"
else
    warn "Symlink created at $BIN_TARGET but 'high-agents' not found in PATH."
    warn "Add  export PATH=\"\$PREFIX/bin:\$PATH\"  to your ~/.bashrc or ~/.zshrc"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   DONE!  Launch with:   high-agents                 ║"
echo "║                                                      ║"
echo "║   Keys:  d=dashboard  c=chat  s=regime  q=quit      ║"
echo "║          ?=help  p=pause  r=reset  ↑↓=scroll-log    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 7. Termux shortcut (optional) ──────────────────────────────
SHORTCUTS="$HOME/.shortcuts/tasks"
if [ -d "$HOME/.shortcuts" ]; then
    mkdir -p "$SHORTCUTS"
    cat > "$SHORTCUTS/high-agents" << 'SHORTCUT'
#!/bin/bash
high-agents
SHORTCUT
    chmod +x "$SHORTCUTS/high-agents"
    log "Termux shortcut created: ~/.shortcuts/tasks/high-agents"
fi

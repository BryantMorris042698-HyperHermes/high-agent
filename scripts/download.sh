#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  HIGH-AGENTS  ─  Download & Install Helper
#
#  Usage:
#    bash <(curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/scripts/download.sh)
#
#  Or choose a method manually below.
# ═══════════════════════════════════════════════════════════════

REPO="https://github.com/BryantMorris042698-HyperHermes/high-agent"
RAW="https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main"
BRANCH="main"

set -euo pipefail

log()  { echo "  [+] $*"; }
info() { echo "  [i] $*"; }
sep()  { echo ""; echo "──────────────────────────────────────────────────────"; }

cat << 'BANNER'

  ██╗  ██╗██╗ ██████╗ ██╗  ██╗
  ██║  ██║██║██╔════╝ ██║  ██║     HIGH-AGENTS
  ███████║██║██║  ███╗███████║     Download & Install Helper
  ██╔══██║██║██║   ██║██╔══██║
  ██║  ██║██║╚██████╔╝██║  ██║
  ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝

BANNER

# ── detect environment ─────────────────────────────────────────
IS_TERMUX=false
HAS_GIT=false
HAS_PIP=false
HAS_CURL=false
HAS_PYTHON=false

command -v pkg     &>/dev/null && IS_TERMUX=true
command -v git     &>/dev/null && HAS_GIT=true
command -v pip     &>/dev/null || command -v pip3 &>/dev/null && HAS_PIP=true
command -v curl    &>/dev/null && HAS_CURL=true
command -v python3 &>/dev/null || command -v python &>/dev/null && HAS_PYTHON=true

PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")
PIP=$(command -v pip3 2>/dev/null || command -v pip 2>/dev/null || echo "pip3")

# ── pick install method ────────────────────────────────────────
echo "  Detected:"
echo "    Termux:  $IS_TERMUX"
echo "    git:     $HAS_GIT"
echo "    pip:     $HAS_PIP"
echo "    curl:    $HAS_CURL"
echo "    Python:  $HAS_PYTHON"
sep

if [[ "$IS_TERMUX" == "true" ]]; then
    # ── TERMUX path ──────────────────────────────────────────
    echo ""
    echo "  Termux detected — using pkg + symlink install"
    echo ""
    pkg install python -y -q 2>/dev/null || true

    if [[ "$HAS_CURL" == "true" ]]; then
        log "Downloading high-agents script…"
        curl -fsSL "$RAW/high-agents" -o "$PREFIX/bin/high-agents"
        chmod +x "$PREFIX/bin/high-agents"
    elif [[ "$HAS_GIT" == "true" ]]; then
        log "Cloning repo…"
        git clone "$REPO" ~/high-agent --depth 1 -q
        ln -sf ~/high-agent/high-agents "$PREFIX/bin/high-agents"
        chmod +x "$PREFIX/bin/high-agents"
    else
        echo "  ERROR: need curl or git. Run:  pkg install curl"
        exit 1
    fi

    sep
    echo ""
    echo "  Done!  Launch with:   high-agents"
    echo ""

elif [[ "$HAS_GIT" == "true" ]] && [[ "$HAS_PIP" == "true" ]]; then
    # ── Git + pip path (Linux / macOS desktop) ───────────────
    echo ""
    echo "  Installing via git clone + pip install -e …"
    echo ""

    DEST="${HOME}/high-agent"
    if [[ -d "$DEST" ]]; then
        log "Repo already at $DEST — pulling latest…"
        git -C "$DEST" pull -q
    else
        log "Cloning repo to $DEST …"
        git clone "$REPO" "$DEST" --depth 1 -q
    fi

    log "Installing Python package (editable)…"
    $PIP install -e "$DEST/python" -q

    sep
    echo ""
    echo "  Done!  Launch with:   high-agents"
    echo ""
    echo "  Or run directly:      python $DEST/high-agents"
    echo ""

elif [[ "$HAS_CURL" == "true" ]] && [[ "$HAS_PYTHON" == "true" ]]; then
    # ── Curl fallback (single file, no git/pip needed) ───────
    echo ""
    echo "  Downloading standalone high-agents script…"
    echo ""
    log "Fetching from GitHub…"
    curl -fsSL "$RAW/high-agents" -o high-agents
    chmod +x high-agents

    sep
    echo ""
    echo "  Done!  Run with:   python high-agents"
    echo "         or:         ./high-agents"
    echo ""

else
    echo "  ERROR: Need Python + one of:  git, pip, curl"
    echo ""
    echo "  Manual install options:"
    echo ""
    echo "  1) git clone + pip:"
    echo "     git clone $REPO"
    echo "     cd high-agent && pip install -e python/"
    echo "     high-agents"
    echo ""
    echo "  2) curl (no git / pip):"
    echo "     curl -fsSL $RAW/high-agents -o high-agents"
    echo "     python3 high-agents"
    echo ""
    echo "  3) pip from git:"
    echo "     pip install 'git+$REPO.git#subdirectory=python'"
    echo "     high-agents"
    echo ""
    exit 1
fi

# ── print all available methods for reference ──────────────────
sep
cat << "METHODS"

  All install methods (for reference):

  A. Termux one-liner:
       pkg install python curl -y && \
       curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/high-agents \
            -o $PREFIX/bin/high-agents && chmod +x $PREFIX/bin/high-agents

  B. Git + pip (desktop / server):
       git clone https://github.com/BryantMorris042698-HyperHermes/high-agent
       cd high-agent && pip install -e python/
       high-agents

  C. pip from git (no clone needed):
       pip install "git+https://github.com/BryantMorris042698-HyperHermes/high-agent.git#subdirectory=python"
       high-agents

  D. curl (zero deps, no install):
       curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/high-agents | python3

  E. Termux setup script (full engine + TUI):
       git clone https://github.com/BryantMorris042698-HyperHermes/high-agent
       bash high-agent/scripts/install-termux.sh

METHODS

"""
high_agent_engine.tui
=====================
Entry point for the HIGH-AGENTS live ASCII animated TUI when the package
is installed via pip.  The real TUI code lives in the repo-root ``high-agents``
script so it stays usable as a zero-dependency standalone download too.

This module is intentionally thin — it just locates and launches that script.
"""

from __future__ import annotations

import curses
import importlib.util
import pathlib
import sys


# Candidate paths for the standalone ``high-agents`` script relative to this file:
#   python/high_agent_engine/tui.py
#       → python/high_agent_engine/
#       → python/
#       → repo-root/          ← high-agents lives here (editable install)
_SCRIPT_NAME = "high-agents"

_SEARCH = [
    pathlib.Path(__file__).resolve().parent.parent.parent / _SCRIPT_NAME,   # repo root (editable)
    pathlib.Path(__file__).resolve().parent.parent / _SCRIPT_NAME,          # python/ sub-dir
]


def _load_script(path: pathlib.Path):
    """Import the standalone script as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location("_high_agents_tui", path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules["_high_agents_tui"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    """Launch the HIGH-AGENTS TUI (pip-installed entry point)."""
    for candidate in _SEARCH:
        if candidate.exists():
            mod = _load_script(candidate)
            # mod.main is the curses screen function: main(stdscr)
            try:
                curses.wrapper(mod.main)
            except KeyboardInterrupt:
                pass
            finally:
                print("\n[HIGH-AGENTS] Session ended.")
            return

    # Script not found — give actionable guidance
    print(
        "\n[HIGH-AGENTS] ERROR: standalone script not found.\n\n"
        "  Editable install (recommended):\n"
        "    git clone https://github.com/BryantMorris042698-HyperHermes/high-agent\n"
        "    cd high-agent && pip install -e python/\n"
        "    high-agents\n\n"
        "  Or download the script directly (no git, no pip):\n"
        "    curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/"
        "high-agent/main/high-agents -o high-agents\n"
        "    python high-agents\n"
    )
    sys.exit(1)

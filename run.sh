#!/bin/bash
# Deep Agent Storm Swarm — one-command launcher
# Usage: ./run.sh
# On Termux: bash run.sh
set -e

cd "$(dirname "$0")"

PY=${PYTHON:-python3}

# Auto-install if the package isn't importable yet
if ! "$PY" -c "import high_agent_engine" 2>/dev/null; then
    echo "[+] First run — installing Deep Agent Storm Swarm..."
    "$PY" -m pip install -e . -q
    echo "[+] Done. Starting..."
fi

exec "$PY" -m high_agent_engine "$@"

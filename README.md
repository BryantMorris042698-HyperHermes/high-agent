# Deep Agent Storm Swarm

<div align="center">

**Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)**

Regime-aware AI agent system that maximizes your codebase's structural health score in real time.

![Python](https://img.shields.io/badge/Python-3.9+-green)
![License](https://img.shields.io/badge/License-MIT-purple)

</div>

---

## Install & Run

```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent && ./run.sh
```

That's it. `run.sh` installs everything on first run, then launches the chat TUI.

**Android (Termux):**
```bash
pkg install python git && git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent && bash run.sh
```

---

## What It Does

The system treats your codebase as a directed graph G where every function is a node and every call is an edge. It computes:

```
Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
```

| Symbol | Meaning | Goal |
|--------|---------|------|
| Q(G) | Newman-Girvan modularity — how well functions cluster | Higher |
| Č(G) | Mean inter-module coupling | Lower |
| V | Cyclomatic complexity per function | Lower |
| α, β, γ | Regime coefficients — what to optimize for | Varies |

The system automatically switches between three optimization **regimes** when it detects a structural shift (z-score rolling window), logs every transition, and tells you exactly what's dragging Φ(G) down.

---

## Chat Commands

Once the TUI opens, type anything or use these commands:

| Command | What it does |
|---------|-------------|
| `/metrics` | Live Φ(G) breakdown |
| `/sweep` | Score all regimes — shows which is best |
| `/theory` | Full math explanation |
| `/history` | Regime switch log |
| `/switch <regime>` | Force a regime (Simple / Advanced / Hybrid) |
| `/simulate` | Simulate a graph deviation |
| `/help` | Show all commands |

No LLM needed — the system analyzes and responds using real Φ(G) math. Optionally connect any LLM:

```bash
export OPENAI_API_KEY=sk-...           # OpenAI
export OPENROUTER_API_KEY=sk-or-...    # OpenRouter
export GROQ_API_KEY=gsk_...            # Groq (free tier)
# Ollama is auto-detected if running locally
```

---

## CLI Commands

`run.sh` passes all args through to the engine:

```bash
./run.sh metrics          # Print Φ(G) snapshot
./run.sh sweep            # Evaluate all regimes
./run.sh theory           # Theory Mode explanation
./run.sh crawl ./src      # Crawl and analyze a directory
./run.sh chat "..."       # Single chat message
./run.sh swarm "..."      # Run agent swarm on a task
./run.sh status           # LLM + engine status
./run.sh setup -m gpt-4o -k sk-...   # Configure LLM
```

---

## LLM Providers

| Provider | How to enable | Free? |
|----------|--------------|-------|
| Ollama (local) | `curl -fsSL https://ollama.com/install.sh \| sh && ollama pull llama3.2` | Yes |
| Groq | `export GROQ_API_KEY=gsk_...` | Yes (rate-limited) |
| OpenAI | `export OPENAI_API_KEY=sk-...` | No |
| OpenRouter | `export OPENROUTER_API_KEY=sk-or-...` | Pay-per-token |
| DeepSeek | `export DEEPSEEK_API_KEY=sk-...` | Cheap |

---

## Python API

```python
from high_agent_engine import RegimeEngine

engine = RegimeEngine()
engine.seed_graph()

phi = engine.compute_phi()
print(f"Φ(G) = {phi['phi']:+.4f}  regime={engine.current_regime}")

results = engine.sweep_regimes()
best = max(results, key=lambda x: x[1])
engine.switch_regime(best[0])
```

---

## Project Layout

```
high-agent/
├── run.sh                       # ← start here
├── pyproject.toml               # pip install -e . from root
├── python/
│   └── high_agent_engine/
│       ├── __init__.py          # RegimeEngine, DirectedGraph, Node, Edge
│       ├── graph.py             # Φ(G) math, modularity, coupling
│       ├── engine.py            # Regime switching + detection
│       ├── tui.py               # Chat-first ANSI TUI
│       ├── chat.py              # NeuralAgent with live Φ enrichment
│       ├── agent.py             # Swarm orchestration
│       ├── llm.py               # Unified LLM client
│       ├── crawler.py           # Codebase → graph parser
│       ├── repl.py              # Fallback REPL
│       └── daemon.py            # Background daemon
├── rust/                        # Optional Rust core (desktop TUI)
├── agents/agents.yaml           # Agent profiles
├── skills/skills.yaml           # Learned skills
└── tests/                       # Test suite
```

---

## License

MIT — Copyright (c) 2024-2026 Bryant Morris

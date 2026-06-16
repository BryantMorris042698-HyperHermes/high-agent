# Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm

**Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)** — The mathematical foundation driving regime-aware AI agent orchestration.

---

## What Is This?

Graph_x_0x0 is an AI Operating System built around a live code-graph model. Your entire codebase is represented as a directed graph G=(V,E), where **nodes are functions** and **edges are calls/imports**. Every decision — regime switches, deviation alerts, agent task routing — traces back to Φ(G) computed live on the graph.

It's designed for **Mobile TUI** (Termux, OMEN Laptop) with an 8-agent deep swarm, Ollama API integration, and a self-improving loop that measures, commits, or rolls back changes based on their impact on code architecture quality.

---

## The Math

```
Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
```

| Symbol | Meaning |
|--------|---------|
| **G = (V,E)** | Your codebase as a directed graph. Nodes=functions, Edges=calls/imports |
| **Q(G)** | Newman-Girvan modularity — how well functions cluster within modules. Higher = better cohesion |
| **Č(G)** | Mean inter-module coupling per node. Lower = less spaghetti |
| **V** | Cyclomatic complexity (McCabe). Branches, loops, conditionals per function |
| **α, β, γ** | Regime-dependent coefficients that shift what the system optimizes |

---

## Three Regimes

| Regime | α | β | γ | Strategy |
|--------|---|---|---|---|
| **Simple** | 0.8 | 0.9 | 0.2 | Minimize coupling. Fast iteration. |
| **Advanced** | 1.2 | 0.5 | 0.3 | Maximize modularity. PR review mode. |
| **Hybrid** | 1.0 | 0.6 | 0.4 | Balance all terms. Team handoff mode. |

**Deviation Detection**: Sliding window → z-score → if |z| > 2.0, change-point detected.  
**Hysteresis**: Regime switch only if ΔΦ(G) > 0.05 (prevents oscillation).

---

## 8-Agent Deep Swarm

| Agent | Role |
|-------|------|
| **Orchestrator** | Regime-aware task routing + Φ(G) optimization |
| **Refactor** | Code restructuring + coupling reduction |
| **Quality** | Code review + quality scoring |
| **Test** | Test generation + coverage analysis |
| **Skill** | Skill discovery + management |
| **Repo** | Repository analysis + cloning |
| **Build** | Build orchestration + multi-language support |
| **Planner** | Task decomposition + execution planning |

---

## Project Structure

```
~/high-agent/rust/
├── Cargo.toml              # Package manifest + feature flags
├── src/
│   ├── lib.rs              # Public API + re-exports
│   ├── main.rs             # CLI binary ("high-agent")
│   ├── graph.rs            # G=(V,E), metrics, Newman-Girvan, snapshot
│   ├── core.rs             # RegimeEngine + detect_and_switch
│   ├── orchestrator.rs     # Piecewise regime switching
│   ├── regime.rs           # Regime enum, RegimeCoeffs, compute_phi()
│   ├── metrics.rs          # Metrics, History, PhiColor, Trend
│   ├── ollama.rs           # OllamaClient: /api/tags, /api/generate, /api/chat
│   ├── error.rs            # AgentError, From impls, handle_error! macro
│   ├── agent.rs            # AgentState, AgentId, AgentRole
│   ├── skills.rs           # SkillManager: save/delete/list/load
│   ├── repos.rs            # RepoManager: add/remove/list/clone
│   ├── build.rs            # BuildManager: detect/build/clean (Rust/Python/Node/Go/Java/C++)
│   ├── swarm.rs            # SwarmState, SwarmTask, run_swarm
│   ├── planner.rs          # PlannerState, plan_task, decompose
│   └── bin/
│       └── tui.rs          # Full TUI binary (requires --features tui)
└── benches/
    └── graph_bench.rs      # Benchmark: modularity, coupling, snapshot

~/high-agent/python/        # Python mirror engine
├── high_agent_engine/
│   ├── __init__.py
│   ├── graph.py            # G=(V,E), Φ(G) computation
│   ├── engine.py           # RegimeEngine with detect_and_evaluate
│   ├── regime.py           # Regime enum, hysteresis, detector
│   ├── ollama.py           # Ollama API client
│   └── crawler.py          # Codebase graph crawler
├── high-agent-repl.py      # Live REPL with sweep, theory, history, watch
├── self-improving-loop.py  # baseline → verify → commit → rollback
└── daemon.py               # Background evaluation → ~/.high-agent/state.json
```

---

## Quick Start

### Build

```bash
# Core only (fast, works on Termux/Mobile)
cargo build

# Full TUI (desktop/laptop)
cargo build --features tui

# Release
cargo build --features tui --release
```

### Run

```bash
# CLI mode
cargo run --features tui

# Inside the TUI:
#   [1-6]   Switch tabs: Dashboard / Graph / Theory / History / Agents / Chat
#   [r]     Refresh metrics
#   [s]     Sweep all 3 regimes and switch to best
#   [d]     Simulate deviation and re-evaluate
#   [6]     Open chat — type natural commands
#   [?]     Toggle help overlay
#   [q]     Quit
```

### Chat Commands

```
build rust           Build a Rust project
build python         Build a Python project
create api myapi     Scaffold a new API project
create cli mytool    Scaffold a new CLI tool
create web mysite    Scaffold a web app
analyze ./src        Analyze code quality
test .               Run tests
skill add myskill    Add a new skill
skill list           List loaded skills
clone https://...    Clone a repository
```

### Python Engine

```bash
cd ~/high-agent/python
pip install -e .

# Run the REPL
python high-agent-repl.py

# Run the daemon (writes to ~/.high-agent/state.json)
python daemon.py

# Run the self-improving loop
python self-improving-loop.py
```

---

## Features

- **Φ(G) Live Dashboard** — color-coded (green > 0, yellow > -2, red < -2) with 3-bar gauges for Q/Č/V
- **Regime Engine** — 3 modes with automatic switching via z-score deviation detection
- **8-Agent Swarm** — Orchestrator + 7 specialist agents working in concert
- **Ollama Integration** — Local LLM support for code generation, review, and explanation
- **Skill Manager** — Load, save, list, and delete agent skills on the fly
- **Repo Manager** — Track and clone repos, analyze their graphs
- **Build Manager** — Multi-language detection and build (Rust, Python, Node, Go, Java, C++)
- **TUI with Catppuccin Mocha** — Dark theme, 6 tabs, chat input, help overlay
- **Python Mirror** — Full Rust engine mirrored in Python for Termux/prototyping environments
- **Self-Improving Loop** — Measures Φ(G), commits improvements, rolls back degradation
- **Daemon Mode** — Background evaluation writing JSON state; TUI reads on [r]
- **Segmented Regime Detector** — Sliding window z-score for change-point detection
- **Hysteresis Guard** — Prevents regime oscillation (only switches if ΔΦ > 0.05)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   TUI (ratatui)                      │
│  Dashboard │ Graph │ Theory │ History │ Agents │ Chat│
└──────────────┬──────────────────────┬─────────────────┘
               │ reads               │ writes
               ▼                     ▼
         ~/.high-agent/state.json   ~/.high-agent/state.json
               ▲                     │
               │                     │
┌──────────────┴──────────────────────┴─────────────────┐
│              Rust Engine (RegimeEngine)              │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │   Graph  │  │ Regime   │  │   Ollama Client   │  │
│  │ G=(V,E)  │  │ Engine   │  │  /api/generate    │  │
│  └──────────┘  └──────────┘  └───────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │           8-Agent Swarm                       │  │
│  │ Orchestrator │ Refactor │ Quality │ Test     │  │
│  │ Skill │ Repo │ Build │ Planner                │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

The TUI is a **projection** of the mathematical model. It doesn't compute anything — it reads Φ(G), Q, Č, V from the engine and paints them. The engine has no idea what a terminal is. This separation means you can run the engine headless (daemon, cron, tests) and attach the TUI whenever you want to see what's happening.

---

## Download & Install

### Pre-built Release

Download from GitHub Releases:
```bash
# Linux x86_64
curl -L https://github.com/BryantMorris042698-HyperHermes/high-agent/releases/latest/download/high-agent-x86_64-unknown-linux-musl.tar.gz \
  | tar xz && ./high-agent-tui

# Or use the Python version (no compilation needed)
pip install high-agent
python -m high_agent_engine.engine
```

### From Source

```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/rust

# Core engine (Termux/Mobile)
cargo build

# Full TUI (desktop)
cargo build --features tui

# Run
cargo run --features tui
```

### Python Only (No Rust)

```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/python
pip install -e .

python high-agent-repl.py
```

---

## Requirements

- **Rust** 1.70+ (for core engine + TUI)
- **Python** 3.9+ (for Python mirror)
- **Ollama** (optional, for LLM integration) — https://ollama.ai
- **ratatui 0.29** + **crossterm 0.28** (optional, for TUI — use `--features tui`)

---

## Configuration

Environment variables:

```bash
export OLLAMA_BASE_URL=http://localhost:11434      # Ollama API endpoint
export OLLAMA_MODEL=llama3.2                       # Default model
export HIGH_AGENT_STATE=~/.high-agent/state.json   # State file location
export HIGH_AGENT_SKILLS=~/.high-agent/skills/     # Skills directory
```

---

## License

MIT — See LICENSE file.

---

**Built with Φ(G). Every decision traces back to the graph.**

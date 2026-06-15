# HIGH-AGENTS — AIOS · Mobile TUI · Deep Agents · Storm Swarm

<div align="center">

![Phi(G)](https://img.shields.io/badge/Phi(G)-a*Q(G)-b*D(G)-c*mean(V)-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Rust](https://img.shields.io/badge/Rust-1.75+-orange)
![License](https://img.shields.io/badge/License-MIT-purple)

**Phi(G) = a1*Q(G) + a2*(1-D(G)) + a3*(1/V)** — Regime-aware codebase intelligence

</div>

---

## Live ASCII Animated TUI

```
 ██╗  ██╗██╗ ██████╗ ██╗  ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗
 ██║  ██║██║██╔════╝ ██║  ██║    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝
 ███████║██║██║  ███╗███████║    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ███████╗
 ██╔══██║██║██║   ██║██╔══██║    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ╚════██║
 ██║  ██║██║╚██████╔╝██║  ██║    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████║
 ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝
```

Live animations: banner colour wave · matrix digital rain · braille agent spinners ⠋⠙⠹⠸ · metric bars · Phi(G) sparkline ▁▂▃▄▅▆▇█ · scrolling log · built-in chat (Codebase Analysis Engine skill).

---

## Download & Run

### Termux one-liner (fastest — no git, no pip)
```bash
pkg install python curl -y && \
curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/high-agents \
     -o $PREFIX/bin/high-agents && chmod +x $PREFIX/bin/high-agents
high-agents
```

### Termux full install (engine + TUI)
```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent
bash high-agent/scripts/install-termux.sh
high-agents
```

### pip install (desktop / server)
```bash
# editable install from clone (recommended)
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent
cd high-agent && pip install -e python/
high-agents

# or straight from git (no clone needed)
pip install "git+https://github.com/BryantMorris042698-HyperHermes/high-agent.git#subdirectory=python"
high-agents
```

### curl pipe (zero deps, runs immediately)
```bash
curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/high-agents | python3
```

### Smart auto-detect installer (picks best method for your env)
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/BryantMorris042698-HyperHermes/high-agent/main/scripts/download.sh)
```

---

## TUI Keys

| Key | Action |
|-----|--------|
| `d` | Dashboard — agents · metrics · activity log |
| `c` | Chat — Codebase Analysis Engine skill |
| `s` | Cycle regime (Simple → Advanced → Hybrid → Balanced → Performance → Conservative) |
| `p` / Space | Pause / resume live updates |
| `r` | Reset metrics |
| `↑` / `↓` | Scroll activity log |
| `?` | Help screen |
| `q` / ESC | Quit |

---

## Easy Customisation

All config is at the top of `high-agents` — edit these to change behaviour without touching logic:

```python
CONFIG     = { "fps": 20, "matrix_density": 0.09, ... }    # speeds & density
AGENTS     = [ "OrchestratorAgent", "RefactorAgent", ... ]  # swarm roster
LOG_EVENTS = [ ("OK", "message"), ("WARN", "..."), ... ]    # activity log
REGIMES    = [ ("Balanced", 0.6, 0.8, 0.4), ... ]          # alpha coefficients
```

---

## What is this?

HIGH-AGENTS is a self-improving AI agent system built around one equation: **maximise Phi(G)** — a weighted combination of modularity, coupling, and cyclomatic complexity. Every decision — regime switches, hot spot alerts, refactoring — traces back to this equation computed live on your codebase graph.

Two layers:
- **Python engine** (`python/`) — full featured, stdlib-only core. Works on Termux, Linux, Mac, Windows.
- **Rust core** (`rust/`) — compiled engine with ratatui TUI dashboard. For desktop speed.

---

## The Mathematics

```
Phi(G) = a1*Q(G) + a2*(1 - D(G)) + a3*(1/V_mean)
```

| Symbol | Name | Measures | Direction |
|--------|------|---------|-----------|
| Q(G) | Newman-Girvan modularity | How well functions cluster within modules | Higher = better |
| D(G) | Mean inter-module coupling | Average cross-module edge weight per node | Lower = better |
| V | Cyclomatic complexity (McCabe) | Branches + loops + conditionals per function | Lower = better |
| a1, a2, a3 | Regime coefficients | What the system optimises for | Varies by regime |

**Six regimes** shift the coefficients:

| Regime | a1 | a2 | a3 | When to use |
|--------|----|----|-----|-------------|
| Simple | 1.0 | 0.0 | 0.0 | Minimise coupling only |
| Advanced | 0.5 | 1.0 | 0.0 | Maximise modularity |
| Hybrid | 0.5 | 1.0 | 0.5 | Balance modularity + complexity |
| Balanced | 0.6 | 0.8 | 0.4 | General purpose |
| Performance | 0.3 | 1.0 | 0.8 | Aggressive optimisation |
| Conservative | 0.8 | 0.5 | 0.2 | Minimal changes |

The system auto-detects when the graph deviates (z-score rolling window) and re-evaluates which regime maximises Phi(G).

---

## Agent Swarm

| Agent | Role |
|-------|------|
| OrchestratorAgent | Routes tasks · owns Phi(G) · switches regimes |
| RefactorAgent | Restructures graph · splits nodes · reduces coupling |
| QualityAgent | Monitors cyclomatic complexity · flags violations |
| TestAgent | Ensures test coverage matches modularity targets |
| SkillAgent | Manages learned patterns · runtime skill creation |
| RepoAgent | GitHub ops · clone · fork · PR |
| BuildAgent | Multi-lang compilation · verification · cache |
| PlannerAgent | Multi-step decomposition · rollback planning |

---

## Architecture

```
high-agent/
├── high-agents                    # Standalone TUI — download & run directly
├── python/
│   ├── high_agent_engine/
│   │   ├── tui.py                 # pip entry point → high-agents command
│   │   ├── graph.py               # G=(V,E), Phi(G), modularity, coupling
│   │   ├── engine.py              # RegimeEngine, deviation detection
│   │   ├── chat.py                # NeuralAgent with live Phi(G) enrichment
│   │   ├── agent.py               # OrchestratorAgent + swarm
│   │   ├── skills.py              # SkillManager (learn on the fly)
│   │   └── ...
│   └── pyproject.toml             # pip package (includes high-agents entry point)
├── rust/src/                      # Rust core + ratatui TUI
├── scripts/
│   ├── download.sh                # Auto-detect installer (5 methods)
│   ├── install-termux.sh          # Termux-specific setup
│   └── ...
└── skills/                        # Learned skill definitions
```

---

## REPL Commands

```bash
python -m high_agent_engine        # launch REPL
```

| Command | Description |
|---------|-------------|
| `metrics`, `phi` | Live Phi(G) breakdown |
| `theory` | Full math explanation |
| `sweep` | Evaluate all 6 regimes |
| `switch <R>` | Switch regime manually |
| `crawl <path>` | Analyse a codebase directory |
| `hot` | Show hot spots (V > 5.0) |
| `chat <msg>` | Neural chat with Phi(G) enrichment |
| `swarm <task>` | Run deep agent swarm |
| `learn <n>: <d>` | Save a new skill |
| `help` | Show all commands |

---

## LLM Providers

Auto-detected in order:

| Provider | Setup |
|----------|-------|
| **Ollama** (local, free) | `ollama run llama3.2:3b` |
| **OpenAI** | `export OPENAI_API_KEY=sk-...` |
| **OpenRouter** | `export OPENROUTER_API_KEY=sk-or-...` |
| **Groq** | `export GROQ_API_KEY=gsk_...` |
| **DeepSeek** | `export DEEPSEEK_API_KEY=sk-...` |

---

## Python API

```python
from high_agent_engine import RegimeEngine, DirectedGraph, Node, Edge

graph = DirectedGraph()
graph.add_node(Node("authenticate", "auth", "auth/mod.rs"))
graph.add_node(Node("validate_token", "auth", "auth/mod.rs"))
graph.add_edge(Edge("authenticate", "validate_token"))

snap = graph.snapshot_full("Balanced")
print(f"Phi(G) = {snap.phi:.4f}  Q={snap.q:.3f}  D={snap.coupling:.3f}")

engine = RegimeEngine()
engine.graph = graph
best = max(engine.sweep_regimes(), key=lambda x: x[1])
print(f"Best regime: {best[0]}  Phi(G) = {best[1]:.4f}")
```

---

## Development

```bash
# Python tests
cd python && pip install -e ".[all]" && pytest tests/ -v

# Rust tests
cd rust && cargo test --features tui

# Build release
./scripts/build-release.sh
```

---

## Roadmap

- [ ] GPU-accelerated graph visualisation in TUI
- [ ] Streaming token output for neural chat
- [ ] Persistent skill storage (SQLite)
- [ ] MCP server integration
- [ ] WebSocket daemon for remote TUI
- [ ] Codebase diff analysis (before/after Phi(G))
- [ ] Multi-language crawler (JavaScript, Go, Rust)
- [ ] PyPI release (after v0.3.0)

---

## License

MIT — see [LICENSE](LICENSE)

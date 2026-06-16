# Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm

<div align="center">

![Φ(G)](https://img.shields.io/badge/Φ(G)-α·Q(G)−β·Č(G)−γ·mean(V)-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Rust](https://img.shields.io/badge/Rust-1.75+-orange)
![License](https://img.shields.io/badge/License-MIT-purple)
![GitHub](https://img.shields.io/badge/GitHub-BryantMorris042698/HyperHermes/high--agent-red)

**Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)** — Regime-aware code architecture intelligence

</div>

---

## What is this?

Graph_x_0x0 is a self-improving AI agent system built around a single mathematical objective: **maximize Φ(G)** — a weighted combination of modularity, coupling, and cyclomatic complexity. Every decision the system makes — regime switches, hot spot alerts, refactoring suggestions — traces back to this equation computed live on your codebase graph.

It's built in two layers:
- **Rust core** (`rust/`) — Fast, compiled engine with TUI dashboard. For OMEN/Arch/Mac.
- **Python engine** (`python/`) — Full mirror, runs anywhere. For Termux, prototyping, CI.

---

## Quick Start

### Clone
```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent
```

### Python (works everywhere — Termux, Linux, Mac, Windows)
```bash
cd python
pip install -e .                    # Install the package

# Interactive REPL (no install needed — also works directly)
python high-agent-repl.py

# Or via module
python -m high_agent_engine        # Full REPL
python -m high_agent_engine metrics # Quick metrics
python -m high_agent_engine sweep   # Evaluate all regimes
python -m high_agent_engine theory  # Full math explanation
python -m high_agent_engine crawl ./src  # Analyze your codebase
python -m high_agent_engine chat "what are the hot spots?"  # Neural chat

# With LLM (optional)
export OPENAI_API_KEY=sk-...        # Or use Ollama (auto-detected)
python high-agent-repl.py --model gpt-4o --api-key $OPENAI_API_KEY
```

### Rust (fast TUI on desktop)
```bash
cd rust
cargo build --features tui          # Build with TUI dashboard
cargo run --example basic --features tui   # Run example
cargo run --bin high-agent-tui --features tui  # TUI dashboard
```

---

## The Mathematics

Everything starts with one equation:

```
Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
```

| Symbol | Name | What it measures | Direction |
|--------|------|-----------------|-----------|
| G | Graph | Your codebase as nodes (functions) + edges (calls) | — |
| Q(G) | Newman-Girvan modularity | How well functions cluster within modules | Higher = better |
| Č(G) | Mean inter-module coupling | Average cross-module edge weight per node | Lower = better |
| V | Cyclomatic complexity (McCabe) | Branches + loops + conditionals per function | Lower = better |
| α, β, γ | Regime coefficients | What the system optimizes for | Varies by regime |

**Three regimes** shift the coefficients:

| Regime | α | β | γ | When to use |
|--------|---|---|---|------------|
| Simple | 1.0 | 0.0 | 0.0 | Minimize coupling only |
| Advanced | 0.5 | 1.0 | 0.0 | Maximize modularity only |
| Hybrid | 0.5 | 1.0 | 0.5 | Balance modularity + complexity |
| Balanced | 0.7 | 0.8 | 0.5 | General purpose |
| Performance | 1.0 | 1.2 | 0.8 | Aggressive optimization |
| Conservative | 0.4 | 0.4 | 0.2 | Minimal changes |

The system automatically detects when the graph deviates from baseline (via z-score rolling window) and re-evaluates which regime maximizes Φ(G). Every switch is logged.

---

## Architecture

```
high-agent/
├── python/                          # Python mirror (Termux/portable)
│   ├── high_agent_engine/           # Package
│   │   ├── graph.py                 # G=(V,E), Φ(G), modularity, coupling
│   │   ├── engine.py                # RegimeEngine, detect_and_evaluate()
│   │   ├── regime.py                # Regime enum, coefficients, transitions
│   │   ├── crawler.py               # Codebase → graph parser
│   │   ├── llm.py                   # Unified LLM client (Ollama + cloud)
│   │   ├── chat.py                  # NeuralAgent with live Φ(G) enrichment
│   │   ├── agent.py                 # OrchestratorAgent, RefactorAgent, Swarm
│   │   ├── skills.py                # SkillManager (learn on the fly)
│   │   ├── repos.py                 # RepoAgent (GitHub operations)
│   │   ├── daemon.py                # Background evaluation daemon
│   │   └── repl.py                  # Full REPL
│   ├── high-agent-repl.py           # Standalone REPL (no install)
│   ├── pyproject.toml               # Package manifest
│   └── requirements.txt
├── rust/                            # Rust core (fast TUI on desktop)
│   ├── src/
│   │   ├── graph.rs                 # 560 lines: G=(V,E), metrics, detection
│   │   ├── core.rs                  # 536 lines: RegimeEngine + Theory Mode
│   │   ├── orchestrator.rs          # 264 lines: piecewise regime switching
│   │   ├── regime.rs                # Regime enum + coefficients
│   │   ├── agent.rs                 # Agent abstractions
│   │   ├── swarm.rs                 # Swarm orchestration
│   │   ├── planner.rs               # Task planner
│   │   ├── tui.rs                   # 479 lines: ratatui dashboard
│   │   └── bin/tui.rs               # TUI binary entry point
│   └── examples/basic.rs            # Complete working example
├── scripts/                         # Automation
│   ├── install.sh                   # One-line installer
│   ├── demo.sh                      # Demo runner
│   ├── termux-setup.sh              # Termux-specific setup
│   └── build-release.sh             # Release builder
├── skills/                          # Learned skills directory
├── agents/                          # Agent configs
├── tests/                           # Test suites
└── .github/workflows/               # CI/CD pipelines
```

---

## Key Features

### Neural Chat with Φ(G) Enrichment
Every message to the neural agent automatically includes live metrics:
```
Φ(G) = +0.1234 | Q = 0.723 | Č = 0.456 | V = 4.2
Regime: Balanced | Hot spots: fn_authenticate (V=12.3), fn_parse_json (V=9.1)
```
The agent understands your codebase architecture in real time.

### Deep Agent Swarm
Agents are regime-aware and specialize:
- **OrchestratorAgent** — routes tasks to the right specialist
- **RefactorAgent** — fixes coupling violations and hot spots
- **QualityAgent** — improves code quality scores
- **TestAgent** — ensures test coverage matches Φ(G)
- **SkillAgent** — learns new capabilities from interactions
- **RepoAgent** — manages GitHub operations (clone, fork, PR)
- **BuildAgent** — handles compilation and build verification
- **PlannerAgent** — multi-step task planning with rollback

### Regime-Aware Deviation Detection
Uses segmented regression (z-score rolling window) to detect when your codebase graph has changed significantly. Triggers automatic regime re-evaluation with hysteresis (0.05 margin).

### Add Skills by Asking
```
learn refactor-circular-deps: Detect and break circular import chains
```
The system stores skills persistently and retrieves them contextually.

### Clone and Run Anywhere
```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/python
pip install -e .
python high-agent-repl.py
```
Works on Termux (Android), Linux, Mac, and Windows (WSL).

---

## REPL Commands

| Command | Description |
|---------|-------------|
| `metrics`, `phi` | Live Φ(G) breakdown |
| `theory` | Full Theory Mode explanation |
| `sweep` | Evaluate all 6 regimes |
| `switch <R>` | Switch regime (Simple/Advanced/Hybrid/Balanced/Performance/Conservative) |
| `history [n]` | Show last n snapshots |
| `crawl <path> [-r]` | Crawl and analyze a directory |
| `load <file>` | Load graph from JSON |
| `hot` | Show hot spots (V > 5.0) |
| `coupling` | Show coupling violations |
| `chat <msg>` | Neural chat with Φ(G)-powered agent |
| `swarm <task>` | Run deep agent swarm |
| `skills` | List available skills |
| `learn <n>: <d>` | Save a new skill |
| `setup [prov] [m] [k]` | Configure LLM provider |
| `status` | System + LLM status |
| `simulate` | Simulate regime deviation (for demos) |
| `reload` | Reset engine to seed graph |
| `sh <cmd>` | Run shell command |
| `help`, `?` | Show help |
| `quit`, `exit` | Exit |

---

## LLM Providers

Graph_x_0x0 supports multiple LLM providers with auto-detection:

| Provider | Setup | Default Model |
|----------|-------|--------------|
| **Ollama** (local, free) | `curl -fsSL https://ollama.com/install.sh \| sh` | `llama3.2:3b` |
| **OpenAI** | `export OPENAI_API_KEY=sk-...` | `gpt-4o-mini` |
| **OpenRouter** | `export OPENROUTER_API_KEY=sk-or-...` | `anthropic/claude-3.5-haiku` |
| **Groq** | `export GROQ_API_KEY=gsk_...` | `llama-3.3-70b-versatile` |
| **DeepSeek** | `export DEEPSEEK_API_KEY=sk-...` | `deepseek-chat` |

Auto-detection: model names starting with `openai/`, `groq/`, `openrouter/` are routed automatically. Ollama is checked first if running locally.

---

## API

### Python
```python
from high_agent_engine import RegimeEngine, DirectedGraph, Node, Edge, Regime

# Build a graph
graph = DirectedGraph()
graph.add_node(Node("authenticate", "auth", "auth/mod.rs"))
graph.add_node(Node("validate_token", "auth", "auth/mod.rs"))
graph.add_node(Node("login", "auth", "auth/mod.rs"))
graph.add_edge(Edge("login", "authenticate"))
graph.add_edge(Edge("login", "validate_token"))

# Analyze
snap = graph.snapshot_full("Balanced")
print(f"Φ(G) = {snap.phi:.4f}")
print(f"Q(G) = {snap.q:.4f}")
print(f"Č(G) = {snap.coupling:.4f}")

# Regime engine
engine = RegimeEngine()
engine.graph = graph
results = engine.sweep_regimes()
best = max(results, key=lambda x: x[1])
engine.switch_regime(best[0])
print(f"Best: {best[0]} with Φ(G) = {best[1]:.4f}")
```

### Rust
```rust
use high_agent_rs::{DirectedGraph, Node, Edge, RegimeEngine};

let mut graph = DirectedGraph::new();
graph.add_node(Node::new("authenticate", "auth", "auth/mod.rs"));
graph.add_node(Node::new("validate_token", "auth", "auth/mod.rs"));
graph.add_edge(Edge::new("authenticate", "validate_token"));

let mut engine = RegimeEngine::new();
engine.graph = graph;
let results = engine.sweep_regimes();
let (best, phi) = results.into_iter().max_by(|a, b| a.1.partial_cmp(&b.1).unwrap()).unwrap();
println!("Best: {} with Φ(G) = {:.4}", best, phi);
```

---

## Development

```bash
# Python tests
cd python
pip install -e ".[all]"
pytest tests/ -v

# Rust tests
cd ../rust
cargo test --features tui

# Build release
./scripts/build-release.sh
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## Roadmap

- [ ] GPU-accelerated graph visualization in TUI
- [ ] Streaming token output for neural chat
- [ ] Persistent skill storage (SQLite)
- [ ] MCP server integration
- [ ] WebSocket daemon for remote TUI
- [ ] Codebase diff analysis (before/after Φ(G))
- [ ] Multi-language crawler (JavaScript, Go, Rust)
- [ ] Pypi release (after v0.3.0)

---

## License

MIT — see [LICENSE](LICENSE)
# Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm

## 1. Concept & Vision

Graph_x_0x0 is a self-aware AI operating system built around a live computational graph of the codebase it manages. It thinks in terms of graph topology — nodes (functions), edges (dependencies), and a single scalar objective Φ(G) that measures architectural quality in real time. Every decision traces back to math. The TUI makes the math visible, beautiful, and interactive. It runs everywhere: desktop with a full TUI, mobile (Termux) as a headless daemon, and as a Python mirror for rapid prototyping.

The system is designed as a **storm of agents** — a swarm of specialized sub-agents coordinated by a central orchestrator, each contributing to the graph, each optimizing Φ(G) from a different angle.

## 2. Design Language

### Aesthetic Direction
Catppuccin Mocha — warm, readable, professional. Not hacker-aesthetic green-on-black, not corporate blue. The palette is cozy yet precise, like a well-designed IDE theme.

### Color Palette (Hex → RGB)
- **Base**: #1E1E2E (background), #313244 (surface), #45475A (overlay)
- **Text**: #CDD6F4 (primary), #A6ADC8 (secondary), #6C7086 (muted)
- **Accent**: #CBA6F7 (mauve — Φ(G) highlight), #F38BA8 (red), #A6E3A1 (green), #F9E2AF (yellow)
- **Regime Colors**: Simple=#89B4FA (blue), Advanced=#A6E3A1 (green), Hybrid=#FAB387 (peach)

### Typography
- **Primary**: System monospace (the TTY is the canvas)
- **Headers**: Bold, uppercase for labels
- **Metrics**: Large, color-coded numbers

### Motion Philosophy
- No animations in TUI — instant state reflection
- Regime transitions: flash the Φ(G) badge, log to history
- History scroll: instant, no interpolation

## 3. Architecture — 5 Layers

### Layer 1: Graph Core (graph.rs — 560 lines)
Pure computation. No I/O, no UI.

**Data Model:**
```rust
pub struct Node { id, module, cyclomatic, quality }
pub struct Edge { from, to, weight }
pub struct DirectedGraph { nodes: HashMap<String, Node>, edges: Vec<Edge> }
```

**Key Methods:**
- `modularity()` — Newman-Girvan Q per module
- `mean_coupling()` — average cross-module edge weight per node
- `total_cyclomatic()` / `mean_quality()` — aggregations
- `snapshot()` — produces `GraphSnapshot` for deviation detector
- `multi_objective(&snapshot, &coeffs)` — computes Φ(G)

**Deviation Detection:** SegmentedRegimeDetector with sliding window, z-score > 2.0 triggers change-point detection.

### Layer 2: Regime Engine (core.rs + orchestrator.rs)

Three regimes, different coefficient profiles:

| Regime   | α   | β   | γ   | Strategy |
|----------|-----|-----|-----|----------|
| Simple   | 0.8 | 0.9 | 0.2 | Minimize coupling. Fast iteration. |
| Advanced | 1.2 | 0.5 | 0.3 | Maximize modularity. PR review mode. |
| Hybrid   | 1.0 | 0.6 | 0.4 | Balance all. Team handoff mode. |

**Orchestrator:**
- `best_regime(snapshot)` — evaluates all 3, picks maximizing Φ(G)
- `evaluate_and_switch(graph)` — hysteresis margin 0.05
- `detect_and_switch(graph)` — feed detector → if deviation → re-evaluate

### Layer 3: Python Mirror
Mirrors Rust core for Termux / rapid prototyping:
- `graph.py` — G=(V,E), Φ(G) computation
- `engine.py` — RegimeEngine with `detect_and_evaluate()`
- `regime.py` — Regime enum, hysteresis, detector
- `self-improving-loop.py` — baseline → verify → commit → rollback cycle
- `high-agent-repl.py` — live REPL with sweep, theory, history, watch commands
- `crawler.py` — statically analyzes real codebases into JSON graphs
- `daemon.py` — background evaluation daemon, writes JSON for TUI

### Layer 4: TUI Dashboard (tui.rs — 479+ lines)
Built with ratatui 0.29 + crossterm 0.28.

**4 Tabs:**
| Tab       | Function       | Content |
|-----------|----------------|---------|
| Dashboard | draw_dashboard | Φ(G) headline + 3 gauges (Q/Č/V) + detail panel |
| Graph     | draw_graph     | ASCII topology visualization |
| Theory    | draw_theory    | Formatted math explanation with live values |
| History   | draw_history   | Timeline of snapshots with trend arrows |

**Status Bar:** Graph_x_0x0 + codebase + Φ value + regime badge

**Event Loop:** draw → poll → handle_key → repeat. Single-threaded, blocking.

### Layer 5: Cargo Setup
Feature-gated TUI: `cargo build` (no TUI) vs `cargo build --features tui` (full dashboard).
TUI binary in `src/bin/tui.rs` with `required-features = ["tui"]`.

## 4. Swarm / Multi-Agent System

### Agent Types
1. **Orchestrator Agent** — central coordinator, owns Φ(G), manages regime
2. **Refactor Agent** — optimizes graph structure (split nodes, merge edges)
3. **Quality Agent** — monitors cyclomatic complexity, flags violations
4. **Test Agent** — ensures test coverage per module
5. **Skill Agent** — manages skill library, loads/creates skills on demand
6. **Repo Agent** — manages repository connections, clones, fetches

### Agent Communication
All agents share the same graph state. They emit graph mutations (add_node, remove_edge, etc.) that the orchestrator applies and evaluates. The orchestrator runs all mutations through Φ(G) before committing.

### Adding Skills
Skills are markdown files in `~/.hermes/skills/` or the `skills/` directory. The Skill Agent can:
- List available skills (`skill list`)
- Load a skill (`skill load <name>`)
- Create a new skill from conversation (`skill save <name>`)
- Update an existing skill (`skill update <name>`)

### Adding Repos
Repos are registered via the REPL or daemon config:
```
repo add <name> <url> [--path <local_path>]
repo list
repo remove <name>
repo sync <name>
```

## 5. CLI / API Surface

### Rust Binaries
- `high-agent-rs` — CLI tool (seed, evaluate, process-task, load-json)
- `high-agent-tui` — Full TUI dashboard (requires `--features tui`)

### Python Scripts
- `high-agent-repl.py` — Interactive REPL
- `daemon.py` — Background daemon (`--daemon`)
- `crawler.py` — Codebase analyzer (`python crawler.py <path>`)
- `self-improving-loop.py` — Auto-improvement cycle

### Daemon ↔ TUI Protocol
Daemon writes JSON to `~/.high-agent/state.json`:
```json
{
  "phi": 0.1234,
  "q": 0.45,
  "coupling": 0.32,
  "mean_v": 5.2,
  "regime": "Advanced",
  "n_nodes": 42,
  "n_edges": 67,
  "timestamp": "2026-06-14T18:30:00Z"
}
```
TUI reads this on `[r]` keypress or configurable auto-refresh.

## 6. Technical Stack

- **Rust**: 1.75+, edition 2021
- **Dependencies**: serde, serde_json, serde_yaml, ratatui (opt), crossterm (opt)
- **Python**: 3.10+, no external deps for core engine
- **TUI**: ratatui 0.29, crossterm 0.28

## 7. File Tree

```
high-agent/
├── SPEC.md
├── README.md
├── LICENSE
├── rust/
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs
│   │   ├── main.rs
│   │   ├── graph.rs
│   │   ├── core.rs
│   │   ├── orchestrator.rs
│   │   ├── error.rs
│   │   ├── regime.rs
│   │   ├── metrics.rs
│   │   ├── skills.rs
│   │   ├── repos.rs
│   │   └── bin/
│   │       └── tui.rs
│   ├── benches/
│   │   └── graph_bench.rs
│   └── examples/
│       └── basic.rs
├── python/
│   ├── high_agent_engine/
│   │   ├── __init__.py
│   │   ├── graph.py
│   │   ├── engine.py
│   │   ├── regime.py
│   │   ├── crawler.py
│   │   ├── metrics.py
│   │   ├── skills.py
│   │   ├── repos.py
│   │   └── daemon.py
│   ├── high-agent-repl.py
│   ├── self-improving-loop.py
│   └── requirements.txt
├── skills/
│   └── README.md
├── agents/
│   └── README.md
├── scripts/
│   ├── install.sh
│   ├── demo.sh
│   └── termux-setup.sh
└── tests/
    ├── test_graph.py
    ├── test_engine.py
    └── test_integration.py
```

## 8. Quality Bar

- All Rust modules compile with zero warnings
- Python engine produces identical Φ(G) values to Rust engine (cross-validation test)
- TUI renders correctly at 80x24 minimum, 120x40 optimal
- Daemon can run 24/7 without memory leaks
- Self-improving loop achieves positive Φ(G) delta on test codebase within 3 iterations
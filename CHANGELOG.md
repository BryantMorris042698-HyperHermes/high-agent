# Changelog

All notable changes to Graph_x_0x0 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0] — 2025-XX-XX

### Added
- **Neural Chat Layer** (`llm.py`, `chat.py`, `agent.py`):
  - Unified LLM client supporting Ollama, OpenAI, OpenRouter, Groq, and DeepSeek with auto-detection
  - `NeuralAgent` class that enriches every message with live Φ(G) metrics, hot spots, and regime context
  - `OrchestratorAgent` with regime-aware task routing and hot spot detection
  - `RefactorAgent`, `QualityAgent`, `TestAgent`, `SkillAgent`, `RepoAgent`, `BuildAgent`, `PlannerAgent`
  - Agent Swarm with multi-agent parallel execution and result synthesis
- **Full REPL** (`repl.py`): sweep, theory, history, hot, coupling, skills, learn, setup, scan, analyze, chat, swarm, refactor commands
- **Standalone REPL** (`high-agent-repl.py`): Run without installation — `python high-agent-repl.py`
- **CLI Entry Point** (`__main__.py`): `python -m high_agent_engine` with subcommands (metrics, sweep, theory, crawl, chat, swarm, status, setup)
- **pyproject.toml**: v0.2.0 with all modules, entry points, optional extras (`[ollama]`, `[all]`)
- **Rust Example** (`rust/examples/basic.rs`): Complete working example with Φ(G) output
- **Python tests** (`tests/test_high_agent_engine.py`): Core tests for graph, engine, regime, crawler

### Fixed
- `engine.py`: Added `snapshot()`, `compute_phi()`, `regime_coeffs()`, `update()` wrapper methods
- `engine.py`: Fixed `ai_analyze()` method with null-check guards
- `engine.py`: Fixed `switch_regime()` for case when metrics is None
- `engine.py`: Fixed `process_task()` — `n_nodes` property call fixed to `n_nodes` attribute
- `__init__.py`: Lazy imports with `_llm_available()` check so package installs without LLM deps
- `high-agent-repl.py`: Syntax error on line 67 (extra `f{` prefix)

## [0.1.0] — 2025-06-15

### Added
- **Graph Core**: `DirectedGraph`, `Node`, `Edge`, `GraphSnapshot` — G=(V,E) code model
- **Metrics Engine**: Newman-Girvan modularity Q(G), coupling Č(G), cyclomatic complexity V
- **Φ(G) Objective**: `α·Q(G) − β·Č(G) − γ·mean(V)` computed live on the graph
- **Three Regimes**: Simple (α=1.0), Advanced (α=0.5,β=1.0), Hybrid (α=0.5,β=1.0,γ=0.5)
- **SegmentedRegimeDetector**: Z-score rolling window for deviation detection
- **RegimeEngine**: Orchestrates graph + detector + regime switching with hysteresis
- **CodebaseCrawler**: Parses directories into DirectedGraph
- **Rust TUI Dashboard** (`ratatui`): 4-tab dashboard (Dashboard, Graph, Theory, History)
- **Self-improving loop**: `python high_agent_engine/self-improving-loop.py`
- **GitHub workflows**: CI (6 parallel jobs), Release (PyPI on version tags)
- **GitHub issue/PR templates**: Bug report, feature request, PR template
- **Shell scripts**: install.sh, demo.sh, termux-setup.sh, build-release.sh
- **Documentation**: SPEC.md, CONTRIBUTING.md, LICENSE, skills/README.md, agents/README.md

### Known Issues
- `test_regime_detector` (Rust) is `#[ignore]`d — z-score window includes test snapshot in baseline, making it environment-sensitive
- TUI requires `cargo build --features tui` — not available on Termux (use Python engine instead)
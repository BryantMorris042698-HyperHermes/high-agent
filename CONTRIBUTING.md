# Contributing to Graph_x_0x0

Thank you for contributing to Graph_x_0x0! This document covers everything you need to know to get started.

## Quick Links

- [SPEC.md](SPEC.md) — Full system specification
- [README.md](README.md) — Project overview and quick start
- [Rust README](rust/README.md) — Rust-specific documentation
- GitHub Issues: https://github.com/BryantMorris042698-HyperHermes/high-agent/issues

## Project Structure

```
high-agent/
├── rust/               # Rust core engine + TUI
│   ├── src/
│   │   ├── graph.rs    # G=(V,E), Φ(G), deviation detection
│   │   ├── core.rs     # RegimeEngine
│   │   ├── orchestrator.rs  # Piecewise regime switching
│   │   ├── regime.rs   # Regime definitions
│   │   ├── metrics.rs  # Metrics + History for TUI
│   │   ├── tui.rs      # ratatui dashboard (in src/bin/)
│   │   └── agents/     # Agent definitions
│   ├── benches/        # Criterion benchmarks
│   └── examples/       # Usage examples
├── python/             # Python mirror engine
│   └── high_agent_engine/  # graph.py, engine.py, regime.py, etc.
├── skills/             # Skill definitions
├── agents/             # Agent configurations
├── scripts/            # Shell scripts
└── tests/              # Python integration tests
```

## Development Setup

### Rust

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone and enter
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/rust

# Core only (fast, works everywhere)
cargo build

# Full TUI (desktop)
cargo build --features tui

# Run tests
cargo test --features tui

# Run clippy
cargo clippy --features tui -- -D warnings

# Run benchmarks
cargo bench
```

### Python

```bash
cd high-agent/python
pip install -e .

# Verify
python -c "from high_agent_engine import *; print('OK')"

# Run the REPL
python high-agent-repl.py

# Run the daemon
python high_agent_engine/daemon.py
```

## Code Style

### Rust

- Format with `cargo fmt` (rustfmt default)
- Clippy warnings as errors: `cargo clippy --features tui -- -D warnings`
- No `unsafe` unless absolutely necessary and documented
- Feature-gate TUI dependencies behind the `tui` feature flag
- All public API items must have doc comments (`///`)
- Error handling via `thiserror` (`HighAgentError` enum)
- Thread-safety via `parking_lot` RwLock where needed

### Python

- Follow PEP 8
- Type hints on all public functions
- Docstrings on all public classes and functions
- No external dependencies for core engine (stdlib only)

## The Math First Principle

Graph_x_0x0 is built around Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V). Every architectural decision should trace back to the graph:

- **Adding a new module?** Ask: how does this affect Q(G)?
- **Adding a cross-module dependency?** Ask: how does this affect Č(G)?
- **Adding a new function?** Ask: how does this affect mean(V)?
- **Any change that doesn't improve Φ(G)?** You need a strong justification.

This doesn't mean the system is rigid — regimes shift the coefficients so the same change can be good or bad depending on context. But the math must always be consulted.

## Filing Issues

- Search existing issues first
- Use the issue templates (Bug Report / Feature Request)
- Tag appropriately: `bug`, `enhancement`, `question`, `documentation`
- For bugs: include reproduction steps, environment, and output
- For features: explain the problem it solves and the Φ(G) impact

## Submitting PRs

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes (follow code style above)
4. Add tests
5. Ensure CI passes
6. Open a PR with the PR template filled out

## Architecture Decision Process

For significant architectural changes:

1. Discuss in an issue first (don't PR without prior discussion)
2. Update SPEC.md to reflect the change
3. Update README.md if user-facing behavior changes
4. Ensure the Python mirror stays in sync with the Rust core

## Adding New Agents

1. Define the agent in `rust/src/agent.rs`
2. Implement the agent logic in a new `rust/src/agents/<name>.rs`
3. Wire it into the swarm in `rust/src/swarm.rs`
4. Add the Python equivalent in `python/high_agent_engine/agents/`
5. Document the agent in `agents/README.md`

## Adding New Skills

Skills are markdown files in `skills/` or `~/.hermes/skills/`. Each skill:
- Has a unique name
- Describes trigger conditions
- Has numbered steps with exact commands
- Documents pitfalls and verification steps

See `skills/README.md` for the skill template.

## Regime Switching

Regime changes are a first-class concept. When would a PR or refactoring change the regime?

- **Simple → Advanced**: Codebase growing, team needs stricter quality gates
- **Advanced → Simple**: Rapid prototyping phase, speed over polish
- **Any → Hybrid**: Team handoff, balancing speed and quality

All regime transitions are logged as `RegimeTransition { from, to, reason, phi_before, phi_after }`.

## Performance

If you're touching the graph core:

- Profile with `cargo bench` before and after
- The graph operations (Q, Č, V) should all be O(n) or better
- Avoid O(n²) in hot paths — use HashMaps instead of Vec scans
- The daemon must be able to run 24/7 without memory leaks

## Questions?

Open an issue with the `question` label, or reach out via the project discussions.

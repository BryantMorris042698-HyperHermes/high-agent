---
name: Pull Request
about: Submit changes to Graph_x_0x0
title: "[PR] "
labels: ""
assignees: ""
---

## Description
Brief description of what this PR changes and why.

## Type of Change
What type of PR is this?

- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Refactoring (no Φ(G) / behavior change)
- [ ] Documentation update
- [ ] Test coverage
- [ ] Build/CI change
- [ ] Performance improvement

## Layers Affected
Check all that apply:

- [ ] Rust core (src/*.rs — graph, core, regime, metrics, etc.)
- [ ] Rust TUI (src/bin/tui.rs)
- [ ] Python mirror (python/high_agent_engine/)
- [ ] Python scripts (high-agent-repl.py, daemon.py, etc.)
- [ ] Documentation (README, SPEC, docs/)
- [ ] CI/CD (.github/workflows/)
- [ ] Scripts (scripts/*.sh)

## Testing
How was this tested?

- [ ] Rust: `cargo test`
- [ ] Rust: `cargo clippy -- -D warnings`
- [ ] Python: pytest or manual test
- [ ] TUI: manual terminal test
- [ ] Cross-platform (tested on multiple OS)
- [ ] No tests (please explain why)

## Φ(G) Impact
Does this change the Φ(G) computation or regime switching logic?

- [ ] No — pure refactor/UI/infra
- [ ] Yes — behavior intentionally changed (explain below)
- [ ] Unsure

## Checklist
- [ ] Code compiles: `cargo build --features tui`
- [ ] Zero warnings on `cargo clippy --features tui -- -D warnings`
- [ ] Tests pass: `cargo test --features tui`
- [ ] Python engine verified: `python -c "from high_agent_engine import *; print('OK')"`
- [ ] No new `unsafe` blocks introduced (unless absolutely necessary)
- [ ] Features are feature-gated (TUI deps behind `tui` feature)

## Additional Notes
Anything else reviewers should know.

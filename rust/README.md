# High-Agent RS (Rust Implementation)

This directory contains the Rust implementation of the combined framework.

## Two Versions

### 1. Mathematical Theory Only (core only)
- Pure graph-theoretic optimisation + segmented/hybrid regime switching
- No TUI, minimal dependencies
- Focused on the objective function and deviation detection

### 2. Full High-Agent (recommended for you)
- Full ratatui TUI
- Regime engine + live objective calculation
- Hardware optimization hooks (RTX 5080 / Termux mobile)
- Ready for Ollama integration and skills loading

## Build Instructions (on your Arch laptop)

```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/rust/high-agent-rs
rustup update stable
cargo build --release
./target/release/high-agent-rs
```

Press `s` to simulate regime switch, `t` to process a task, `q` to quit.

The TUI shows live regime state and the multi-objective value from your Mathematical Theory of Code.

## Next Steps (tell me which to build first)
- Real Ollama client integration
- Proper graph data structure
- Device detection (CUDA vs Termux)
- Systemd service + Hyprland keybind packaging

This is the foundation. The TUI is the primary interface as requested.
# High-Agent RS - Termux Optimized (Lightweight)

This is the **lightweight Termux version** optimized for your Galaxy Z Fold7 and Lenovo Idea Tab Pro.

## Goals for Mobile
- Minimal dependencies
- Fast to build on-device or via cross-compilation
- Core regime engine (Mathematical Theory + segmented/hybrid switching) runs efficiently on ARM
- Simple text/CLI interface that works great in Termux
- Heavy tasks automatically routed to your RTX 5080 laptop via Tailscale

## Build on Termux

```bash
pkg update && pkg install rust clang
cargo install cargo-edit  # optional

# Clone
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/rust/high-agent-rs-termux

cargo build --release
./target/release/high-agent-rs-termux
```

## Key Features
- Same RegimeEngine as the full version
- Lightweight text interface showing current regime and objective value
- `s` = simulate deviation & switch regime
- `t <task>` = process task (triggers regime logic)
- Designed to stay in Simple regime by default and escalate only when needed

## Cross-Device Workflow (Recommended)
- Run full rich TUI on laptop
- Run this lightweight client on phone/tablet
- Use Tailscale for seamless task routing and result sync

This version keeps the mathematical guarantees of your Theory of Code while being practical on mobile hardware.
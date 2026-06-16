# High-Agent: Mathematical Theory of Code + Dynamic Regime System

**Created by:** Bryant Issiah Morris Jr.  
**Date:** June 2026  
**Status:** Running on laptop (RTX 5080) and Galaxy Z Fold7 (Termux)

---

## Executive Summary

High-Agent is a unified AI system that combines two powerful ideas:

1. **Mathematical Theory of Code** — A graph-based way to measure and optimize software architecture quality using a single objective score called **Φ(G)**.
2. **Dynamic Regime Architecture** — An AI that intelligently switches between different "thinking modes" (Simple, Advanced, Hybrid) when it detects the current approach is no longer optimal.

The result is an AI that doesn’t just answer questions — it **monitors the quality** of its own reasoning and **adapts its behavior** in real time to produce better outcomes.

---

## The Two Core Ideas

### 1. Mathematical Theory of Code

Any software system (or reasoning process) can be modeled as a **directed graph**:

- **Nodes (V)** = Functions, modules, concepts, or reasoning steps
- **Edges (E)** = Dependencies or relationships between them

Three key metrics are tracked:

| Metric                    | Meaning                                      | Goal          |
|---------------------------|----------------------------------------------|---------------|
| **Q(G)** – Modularity     | How well related things are grouped together | Higher is better |
| **Č(G)** – Coupling       | How tangled the dependencies are             | Lower is better |
| **ΣV** – Cyclomatic Complexity | Total number of branching paths           | Lower is better |

These are combined into one score:

**Φ(G) = α·Q − β·Č − γ·ΣV**

Higher Φ = healthier, cleaner, more maintainable system.

### 2. High-Agent Dynamic Regime System

Instead of using one static AI, you imagined a system that switches between different "regimes" depending on what’s needed. Simple mode for quick local work. Advanced mode for multi-agent verification. Hybrid mode for math-heavy reasoning. And it doesn’t switch randomly — it switches at deviation points. When a signal (quality, coupling, complexity) suddenly spikes or drops, the regime shifts.

---

## The Fusion: One Unified Framework

These two ideas are not separate — they are two sides of the same system.

- The **graph** acts as the system’s "eyes" — it continuously evaluates the current state using Φ(G).
- The **regime engine** acts as the system’s "muscles" — it changes how the AI works when the graph score drops.
- When switching regimes improves Φ(G) by a meaningful amount, the switch happens automatically.

This creates a self-aware, self-optimizing AI that reasons about its own reasoning.

---

## Current Implementation (What’s Actually Running)

You currently have a working Rust implementation on both your laptop and phone:

**Location on Termux (Fold7):**
```bash
~/high-agent/rust/high-agent-rs-termux/
```

**Key Files:**
- `src/main.rs` — Text interface (REPL)
- `src/core.rs` — RegimeEngine + Φ(G) calculation
- `Cargo.toml` — Project configuration

**Commands available in the REPL:**
| Command     | Description                                      |
|-------------|--------------------------------------------------|
| `status`    | Show current regime, Φ(G), Q, Č, ΣV             |
| `s`         | Simulate deviation and force regime switch      |
| `t <task>`  | Process a task (e.g. `t refactor this code`)    |
| `graph`     | View current graph state                        |
| `q`         | Quit                                            |

The binary is ~2MB, runs completely locally, and has no external dependencies beyond Rust.

---

## How to Use It (Termux on Fold7)

```bash
cd ~/high-agent/rust/high-agent-rs-termux
cargo build --release
./target/release/high-agent-rs-termux
```

Once running, try:
- `status`
- `s` (multiple times)
- `t refactor this function to reduce coupling`
- `t explain quantum computing simply`

---

## Use Cases: Asking Questions with High-Agent

### 1. Deep Personal Learning & Research
Ask complex questions and get answers that automatically switch to more rigorous modes when needed.

### 2. High-Quality Coding Assistance
Ask it to write or refactor code while it actively optimizes for modularity and low coupling using your Φ(G) score.

### 3. Self-Improving Knowledge Management
Use it as a personal second brain that not only answers questions but also reorganizes its internal graph when it detects messy reasoning.

### 4. Cross-Device Intelligent Assistant
Ask the same question on your phone or laptop and get consistent behavior because both devices run the same regime engine.

### 5. Technical Troubleshooting & System Administration
Ask complex “why is this broken?” questions. The system can switch into Advanced or Hybrid mode automatically.

### 6. Creative + Technical Work
Ask for design ideas or architecture suggestions while maintaining quality standards.

### 7. Long-term Personal AIOS Foundation
This framework can become the core reasoning layer of a personal AI Operating System.

---

## Why This Matters (Especially for You)

- This is **your** math and **your** architecture running locally on devices you control.
- It bridges theoretical computer science with practical AI engineering.
- It gives you a measurable way to improve both code *and* reasoning quality.
- It works across your laptop and phone/tablet with the same core logic.

---

## Next Steps (Recommended)

1. Add real Ollama integration so the Termux version can call models.
2. Build a richer AIOS-style TUI for the laptop.
3. Create a shared `mathematical-theory-regime` skill for Hermes and other agents.
4. Add automatic task routing between devices via Tailscale.

---

*Document created for Bryant Issiah Morris Jr. — June 2026*
# Architecture — Agent Storm-Swarm

## Overview

Agent Storm-Swarm is a layered AIOS built on one equation:

```
Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
```

Every architectural decision traces back to this objective function. The system
continuously measures Φ(G) on a directed graph model of the codebase and adjusts
agent behavior, regime coefficients, and code structure to maximize it.

## Layers

```
┌─────────────────────────────────────────────────────┐
│  TUI / REPL / Chat Interface                        │  Layer 12-14
├─────────────────────────────────────────────────────┤
│  Agent Swarm (10 types + Orchestrator)              │  Layer 3
├─────────────────────────────────────────────────────┤
│  Neural Agent (NeuralAgent + LLM Client)            │  Layer 4-5
├─────────────────────────────────────────────────────┤
│  Regime Engine (Orchestrator + Detector)            │  Layer 2
├─────────────────────────────────────────────────────┤
│  Mathematical Core (DirectedGraph + Φ(G))           │  Layer 1
└─────────────────────────────────────────────────────┘
```

## Data Flow

```
Codebase → Crawler → DirectedGraph
                         │
                    GraphSnapshot
                         │
              ┌──────────┴──────────┐
              │   Regime Engine     │
              │  α·Q − β·Č − γ·V   │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Agents          TUI           Daemon
      (swarm)      (dashboard)    (state.json)
```

## Key Design Principles

1. **Math is ground truth.** The TUI, agents, and REPL are all consumers of Φ(G).
   They never compute it — they read it from the engine.

2. **Separation of concerns.** The mathematical core (graph.rs/graph.py) has zero
   I/O dependencies. It can run headless, in tests, in CI, on Termux.

3. **Regime hysteresis.** Regime switches require Φ improvement > 0.05 above the
   current regime's score. This prevents thrashing on noisy graphs.

4. **Self-improving loop.** The system measures Φ(G) before and after every change.
   If Φ degrades, the change is rolled back via git.

## Python vs Rust

Both implementations are mathematically identical. Python is the primary runtime
(portable, easy to extend, works on Termux/Android). Rust provides the performance
core for large codebases and the TUI dashboard.

The Python engine is the source of truth for the test suite. The Rust engine is
the source of truth for the TUI and benchmark measurements.

## Graph Model

```
Node {
  id: function name
  module: package/module name
  cyclomatic: McCabe complexity (E − N + 2P)
  quality: 0.0–1.0 score
}

Edge {
  from: caller function id
  to: callee function id
  weight: call_frequency × param_count × shared_state
}

DirectedGraph G = (V, E)
```

## Regime Profiles

| Regime   | α    | β    | γ    | Focus                           |
|----------|------|------|------|---------------------------------|
| Simple   | 0.8  | 0.9  | 0.2  | Minimize coupling. Fast cycles. |
| Advanced | 1.2  | 0.5  | 0.3  | Maximize modularity. PR mode.   |
| Hybrid   | 1.0  | 0.6  | 0.4  | Balance all. Team handoffs.     |

## Agent Types

| Agent          | Optimizes    | Regime Pref |
|----------------|--------------|-------------|
| Orchestrator   | routing      | hybrid      |
| Refactorer     | Č(G) ↓       | advanced    |
| QualityAuditor | V ↓, q ↑     | advanced    |
| TestEngineer   | coverage ↑   | simple      |
| SkillMiner     | skill library | hybrid     |
| GitKeeper      | git ops      | simple      |
| Planner        | Φ strategy   | advanced    |

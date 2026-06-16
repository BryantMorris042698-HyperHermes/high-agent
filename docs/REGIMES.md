# Regime System

## What is a Regime?

A regime is a set of coefficients (α, β, γ) that shifts what Φ(G) optimizes for.

```
Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
```

By changing the coefficients, the same equation produces different rankings of
codebase states. The orchestrator picks the regime that maximizes Φ(G) for the
current graph topology.

## Regime Definitions

### Simple (α=0.8, β=0.9, γ=0.2)

Strong coupling penalty (β=0.9). Weak modularity reward (α=0.8). Minimal
complexity concern (γ=0.2).

**Use when:** Fast iteration. New features. Coupling is the main risk.
The system will aggressively remove cross-module edges to minimize Č(G).

### Advanced (α=1.2, β=0.5, γ=0.3)

Strong modularity reward (α=1.2). Moderate coupling penalty (β=0.5).
Higher complexity concern (γ=0.3).

**Use when:** PR review mode. The codebase has good modularity but complexity
is creeping up. The system rewards clean module boundaries above all else.

### Hybrid (α=1.0, β=0.6, γ=0.4)

Balanced coefficients. No single term dominates.

**Use when:** Team handoffs. The system needs to balance all three concerns
without over-indexing on any one metric. Default regime.

## Regime Switching

The `SegmentedRegimeDetector` uses z-score change-point detection:

1. Maintain a sliding window of the last N snapshots
2. For each new snapshot, compute z-scores of Q, Č, V against window baseline
3. If any |z| > threshold (default 2.0): change-point detected
4. Re-evaluate all 3 regimes against current graph
5. If best regime beats current by hysteresis margin (0.05): switch

This prevents unnecessary switches on normal metric fluctuation while
catching genuine structural changes that warrant re-evaluation.

## Hysteresis

Regime switches require:

```
Φ(best_regime) − Φ(current_regime) > HYSTERESIS_MARGIN (0.05)
```

Without hysteresis, regimes would thrash on every minor perturbation.
The margin ensures each switch provides meaningful improvement.

## History

Every regime transition is logged as a `RegimeTransition`:

```python
RegimeTransition {
  from_: str      # previous regime
  to: str         # new regime
  reason: str     # why the switch occurred
  phi_before: float
  phi_after: float
}
```

The TUI's History tab shows the full transition log with timestamps and
Φ(G) values before/after each switch.

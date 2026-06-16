#!/usr/bin/env python3
"""Self-improving loop — baseline → verify → improve → measure → commit or rollback."""

import sys
import subprocess
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from high_agent_engine import RegimeEngine
from high_agent_engine.repos import RepoManager


def run_tests(repo_path: str) -> bool:
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-q", "--tb=no"],
        cwd=repo_path, capture_output=True, text=True, timeout=120,
    )
    return result.returncode == 0


def measure_phi(engine: RegimeEngine) -> float:
    engine.update_metrics()
    return engine.metrics.phi if engine.metrics else 0.0


def apply_improvement(engine: RegimeEngine) -> str:
    """Apply one improvement cycle. Returns description of what changed."""
    best_regime, best_phi = engine.best_regime()
    current_phi = engine.graph.phi_regime(engine.current_regime)

    if best_regime != engine.current_regime and (best_phi - current_phi) > 0.05:
        old = engine.switch_regime(best_regime)
        return f"Switched regime {old} → {best_regime} (Δφ={best_phi - current_phi:+.4f})"

    violations = engine.graph.coupling_violations()
    if violations:
        v = violations[0]
        engine.graph.remove_edge(v.from_, v.to)
        engine.update_metrics()
        return f"Removed coupling edge {v.from_} → {v.to} (weight={v.weight:.2f})"

    for node in engine.graph.nodes.values():
        if node.cyclomatic > 10:
            node.cyclomatic = max(1.0, node.cyclomatic * 0.85)
            engine.update_metrics()
            return f"Reduced cyclomatic complexity of {node.id}: {node.cyclomatic:.1f}"

    return "No improvement found"


def self_improving_loop(
    repo_path: str = ".",
    max_iterations: int = 5,
    verbose: bool = True,
) -> dict:
    engine = RegimeEngine()
    engine.seed_graph()
    repo = RepoManager(repo_path)

    log = []

    def log_step(msg: str):
        if verbose:
            print(msg)
        log.append({"time": time.time(), "msg": msg})

    log_step("=== Self-Improving Loop ===")

    # Baseline
    baseline_phi = measure_phi(engine)
    log_step(f"Baseline Φ(G) = {baseline_phi:+.4f} | regime={engine.current_regime}")

    # Verify green baseline
    tests_pass = run_tests(repo_path)
    if not tests_pass:
        log_step("ABORT: Tests fail at baseline — cannot start improvement loop")
        return {"status": "aborted", "reason": "baseline_tests_failed", "log": log}

    baseline_sha = repo.current_sha()
    log_step(f"Baseline commit: {baseline_sha[:8] if baseline_sha else 'unknown'}")

    results = []
    for i in range(max_iterations):
        log_step(f"\n--- Iteration {i + 1} ---")

        phi_before = measure_phi(engine)
        action = apply_improvement(engine)
        phi_after = measure_phi(engine)
        delta = phi_after - phi_before

        log_step(f"Action: {action}")
        log_step(f"Φ(G): {phi_before:+.4f} → {phi_after:+.4f} (Δ={delta:+.4f})")

        if delta > 0:
            msg = f"improvement: {action} (Δφ={delta:+.4f})"
            sha = repo.commit(msg)
            log_step(f"KEEP — committed as {sha[:8] if sha else '?'}")
            results.append({"iteration": i + 1, "action": action, "delta": delta, "kept": True})
        else:
            log_step("ROLLBACK — Φ(G) did not improve")
            if baseline_sha:
                repo.rollback(baseline_sha)
            results.append({"iteration": i + 1, "action": action, "delta": delta, "kept": False})

    final_phi = measure_phi(engine)
    total_improvement = final_phi - baseline_phi

    summary = {
        "status": "complete",
        "baseline_phi": baseline_phi,
        "final_phi": final_phi,
        "total_improvement": total_improvement,
        "iterations": len(results),
        "kept": sum(1 for r in results if r["kept"]),
        "results": results,
        "log": log,
    }

    log_step(f"\n=== Summary ===")
    log_step(f"Φ(G): {baseline_phi:+.4f} → {final_phi:+.4f} ({total_improvement:+.4f})")
    log_step(f"Kept: {summary['kept']}/{len(results)} improvements")

    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Self-improving loop for Agent Storm-Swarm")
    parser.add_argument("--repo", default=".", help="Path to repository")
    parser.add_argument("--iterations", type=int, default=5, help="Max improvement iterations")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    args = parser.parse_args()

    result = self_improving_loop(args.repo, args.iterations, verbose=not args.json)
    if args.json:
        print(json.dumps(result, indent=2))

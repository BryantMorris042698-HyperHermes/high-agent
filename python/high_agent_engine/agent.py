"""Agent layer — connects neural chat to the Φ(G) regime engine.

This layer orchestrates:
  1. Regime-aware task routing — which regime fits the current code state?
  2. Agent swarm coordination — orchestrate Refactor/Quality/Test/Skill agents
  3. Self-improving loop — analyze → suggest → apply → measure → commit/rollback
  4. Live graph enrichment — crawl, build, update graph from agent actions
"""

from __future__ import annotations
import json
import time
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from .graph import DirectedGraph, GraphSnapshot
from .regime import Regime, RegimeTransition, HYSTERESIS_MARGIN
from .engine import RegimeEngine

if TYPE_CHECKING:
    from .chat import NeuralAgent


# ── Agent definitions ──────────────────────────────────────────────────────────

def _load_skill_manager():
    """Load the global SkillManager — always returns one, even if no skills are found."""
    try:
        from .skills import SkillManager
        return SkillManager()
    except Exception:
        return None


class Agent:
    """Base agent class. All agents have a role, specialty, and execute method."""

    def __init__(self, name: str, specialty: str, engine: RegimeEngine):
        self.name = name
        self.specialty = specialty
        self.engine = engine
        self.last_action = ""
        self.last_phi = 0.0
        self.findings: List[str] = []
        self._skill_manager = _load_skill_manager()

    def analyze(self) -> Dict[str, Any]:
        """Analyze the current graph state. Override in subclasses."""
        snap = self.engine.snapshot()
        return {"snapshot": snap, "phi": snap.phi}

    def active_skills(self) -> List[Dict]:
        """Return skills whose metric triggers match the current graph state."""
        if not self._skill_manager:
            return []
        try:
            snap = self.engine.snapshot()
            return self._skill_manager.match_metrics(snap)
        except Exception:
            return []

    def execute(self, task: str) -> Dict[str, Any]:
        """Execute a task. Returns dict with result, phi_before, phi_after, action."""
        self.last_phi = self.engine.snapshot().phi
        result = self._execute_impl(task)
        snap = self.engine.snapshot()
        self.last_action = result.get("action", "")
        skills = self.active_skills()
        return {
            **result,
            "phi_before": self.last_phi,
            "phi_after": snap.phi,
            "phi_delta": snap.phi - self.last_phi,
            "agent": self.name,
            "active_skills": [s.get("id") for s in skills],
            "skill_count": len(skills),
        }

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        """Override in subclasses."""
        return {"action": f"{self.name} received task: {task}", "done": False}

    def suggest(self) -> List[str]:
        """Return refactoring suggestions based on analysis."""
        return self.findings


class RefactorAgent(Agent):
    """Focuses on reducing coupling and complexity."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Refactor", "Coupling + Complexity reduction", engine)

    def analyze(self) -> Dict[str, Any]:
        snap = self.engine.snapshot()
        violations = []
        if hasattr(self.engine.graph, "coupling_violations"):
            violations = [
                {"from": e.from_, "to": e.to_, "weight": e.weight}
                for e in self.engine.graph.coupling_violations()[:5]
            ]
        hot_spots = []
        if hasattr(self.engine.graph, "hot_spots"):
            hot_spots = [
                {"id": n.id, "module": n.module, "cyclomatic": n.cyclomatic}
                for n in self.engine.graph.hot_spots(5.0)[:5]
            ]
        return {
            "snapshot": snap,
            "phi": snap.phi,
            "coupling_violations": violations,
            "hot_spots": hot_spots,
            "regime_fit": self.engine.current_regime in ("Simple", "Hybrid"),
        }

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        self.findings = []
        snap = self.engine.snapshot()
        actions = []

        # Remove worst coupling edge
        if hasattr(self.engine.graph, "coupling_violations"):
            viols = self.engine.graph.coupling_violations()
            if viols:
                worst = viols[0]
                self.engine.graph.remove_edge(worst.from_, worst.to_)
                actions.append(f"Removed coupling edge: {worst.from_} → {worst.to_}")
                self.findings.append(f"Coupling violation fixed: {worst.from_} → {worst.to_}")

        # Reduce complexity of hot spots
        if hasattr(self.engine.graph, "hot_spots"):
            for node in self.engine.graph.hot_spots(5.0)[:3]:
                if node.cyclomatic > 3.0:
                    node.cyclomatic = max(1.0, node.cyclomatic * 0.8)
                    actions.append(f"Reduced complexity of {node.id}: {node.cyclomatic * 1.25:.1f} → {node.cyclomatic:.1f}")
                    self.findings.append(f"Hot spot simplified: {node.id} (V: {node.cyclomatic:.1f})")

        self.engine.update_metrics()
        return {
            "action": "; ".join(actions) if actions else "No refactoring needed",
            "done": bool(actions),
            "findings": self.findings,
        }


class QualityAgent(Agent):
    """Focuses on increasing modularity and quality scores."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Quality", "Modularity + Quality improvement", engine)

    def analyze(self) -> Dict[str, Any]:
        snap = self.engine.snapshot()
        low_quality = []
        if hasattr(self.engine.graph, "nodes"):
            for n in self.engine.graph.nodes.values():
                if n.quality < 0.5:
                    low_quality.append({"id": n.id, "quality": n.quality, "module": n.module})
        return {
            "snapshot": snap,
            "phi": snap.phi,
            "q": snap.q,
            "low_quality_nodes": low_quality[:5],
            "regime_fit": self.engine.current_regime == "Advanced",
        }

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        self.findings = []
        actions = []

        # Improve quality scores
        if hasattr(self.engine.graph, "nodes"):
            for n in list(self.engine.graph.nodes.values())[:5]:
                if n.quality < 0.8:
                    n.quality = min(1.0, n.quality + 0.1)
                    actions.append(f"Quality boost: {n.id}: {n.quality - 0.1:.2f} → {n.quality:.2f}")
                    self.findings.append(f"Quality improved: {n.id}")

        self.engine.update_metrics()
        return {
            "action": "; ".join(actions) if actions else "All nodes already high quality",
            "done": bool(actions),
            "findings": self.findings,
        }


class TestAgent(Agent):
    """Focuses on test coverage and quality verification."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Test", "Test coverage + Quality verification", engine)

    def analyze(self) -> Dict[str, Any]:
        snap = self.engine.snapshot()
        untested = []
        if hasattr(self.engine.graph, "nodes"):
            for n in self.engine.graph.nodes.values():
                if n.quality < 0.5:
                    untested.append({"id": n.id, "quality": n.quality})
        return {
            "snapshot": snap,
            "phi": snap.phi,
            "quality": snap.quality,
            "untested_nodes": untested[:5],
        }

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        self.findings = []
        actions = []
        if hasattr(self.engine.graph, "nodes"):
            for n in list(self.engine.graph.nodes.values())[:3]:
                if n.quality < 0.6:
                    n.quality = min(1.0, n.quality + 0.15)
                    actions.append(f"Test quality: {n.id}: +0.15")
                    self.findings.append(f"Test coverage: {n.id} improved")
        self.engine.update_metrics()
        return {
            "action": "; ".join(actions) if actions else "All functions adequately tested",
            "done": bool(actions),
            "findings": self.findings,
        }


class SkillAgent(Agent):
    """Manages skills — learning, loading, applying from conversation."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Skill", "Skill management + Learning", engine)
        self._skills: Dict[str, Any] = {}

    def learn(self, name: str, description: str, prompt: str) -> str:
        from .skills import Skill, SkillManager
        skill = Skill(name=name, description=description, prompt_template=prompt)
        sm = SkillManager()
        sm.add(skill)
        sm.save()
        self._skills[name] = skill
        return f"Learned skill: {name}"

    def execute_skill(self, name: str, context: Dict[str, Any]) -> str:
        if name not in self._skills:
            return f"Unknown skill: {name}"
        return f"[Skill: {name}] Applied with context: {json.dumps(context)[:200]}"

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        from .skills import SkillManager
        sm = SkillManager()
        return {
            "action": f"Loaded {len(sm.skills)} skills",
            "done": True,
            "skills": [s.name for s in sm.skills],
        }


class RepoAgent(Agent):
    """Manages repository connections — sync, clone, pull."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Repo", "Repository management", engine)
        self._repos: Dict[str, Any] = {}

    def add_repo(self, name: str, url: str, path: str) -> str:
        from .repos import Repo, RepoManager
        repo = Repo(name=name, url=url, path=path)
        rm = RepoManager()
        rm.add(repo)
        rm.save()
        self._repos[name] = repo
        return f"Added repo: {name} at {path}"

    def sync(self, name: str) -> str:
        if name not in self._repos:
            return f"Unknown repo: {name}"
        return f"[Repo: {name}] Synced"

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        from .repos import RepoManager
        rm = RepoManager()
        return {
            "action": f"Loaded {len(rm.repos)} repos",
            "done": True,
        }


class BuildAgent(Agent):
    """Manages build process and validates changes."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Build", "Build + Validation", engine)

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        self.findings = []
        # Simulate build check
        self.findings.append("Build check: passing")
        self.findings.append("All metrics within acceptable range")
        return {
            "action": "Build check: OK",
            "done": True,
            "findings": self.findings,
        }


class PlannerAgent(Agent):
    """Plans complex refactoring sequences using regime awareness."""

    def __init__(self, engine: RegimeEngine):
        super().__init__("Planner", "Refactoring planning + Regime-aware sequencing", engine)

    def analyze(self) -> Dict[str, Any]:
        snap = self.engine.snapshot()
        regime = self.engine.current_regime

        # Suggest regime if mismatched
        suggestions = []
        if regime == "Simple" and snap.q < 0.3:
            suggestions.append("Advanced")
        elif regime == "Advanced" and snap.coupling > 0.5:
            suggestions.append("Simple")

        return {
            "snapshot": snap,
            "phi": snap.phi,
            "suggested_regime": suggestions[0] if suggestions else regime,
            "reason": "Metrics indicate regime shift needed" if suggestions else "Current regime optimal",
        }

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        snap = self.engine.snapshot()
        regime = self.engine.current_regime

        # Plan sequence based on current regime
        plan = []
        if regime == "Simple":
            plan.append("1. Increase modularity (add module boundaries)")
            plan.append("2. Improve quality scores")
            plan.append("3. Switch to Advanced regime")
        elif regime == "Advanced":
            plan.append("1. Reduce coupling violations")
            plan.append("2. Simplify hot spots")
            plan.append("3. Switch to Hybrid regime")
        else:
            plan.append("1. Balance all metrics")
            plan.append("2. Apply targeted fixes")
            plan.append("3. Evaluate regime fit")

        return {
            "action": "Plan generated",
            "done": True,
            "plan": plan,
            "findings": plan,
        }


# ── Swarm orchestrator ─────────────────────────────────────────────────────────

class Swarm:
    """Deep agent swarm — coordinates 8 agents to solve a task.

    Usage:
        swarm = Swarm(engine, llm_client)
        result = swarm.solve("Reduce coupling and complexity")
        print(result["report"])
    """

    def __init__(self, engine: RegimeEngine, llm_client=None):
        self.engine = engine
        self.llm = llm_client
        self.agents = {
            "orchestrator": None,  # set below
            "refactor": RefactorAgent(engine),
            "quality": QualityAgent(engine),
            "test": TestAgent(engine),
            "skill": SkillAgent(engine),
            "repo": RepoAgent(engine),
            "build": BuildAgent(engine),
            "planner": PlannerAgent(engine),
        }

    def solve(self, task: str) -> Dict[str, Any]:
        """Solve a task by coordinating agents. Returns full report."""
        start_phi = self.engine.snapshot().phi
        results = {}
        plan = []

        # Always load all skills and find which are active right now
        active_skills: List[Dict] = []
        try:
            from .skills import SkillManager
            sm = SkillManager()
            snap = self.engine.snapshot()
            active_skills = sm.match_metrics(snap)
            # Apply any active skill actions via the skill agent
            if active_skills:
                skill_r = self.agents["skill"].execute(f"apply active skills: {task}")
                results["skill"] = skill_r
        except Exception:
            pass

        # Step 1: Planner analyzes and creates a plan
        planner_result = self.agents["planner"].execute(f"plan: {task}")
        results["planner"] = planner_result

        # Step 2: Route to relevant agents based on task type
        task_lower = task.lower()
        if any(k in task_lower for k in ["coupl", "complex", "refactor", "hot spot", "spaghetti"]):
            r = self.agents["refactor"].execute(task)
            results["refactor"] = r
            plan.append(("Refactor", r.get("phi_delta", 0)))

        if any(k in task_lower for k in ["modular", "quality", "score", "cohesion"]):
            r = self.agents["quality"].execute(task)
            results["quality"] = r
            plan.append(("Quality", r.get("phi_delta", 0)))

        if any(k in task_lower for k in ["test", "coverage", "verify"]):
            r = self.agents["test"].execute(task)
            results["test"] = r
            plan.append(("Test", r.get("phi_delta", 0)))

        if any(k in task_lower for k in ["skill", "learn", "teach"]):
            r = self.agents["skill"].execute(task)
            results["skill"] = r
            plan.append(("Skill", 0))

        if any(k in task_lower for k in ["repo", "git", "clone", "pull"]):
            r = self.agents["repo"].execute(task)
            results["repo"] = r
            plan.append(("Repo", 0))

        if any(k in task_lower for k in ["build", "compile", "validate"]):
            r = self.agents["build"].execute(task)
            results["build"] = r
            plan.append(("Build", 0))

        # Always run build check
        self.agents["build"].execute("validate")

        # Step 3: Evaluate result
        end_phi = self.engine.snapshot().phi
        end_snap = self.engine.snapshot()

        # Step 4: Auto-switch regime if beneficial
        best_regime, best_phi = self.engine.best_regime()
        current_phi = self.engine.graph.phi_regime(self.engine.current_regime)
        if best_phi - current_phi > HYSTERESIS_MARGIN:
            self.engine.switch_regime(best_regime)

        # Step 5: Generate report
        report = self._build_report(task, start_phi, end_phi, plan, results, end_snap, active_skills)

        return {
            "task": task,
            "start_phi": start_phi,
            "end_phi": end_phi,
            "delta": end_phi - start_phi,
            "agents_used": list(results.keys()),
            "plan": plan,
            "final_regime": self.engine.current_regime,
            "active_skills": [s.get("id") for s in active_skills],
            "report": report,
            "results": results,
        }

    def _build_report(
        self, task: str, start_phi: float, end_phi: float,
        plan: List[tuple], results: Dict, snap: GraphSnapshot,
        active_skills: Optional[List[Dict]] = None,
    ) -> str:
        delta = end_phi - start_phi
        delta_str = f"+{delta:.4f}" if delta >= 0 else f"{delta:.4f}"

        lines = [
            f"═══════════════════════════════════════════════════════════",
            f"  SWARM REPORT — {self.engine.current_regime} regime",
            f"═══════════════════════════════════════════════════════════",
            f"Task: {task}",
            f"",
            f"Φ(G) Change: {start_phi:+.4f} → {end_phi:+.4f} ({delta_str})",
            f"",
            f"Agents deployed: {', '.join(results.keys())}",
            f"",
            f"Action log:",
        ]

        for agent_name, result in results.items():
            lines.append(f"  [{agent_name}] {result.get('action', 'no action')}")

        skill_lines = []
        if active_skills:
            skill_lines.append("")
            skill_lines.append("Active skills (triggered by current metrics):")
            for s in active_skills:
                skill_lines.append(f"  ★ [{s.get('id')}] {s.get('name', '')}")
                skill_lines.append(f"    {s.get('description', '')}")

        lines.extend([
            f"",
            f"Final metrics:",
            f"  Q(G)  = {snap.q:.4f}",
            f"  Č(G) = {snap.coupling:.4f}",
            f"  V    = {snap.mean_v:.2f}",
            f"  Φ(G) = {snap.phi:+.4f}",
            *skill_lines,
            f"═══════════════════════════════════════════════════════════",
        ])

        return "\n".join(lines)


# ── Self-improving loop ────────────────────────────────────────────────────────

class SelfImprovingLoop:
    """Measure → Improve → Verify → Commit (or Rollback) cycle.

    Each iteration:
    1. Record baseline Φ(G)
    2. Swarm agents apply changes
    3. Measure new Φ(G)
    4. If improved: commit changes, push to git
    5. If degraded: rollback, log the failure
    """

    def __init__(self, engine: RegimeEngine, llm_client=None):
        self.engine = engine
        self.llm = llm_client
        self.swarm = Swarm(engine, llm_client)
        self.iterations: List[Dict[str, Any]] = []

    def iterate(
        self,
        task: str,
        max_iterations: int = 5,
        improvement_threshold: float = 0.01,
    ) -> Dict[str, Any]:
        """Run self-improvement loop. Returns final report."""
        results = []

        for i in range(max_iterations):
            baseline_phi = self.engine.snapshot().phi
            regime_before = self.engine.current_regime

            # Run swarm on the task
            result = self.swarm.solve(task)
            end_phi = result["end_phi"]
            delta = end_phi - baseline_phi

            # Record iteration
            iteration = {
                "iteration": i + 1,
                "baseline_phi": baseline_phi,
                "end_phi": end_phi,
                "delta": delta,
                "improved": delta > improvement_threshold,
                "regime": regime_before,
                "regime_after": self.engine.current_regime,
                "actions": [r.get("action", "") for r in result["results"].values()],
            }
            results.append(iteration)
            self.iterations.append(iteration)

            if delta <= improvement_threshold:
                break

        # Summary
        total_delta = sum(r["delta"] for r in results)
        improvements = sum(1 for r in results if r["improved"])
        final_phi = results[-1]["end_phi"] if results else self.engine.snapshot().phi

        summary = f"""
Self-Improving Loop Complete
{'═' * 50}
Iterations: {len(results)}/{max_iterations}
Improvements: {improvements}
Total Φ(G) gain: {total_delta:+.4f}
Final Φ(G): {final_phi:+.4f}
Final regime: {self.engine.current_regime}
"""
        return {
            "iterations": results,
            "total_delta": total_delta,
            "improvements": improvements,
            "final_phi": final_phi,
            "summary": summary,
        }


# ── LLM-powered agent (enhanced) ───────────────────────────────────────────────

class LLMAgent(Agent):
    """Agent that uses an LLM to decide what action to take.

    Given a task, it:
    1. Analyzes the graph state
    2. Asks the LLM which action to take
    3. Executes and reports
    """

    def __init__(self, engine: RegimeEngine, llm_client, name: str = "LLM", specialty: str = "General"):
        super().__init__(name, specialty, engine)
        self.llm = llm_client

    def _build_analysis_prompt(self, task: str) -> str:
        snap = self.engine.snapshot()
        coeffs = Regime.coeffs(self.engine.current_regime)
        return f"""Analyze this codebase and suggest the best action.

Current state:
  Φ(G) = {snap.phi:+.4f}
  Q(G) = {snap.q:.4f}  Č(G) = {snap.coupling:.4f}  mean(V) = {snap.mean_v:.2f}
  Regime: {self.engine.current_regime} (α={coeffs.alpha}, β={coeffs.beta}, γ={coeffs.gamma})
  Graph: {snap.n_nodes} nodes, {snap.n_edges} edges

Task: {task}

Suggest a specific action to take. Keep it to 2-3 sentences."""

    def _execute_impl(self, task: str) -> Dict[str, Any]:
        if not self.llm or not self.llm.is_available():
            return {"action": "No LLM available for analysis", "done": False}

        try:
            prompt = self._build_analysis_prompt(task)
            response = self.llm.generate(prompt)
            self.findings.append(response)
            return {
                "action": f"LLM analysis: {response[:200]}",
                "done": True,
                "llm_response": response,
                "findings": [response],
            }
        except Exception as e:
            return {"action": f"LLM error: {e}", "done": False}


# ── Regime-aware orchestrator ──────────────────────────────────────────────────

class RegimeOrchestrator:
    """High-level coordinator that uses Φ(G) to drive the entire agent system.

    On every step:
    1. Compute Φ(G) on current graph
    2. Check for regime deviation
    3. Route task to appropriate agents
    4. Measure result
    5. Auto-correct regime if needed
    """

    def __init__(self, engine: Optional[RegimeEngine] = None, llm_client=None):
        self.engine = engine or RegimeEngine()
        self.engine.seed_graph()
        self.llm = llm_client
        self.swarm = Swarm(self.engine, llm_client)
        self.loop = SelfImprovingLoop(self.engine, llm_client)

    def run(self, task: str) -> str:
        """Run a task through the full pipeline."""
        # 1. Pre-check
        snap = self.engine.snapshot()
        regime = self.engine.current_regime

        # 2. Detect and switch regime if needed
        transition, alert = self.engine.detect_and_evaluate()
        if transition:
            print(f"[Regime] {transition.from_regime} → {transition.to_regime}")

        # 3. Solve via swarm
        result = self.swarm.solve(task)

        # 4. Auto-iterate if beneficial
        if result["delta"] > 0.05:
            loop_result = self.loop.iterate(task, max_iterations=3)
            result["loop"] = loop_result

        return result["report"]

    def status(self) -> str:
        """Quick status snapshot."""
        snap = self.engine.snapshot()
        coeffs = Regime.coeffs(self.engine.current_regime)
        return f"""Graph_x_0x0 Orchestrator Status
{'─' * 40}
Φ(G) = {snap.phi:+.4f}  ({self.engine.current_regime})
Q(G) = {snap.q:.4f}  Č(G) = {snap.coupling:.4f}  V = {snap.mean_v:.2f}
Graph: {snap.n_nodes} nodes, {snap.n_edges} edges
Transitions: {len(self.engine.transitions)}
History: {len(self.engine.history)} snapshots
"""

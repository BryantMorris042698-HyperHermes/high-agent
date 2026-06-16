"""Neural chat interface — AI agent powered by Φ(G) Mathematical Codebase Analysis.

This is the core conversational layer. Every chat message is enriched with:
  - Live Φ(G) graph metrics (Q, Č, V, phi)
  - Current regime and regime transition history
  - Hot spots and coupling violations from the graph
  - Agent suggestions based on regime and metrics

The agent can also:
  - Crawl a codebase and analyze it live
  - Suggest refactors based on architectural signals
  - Switch regimes based on conversation context
  - Execute code changes via skill system
"""

from __future__ import annotations
import json
import os
import re
import textwrap
import time
from typing import Any, Callable, Dict, List, Optional
from .llm import LLMClient, auto_setup, setup_ollama, print_status
from .graph import DirectedGraph, GraphSnapshot
from .regime import Regime
from .engine import RegimeEngine


# ── Agent system prompt ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Graph_x_0x0, an AIOS (Autonomous Intelligent Operating System) for Mobile TUI Deep Agents.

Your core mathematical engine computes Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V) over your codebase graph in real-time.

## What you know about the codebase
{graph_context}

## Current regime: {regime} ({regime_desc})
Coefficients: α={alpha}, β={beta}, γ={gamma}
Regime strategy: {strategy}

## What you can do
1. **Analyze code**: I can crawl any directory, build a graph of functions/modules, and compute live metrics.
2. **Detect architectural problems**: High coupling (Č), complex functions (V), low modularity (Q) are flagged automatically.
3. **Switch regimes**: Based on task context, I can optimize for different goals:
   - Simple: Minimize coupling (fast iteration mode)
   - Advanced: Maximize modularity (PR review mode)
   - Hybrid: Balance all (team handoff mode)
4. **Execute changes**: I can create skills, manage repos, run tests, and apply refactors.
5. **Learn**: I can add new skills from conversation — just ask "learn this approach" and I'll save it.

## Commands
- "crawl <path>" — build graph from a codebase
- "regime" — explain the current regime
- "metrics" — show live Φ(G) numbers
- "history" — show recent regime transitions
- "switch to <Simple|Advanced|Hybrid>" — change regime
- "skills" — list available skills
- "learn <name>: <description>" — save a new skill
- "status" — show LLM and system status

## Response style
- Concise, technical, action-oriented
- Show actual numbers (Φ, Q, Č, V) in every analysis
- Flag specific functions/modules when reporting issues
- Suggest concrete changes with expected Φ(G) impact
"""


def format_graph_context(snap: Optional[GraphSnapshot], engine: RegimeEngine) -> str:
    """Build the graph context block for the system prompt."""
    if snap is None or snap.n_nodes == 0:
        return "No codebase loaded. Use 'crawl <path>' to analyze a codebase."

    hot_spots = []
    if engine.graph and hasattr(engine.graph, "hot_spots"):
        try:
            hot_spots = [n.id for n in engine.graph.hot_spots(5.0)[:5]]
        except Exception:
            pass

    coupling_violations = []
    if engine.graph and hasattr(engine.graph, "coupling_violations"):
        try:
            coupling_violations = len(engine.graph.coupling_violations())
        except Exception:
            pass

    return f"""Loaded codebase graph:
  Nodes: {snap.n_nodes} functions across {snap.n_modules} modules
  Edges: {snap.n_edges} dependencies
  Φ(G) = {snap.phi:+.4f}
  Q(G) = {snap.q:.4f} (modularity — higher = better clustering)
  Č(G) = {snap.coupling:.4f} (coupling — lower = less spaghetti)
  mean(V) = {snap.mean_v:.2f} (cyclomatic complexity)
  Max cyclomatic: {snap.max_v:.2f}

Hot spots (high cyclomatic): {hot_spots or 'None'}
Coupling violations: {coupling_violations} cross-module edges
Regime history: {len(engine.history)} snapshots, {len(engine.transitions)} regime switches
"""


def format_phi_breakdown(snap: GraphSnapshot, regime: str, coeffs) -> str:
    """Build the Φ(G) math block."""
    return f"""Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
        = {coeffs.alpha}·{snap.q:.4f} − {coeffs.beta}·{snap.coupling:.4f} − {coeffs.gamma}·{snap.mean_v:.2f}
        = {coeffs.alpha * snap.q:.4f} − {coeffs.beta * snap.coupling:.4f} − {coeffs.gamma * snap.mean_v:.2f}
        = {snap.phi:+.4f}"""


# ── Conversation turn ─────────────────────────────────────────────────────────

class ChatMessage:
    def __init__(self, role: str, content: str, meta: Optional[Dict[str, Any]] = None):
        self.role = role
        self.content = content
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


# ── Main NeuralAgent ──────────────────────────────────────────────────────────

class NeuralAgent:
    """Conversational AI agent powered by the Φ(G) codebase graph engine.

    Usage:
        agent = NeuralAgent()              # auto-detect LLM (Ollama → API key)
        agent = NeuralAgent(model="gpt-4o", api_key="sk-...")  # OpenAI
        agent = NeuralAgent(model="llama3.2:3b")  # Ollama specific

        # Chat
        resp = agent.chat("Analyze my codebase")
        print(resp)

        # Crawl and analyze
        agent.crawl("/path/to/project")

        # Regime switch
        agent.switch_regime("Advanced")

        # Streaming
        for chunk in agent.chat("Explain the hot spots", stream=True):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
        engine: Optional[RegimeEngine] = None,
        system_override: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.engine = engine or RegimeEngine()
        self.engine.seed_graph()
        self.conversation: List[ChatMessage] = []
        self._llm: Optional[LLMClient] = None
        self._llm_params = dict(
            model=model,
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._system_prompt = system_override
        self._last_snap: Optional[GraphSnapshot] = None
        self._just_switched = False

        # Command handlers
        self._commands = {
            "crawl": self._cmd_crawl,
            "regime": self._cmd_regime,
            "metrics": self._cmd_metrics,
            "phi": self._cmd_phi,
            "theory": self._cmd_theory,
            "history": self._cmd_history,
            "switch": self._cmd_switch,
            "skills": self._cmd_skills,
            "learn": self._cmd_learn,
            "status": self._cmd_status,
            "sweep": self._cmd_sweep,
            "hot": self._cmd_hot_spots,
            "coupling": self._cmd_coupling,
            "refactor": self._cmd_refactor,
            "simulate": self._cmd_simulate,
            "load": self._cmd_load,
            "help": self._cmd_help,
        }

    # ── LLM lazy init ─────────────────────────────────────────────────────

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(**self._llm_params)
        return self._llm

    def reset_llm(self, **kwargs) -> None:
        """Reset LLM with new params."""
        self._llm_params.update(kwargs)
        self._llm = None  # force reinit

    # ── System prompt ──────────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        if self._system_prompt:
            return self._system_prompt

        coeffs = Regime.coeffs(self.engine.current_regime)
        snap = self.engine.snapshot()

        return SYSTEM_PROMPT.format(
            graph_context=format_graph_context(snap, self.engine),
            regime=self.engine.current_regime,
            regime_desc=Regime.description(self.engine.current_regime),
            alpha=coeffs.alpha,
            beta=coeffs.beta,
            gamma=coeffs.gamma,
            strategy=Regime.strategy(self.engine.current_regime),
        )

    # ── Snapshot helpers ──────────────────────────────────────────────────

    def snapshot(self) -> GraphSnapshot:
        snap = self.engine.graph.snapshot_full(self.engine.current_regime)
        self._last_snap = snap
        return snap

    def phi(self) -> Dict[str, float]:
        coeffs = Regime.coeffs(self.engine.current_regime)
        snap = self._last_snap or self.snapshot()
        return {
            "phi": coeffs.alpha * snap.q - coeffs.beta * snap.coupling - coeffs.gamma * snap.mean_v,
            "q": snap.q,
            "coupling": snap.coupling,
            "mean_v": snap.mean_v,
            "regime": self.engine.current_regime,
        }

    # ── Main chat ─────────────────────────────────────────────────────────

    def chat(
        self,
        message: str,
        stream: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a message and get a response. Auto-routes to command or LLM."""
        message = message.strip()
        if not message:
            return "Send me a message to analyze your codebase."

        # Check for built-in commands (prefix with / or keywords)
        cmd_result = self._try_command(message)
        if cmd_result is not None:
            return cmd_result

        # Refresh context
        snap = self.snapshot()
        coeffs = Regime.coeffs(self.engine.current_regime)

        # Update system prompt with fresh metrics
        system = self._build_system_prompt()

        # Build conversation messages
        # Add regime switch context if just switched
        context_note = ""
        if self._just_switched:
            context_note = f"[Note: Regime just switched to {self.engine.current_regime}. Explain the implications.]\n"
            self._just_switched = False

        if context:
            context_note += f"\n[Context: {json.dumps(context)}]\n"

        user_msg = context_note + message
        self.conversation.append(ChatMessage("user", user_msg))

        # Build messages for LLM
        llm_messages = [("system", system)]
        for msg in self.conversation[-10:]:  # sliding window of last 10
            llm_messages.append((msg.role, msg.content))

        try:
            if not self.llm.is_available():
                return self._no_llm_response(message)

            resp = self.llm.chat(llm_messages, stream=stream)

            if stream:
                # Return generator for streaming
                return resp  # type: ignore

            self.conversation.append(ChatMessage("assistant", resp))

            # Auto-detect regime suggestion in response
            suggested_regime = self._extract_regime_suggestion(resp)
            if suggested_regime and suggested_regime != self.engine.current_regime:
                self.engine.switch_regime(suggested_regime)
                self._just_switched = True
                resp += f"\n\n[Auto-switched to {suggested_regime} regime based on analysis.]"

            return resp

        except Exception as e:
            return f"LLM error: {e}\n\n{self._no_llm_response(message)}"

    def _no_llm_response(self, message: str) -> str:
        """Fallback response using live Φ(G) analysis — works without an LLM."""
        snap = self.snapshot()
        coeffs = Regime.coeffs(self.engine.current_regime)

        q_term = coeffs.alpha * snap.q
        c_term = -coeffs.beta * snap.coupling
        v_term = -coeffs.gamma * snap.mean_v

        terms = [
            (q_term, "Q(G)", "modularity is weak — functions cluster poorly across modules"),
            (c_term, "Č(G)", f"coupling is {'very high' if snap.coupling > 0.7 else 'elevated'} — cross-module dependencies dominate"),
            (v_term, "V",    f"cyclomatic complexity is {'high' if snap.mean_v > 10 else 'moderate'} — functions have too many branches"),
        ]
        worst = min(terms, key=lambda x: x[0])
        best_r, best_phi = max(self.engine.sweep_regimes(), key=lambda x: x[1])
        switch_hint = ""
        if best_r != self.engine.current_regime and (best_phi - snap.phi) > 0.01:
            switch_hint = f"\nBest regime: switch {self.engine.current_regime} → {best_r}  (Δ={best_phi - snap.phi:+.4f})"

        hot = []
        try:
            hot = [n.id for n in self.engine.graph.hot_spots(5.0)[:3]]
        except Exception:
            pass

        return textwrap.dedent(f"""\
            Φ(G) = {snap.phi:+.4f}  [{self.engine.current_regime.upper()}]
            ═══════════════════════════════════════
            Φ = α·Q − β·Č − γ·V
              = {coeffs.alpha}·({snap.q:.4f}) − {coeffs.beta}·({snap.coupling:.4f}) − {coeffs.gamma}·({snap.mean_v:.2f})
              = {q_term:+.4f} {c_term:+.4f} {v_term:+.4f}
              = {snap.phi:+.4f}

            Q(G)     = {snap.q:.4f}  (modularity)
            Č(G)     = {snap.coupling:.4f}  (coupling)
            mean(V)  = {snap.mean_v:.2f}   (cyclomatic)

            Dominant constraint: {worst[1]} — {worst[2]}
              Term value: {worst[0]:+.4f}{switch_hint}

            Graph: {snap.n_nodes} nodes · {snap.n_edges} edges · {snap.n_modules} modules{f'{chr(10)}Hot spots: {", ".join(hot)}' if hot else ''}

            ─── To enable AI chat ──────────────────
            Ollama (local, free):
              pkg install ollama   # Termux
              ollama pull llama3.2:3b
            OpenAI:
              export OPENAI_API_KEY=sk-...
            Then: python -m high_agent_engine tui
        """)

    # ── Command routing ───────────────────────────────────────────────────

    def _try_command(self, message: str) -> Optional[str]:
        """Try to match a built-in command. Returns None if not a command."""
        msg_lower = message.lower().strip()

        # Exact commands
        for cmd_name in self._commands:
            patterns = [
                f"/{cmd_name}",
                f"--{cmd_name}",
                f"{cmd_name}:",
                f"{cmd_name} ",
            ]
            for pat in patterns:
                if msg_lower.startswith(pat.lstrip()):
                    return self._commands[cmd_name](message)

        # Keyword shortcuts
        if msg_lower in ("metrics", "phi", "phi(g)"):
            return self._cmd_metrics("")
        if msg_lower in ("status", "llm status"):
            return self._cmd_status("")
        if msg_lower in ("help", "?"):
            return self._cmd_help("")
        if msg_lower in ("history", "transitions"):
            return self._cmd_history("")
        if msg_lower in ("regime", "current regime"):
            return self._cmd_regime("")
        if msg_lower.startswith("crawl "):
            return self._cmd_crawl(message)
        if msg_lower.startswith("switch ") or msg_lower.startswith("switch to "):
            return self._cmd_switch(message)
        if msg_lower.startswith("load "):
            return self._cmd_load(message)
        if msg_lower.startswith("learn "):
            return self._cmd_learn(message)
        if msg_lower in ("sweep", "sweep regimes"):
            return self._cmd_sweep("")
        if msg_lower in ("hot", "hotspots", "hot spots"):
            return self._cmd_hot_spots("")
        if msg_lower in ("coupling", "coupling violations"):
            return self._cmd_coupling("")
        if msg_lower in ("simulate", "simulate deviation"):
            return self._cmd_simulate("")

        return None

    # ── Command implementations ──────────────────────────────────────────

    def _cmd_crawl(self, message: str) -> str:
        """crawl <path> [--recursive]"""
        parts = message.strip().split()
        if len(parts) < 2:
            return "Usage: crawl <path> [--recursive]"
        path = parts[1]
        recursive = "--recursive" in parts or "-r" in parts

        try:
            from .crawler import CodebaseCrawler
            crawler = CodebaseCrawler(recursive=recursive)
            graph = crawler.crawl(path)
            self.engine.graph = graph
            self.engine.seed_graph()
            snap = self.engine.snapshot()
            return f"Crawled {path}: {graph.n_nodes} nodes, {graph.n_edges} edges across {graph.n_modules} modules.\n\nΦ(G) = {snap.phi:+.4f}  regime={self.engine.current_regime}"
        except Exception as e:
            return f"Crawl failed: {e}"

    def _cmd_regime(self, _: str) -> str:
        coeffs = Regime.coeffs(self.engine.current_regime)
        desc = Regime.description(self.engine.current_regime)
        strategy = Regime.strategy(self.engine.current_regime)
        return f"""Current regime: {self.engine.current_regime}
Description: {desc}
Strategy: {strategy}

Coefficients: α={coeffs.alpha}, β={coeffs.beta}, γ={coeffs.gamma}
Task: {Regime.task(self.engine.current_regime)}

Three regimes available:
  Simple   (α=0.8, β=0.9, γ=0.2) — Minimize coupling. Fast iteration.
  Advanced (α=1.2, β=0.5, γ=0.3) — Maximize modularity. PR review mode.
  Hybrid   (α=1.0, β=0.6, γ=0.4) — Balance all. Team handoff mode.
"""

    def _cmd_metrics(self, _: str) -> str:
        snap = self.snapshot()
        coeffs = Regime.coeffs(self.engine.current_regime)
        return f"""Live Metrics (Φ(G) = α·Q − β·Č − γ·mean(V))
───────────────────────────────────────────────
Φ(G)       = {snap.phi:+.4f}
Q(G)       = {snap.q:.4f}  (modularity — higher=better)
Č(G)       = {snap.coupling:.4f}  (coupling — lower=better)
mean(V)    = {snap.mean_v:.2f}  (cyclomatic — lower=better)
max(V)      = {snap.max_v:.2f}

Breakdown:
  α·Q(G)   = {coeffs.alpha * snap.q:+.4f}
  β·Č(G)   = {coeffs.beta * snap.coupling:+.4f}
  γ·mean(V)= {coeffs.gamma * snap.mean_v:+.4f}

Graph: {snap.n_nodes} nodes, {snap.n_edges} edges, {snap.n_modules} modules
Regime: {self.engine.current_regime}  History: {len(self.engine.history)} snapshots
"""

    def _cmd_phi(self, _: str) -> str:
        snap = self.snapshot()
        coeffs = Regime.coeffs(self.engine.current_regime)
        return format_phi_breakdown(snap, self.engine.current_regime, coeffs)

    def _cmd_theory(self, _: str) -> str:
        return self.engine.theory_explain()

    def _cmd_history(self, _: str) -> str:
        if not self.engine.transitions:
            return f"No regime transitions yet. {len(self.engine.history)} snapshots recorded."
        lines = ["Regime Transitions:", ""]
        for i, t in enumerate(self.engine.transitions[-10:]):
            lines.append(f"  {i+1}. {t.from_regime} → {t.to_regime}  Φ: {t.phi_before:+.4f} → {t.phi_after:+.4f}  ({t.reason})")
        return "\n".join(lines)

    def _cmd_switch(self, message: str) -> str:
        target = message.lower().replace("switch", "").replace("switch to", "").strip()
        if target not in ("simple", "advanced", "hybrid"):
            return "Usage: switch <Simple|Advanced|Hybrid>"
        old = self.engine.switch_regime(target)
        snap = self.engine.snapshot()
        self._just_switched = True
        return f"Switched {old} → {target}\n\nΦ(G) = {snap.phi:+.4f}  regime = {target}"

    def _cmd_skills(self, _: str) -> str:
        from .skills import SkillManager
        sm = SkillManager()
        if not sm.skills:
            return "No skills loaded. Add skills with 'learn <name>: <description>'"
        lines = ["Available skills:", ""]
        for s in sm.skills:
            lines.append(f"  • {s.name}: {s.description[:80]}")
        return "\n".join(lines)

    def _cmd_learn(self, message: str) -> str:
        """learn <name>: <description>"""
        parts = message.split(":", 1)
        if len(parts) < 2:
            return "Usage: learn <name>: <description>"
        name = parts[0].replace("learn", "").strip()
        desc = parts[1].strip()
        from .skills import Skill, SkillManager
        sm = SkillManager()
        skill = Skill(name=name, description=desc, prompt_template=f"Apply {name}: {desc}")
        sm.add(skill)
        sm.save()
        return f"Saved skill: {name}\n\n{desc}"

    def _cmd_status(self, _: str) -> str:
        print_status(self._llm)
        snap = self.snapshot()
        avail = self.llm.is_available() if self._llm else False
        return f"""LLM: {'✓ connected' if avail else '✗ not available'}
Provider: {self.llm.provider if avail else 'none'}
Model: {self.llm.model if avail else 'none'}

Graph: {snap.n_nodes} nodes, {snap.n_edges} edges
Φ(G) = {snap.phi:+.4f}  regime = {self.engine.current_regime}
"""

    def _cmd_sweep(self, _: str) -> str:
        results = self.engine.sweep_regimes()
        lines = ["Regime Sweep:", ""]
        lines.append(f"  {'Regime':<10} {'Φ(G)':>10}")
        lines.append("  " + "-" * 22)
        best = max(results, key=lambda x: x[1])
        for regime, phi in sorted(results, key=lambda x: x[1], reverse=True):
            tag = " ← BEST" if regime == best[0] else ""
            cur = " [current]" if regime == self.engine.current_regime else ""
            lines.append(f"  {regime:<10} {phi:>+10.4f}{tag}{cur}")
        return "\n".join(lines)

    def _cmd_hot_spots(self, _: str) -> str:
        if not hasattr(self.engine.graph, "hot_spots"):
            return "Hot spots not available."
        try:
            spots = self.engine.graph.hot_spots(5.0)[:10]
            if not spots:
                return "No hot spots found (all functions below V > 5.0 threshold)."
            lines = ["Hot Spots (high cyclomatic complexity):", ""]
            for n in spots:
                lines.append(f"  • {n.id} (module: {n.module})  V={n.cyclomatic:.1f}")
            return "\n".join(lines)
        except Exception as e:
            return f"Hot spots error: {e}"

    def _cmd_coupling(self, _: str) -> str:
        if not hasattr(self.engine.graph, "coupling_violations"):
            return "Coupling violations not available."
        try:
            viols = self.engine.graph.coupling_violations()
            if not viols:
                return "No coupling violations — all edges are within modules."
            lines = ["Coupling Violations (cross-module edges):", ""]
            for e in viols[:10]:
                lines.append(f"  • {e.from_} → {e.to_} (weight: {e.weight:.2f})")
            if len(viols) > 10:
                lines.append(f"  ... and {len(viols) - 10} more")
            return "\n".join(lines)
        except Exception as e:
            return f"Coupling analysis error: {e}"

    def _cmd_refactor(self, _: str) -> str:
        if not hasattr(self.engine.graph, "coupling_violations"):
            return "Refactor not available."
        try:
            viols = self.engine.graph.coupling_violations()
            if viols:
                e = viols[0]
                self.engine.graph.remove_edge(e.from_, e.to_)
                snap = self.engine.snapshot()
                return f"Removed coupling edge: {e.from_} → {e.to_}\nNew Φ(G) = {snap.phi:+.4f}"
            return "No coupling violations to remove."
        except Exception as e:
            return f"Refactor error: {e}"

    def _cmd_simulate(self, _: str) -> str:
        self.engine.simulate_deviation()
        snap = self.engine.snapshot()
        avail = self.engine.detector is not None
        return f"Simulated deviation.\n\nΦ(G) = {snap.phi:+.4f}  regime = {self.engine.current_regime}\nDeviation detected: {'yes' if avail else 'no'}"

    def _cmd_load(self, message: str) -> str:
        parts = message.strip().split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: load <graph.json>"
        try:
            with open(parts[1]) as f:
                data = f.read()
            self.engine.load_from_json(data)
            snap = self.engine.snapshot()
            return f"Loaded: {snap.n_nodes} nodes, {snap.n_edges} edges\n\nΦ(G) = {snap.phi:+.4f}  regime = {self.engine.current_regime}"
        except Exception as e:
            return f"Load error: {e}"

    def _cmd_help(self, _: str) -> str:
        return textwrap.dedent("""\
            Graph_x_0x0 Neural Chat — Commands
            ─────────────────────────────────
            Natural language: Ask anything about your codebase!
            
            Built-in commands:
              /crawl <path>     Analyze a codebase directory
              /metrics          Show live Φ(G), Q, Č, V numbers
              /phi              Show Φ(G) mathematical breakdown
              /theory           Full Theory Mode explanation
              /regime           Explain current regime
              /sweep            Evaluate all 3 regimes
              /switch <R>       Switch regime: Simple|Advanced|Hybrid
              /history          Show regime transition history
              /hot              Show hot spots (high complexity)
              /coupling         Show coupling violations
              /refactor         Auto-fix worst coupling violation
              /simulate         Simulate a regime deviation
              /load <file>      Load graph from JSON
              /skills           List available skills
              /learn <n>: <d>   Save a new skill
              /status           LLM connection status
              /help             Show this help

            LLM setup:
              agent.setup()     Auto-detect best provider
              agent.setup(model="gpt-4o", api_key="sk-...")  OpenAI
              agent.setup(model="llama3.2:3b")                 Ollama
        """)

    # ── Regime suggestion extraction ─────────────────────────────────────

    def _extract_regime_suggestion(self, response: str) -> Optional[str]:
        """Heuristically extract regime suggestion from LLM response."""
        r = response.lower()
        if "switch to simple" in r or "regime: simple" in r:
            return "simple"
        if "switch to advanced" in r or "regime: advanced" in r or "pr review" in r:
            return "advanced"
        if "switch to hybrid" in r or "regime: hybrid" in r or "balance" in r:
            return "hybrid"
        return None

    # ── Convenience ───────────────────────────────────────────────────────

    def setup(self, **kwargs) -> "NeuralAgent":
        """Reinitialize LLM with new params. Usage: agent.setup(model="gpt-4o", api_key="sk-...")"""
        self._llm_params.update(kwargs)
        self._llm = None
        if self.llm.is_available():
            print(f"[{self.llm.provider}] Connected — {self.llm.model}")
        else:
            print(f"[{self.llm.provider}] Not available — {self.llm.model}")
        return self

    def crawl(self, path: str, recursive: bool = True) -> str:
        """Crawl and analyze a codebase."""
        return self._cmd_crawl(f"crawl {path} --recursive" if recursive else f"crawl {path}")

    def switch(self, regime: str) -> str:
        """Switch to a regime."""
        return self._cmd_switch(f"switch {regime}")

    def run(self) -> None:
        """Interactive REPL loop."""
        print("╔══════════════════════════════════════════════════╗")
        print("║     Graph_x_0x0 — Neural Chat Agent             ║")
        print("║  Type 'exit' or Ctrl+D to quit                  ║")
        print("╚══════════════════════════════════════════════════╝")
        print()

        if not self.llm.is_available():
            print("[!] No LLM available. Commands will still work.")
            print("    Set up: agent.setup(model='llama3.2:3b')  # Ollama")
            print("    Or:     agent.setup(model='gpt-4o', api_key='sk-...')")
            print()

        while True:
            try:
                user_input = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break

            resp = self.chat(user_input)
            print()
            if hasattr(resp, "__iter__") and not isinstance(resp, str):
                for chunk in resp:
                    print(chunk, end="", flush=True)
                print()
            else:
                print(resp)
            print()


# ── CLI chat ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Graph_x_0x0 Neural Chat — AI Agent powered by Φ(G) Analysis"
    )
    parser.add_argument("--model", "-m", default=None, help="Model (e.g. llama3.2:3b, gpt-4o)")
    parser.add_argument("--api-key", "-k", default=None, help="API key for cloud providers")
    parser.add_argument("--provider", "-p", default=None,
                        choices=["openai", "openrouter", "groq", "deepseek", "ollama"])
    parser.add_argument("--base-url", "-u", default=None, help="Custom base URL")
    parser.add_argument("--crawl", "-c", default=None, help="Initial crawl path")
    parser.add_argument("--regime", "-r", default=None,
                        choices=["Simple", "Advanced", "Hybrid"])
    parser.add_argument("--temperature", "-t", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=2048)
    args = parser.parse_args()

    # Build LLM params
    llm_kwargs = {"temperature": args.temperature, "max_tokens": args.max_tokens}
    if args.model:
        llm_kwargs["model"] = args.model
    if args.api_key:
        llm_kwargs["api_key"] = args.api_key
    if args.provider:
        llm_kwargs["provider"] = args.provider
    if args.base_url:
        llm_kwargs["base_url"] = args.base_url

    agent = NeuralAgent(**llm_kwargs)

    # Initial crawl
    if args.crawl:
        print(f"[*] Crawling {args.crawl}...")
        result = agent.crawl(args.crawl)
        print(result)
        print()

    # Initial regime
    if args.regime:
        agent.switch(args.regime)

    # Show status
    print_status(agent._llm)

    # Run REPL
    agent.run()


if __name__ == "__main__":
    main()

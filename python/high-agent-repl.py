#!/usr/bin/env python3
"""Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm.

Standalone REPL (no install needed). Run with:
  python high-agent-repl.py
  python high-agent-repl.py --model gpt-4o --api-key sk-...
  python high-agent-repl.py --model llama3.2:3b
  python high-agent-repl.py --crawl /path/to/codebase
"""

import cmd
import os
import readline
import sys
import textwrap

# ── ANSI colors ────────────────────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
BANNER = f"""{CYAN}
╔═══════════════════════════════════════════════════════════════╗
║              Graph_x_0x0  —  AIOS Deep Agents                ║
║                                                               ║
║  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)                          ║
║  Regime-aware code architecture intelligence                  ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
"""


def color_phi(phi: float) -> str:
    if phi > 0:
        return f"{GREEN}{phi:+.4f}{RESET}"
    if phi > -2:
        return f"{YELLOW}{phi:+.4f}{RESET}"
    return f"{RED}{phi:+.4f}{RESET}"


def color_regime(r: str) -> str:
    colors = {
        "Simple": GREEN,
        "Advanced": CYAN,
        "Hybrid": YELLOW,
        "Balanced": MAGENTA,
        "Performance": RED,
        "Conservative": DIM,
    }
    return f"{colors.get(r, '')}{r}{RESET}"


# ── Banner ─────────────────────────────────────────────────────────────────────

def print_banner():
    print(BANNER)


def print_status_bar(phi: float, regime: str, n_nodes: int, n_edges: int):
    print(f"{DIM}Φ(G)={RESET}{color_phi(phi)}  "
          f"{DIM}regime={RESET}{color_regime(regime)}  "
          f"{DIM}nodes={RESET}{n_nodes}  "
          f"{DIM}edges={RESET}{n_edges}{RESET}")


# ── LLM setup prompt ───────────────────────────────────────────────────────────

def prompt_llm_setup():
    print(f"""
{CYAN}LLM Setup:{RESET}
  1) Ollama (local, free) — requires: curl -fsSL https://ollama.com/install.sh | sh
  2) OpenAI API key      — requires: export OPENAI_API_KEY=sk-...
  3) OpenRouter          — requires: export OPENROUTER_API_KEY=sk-or-...
  4) Skip (use commands only)
""")
    choice = input(f"{BOLD}Choice (1-4) [4]: {RESET}").strip()
    return choice


def auto_setup_llm():
    """Try Ollama first, then API keys."""
    try:
        import requests
    except ImportError:
        return None

    from high_agent_engine.llm import LLMClient, auto_setup
    client = auto_setup()
    if client.is_available():
        print(f"[{client.provider}] Connected — {client.model}")
        return client

    # Try specific API keys
    for env_var, provider in [
        ("OPENAI_API_KEY", "openai"),
        ("OPENROUTER_API_KEY", "openrouter"),
        ("GROQ_API_KEY", "groq"),
    ]:
        if os.getenv(env_var):
            try:
                client = LLMClient(provider=provider)
                if client.is_available():
                    print(f"[{provider}] Connected — {client.model}")
                    return client
            except Exception:
                pass

    print(f"{YELLOW}[!] No LLM provider available. Use 'setup' command to configure.{RESET}")
    return None


# ── Main REPL ──────────────────────────────────────────────────────────────────

class AgentRepl(cmd.Cmd):
    prompt = f"{BOLD}graph_x>{RESET} "
    intro = ""

    def __init__(self, llm_client=None, initial_crawl: str = None, initial_regime: str = None):
        super().__init__()
        self.llm = llm_client
        self.engine = None
        self.neural_agent = None
        self._init_engine()

        if initial_crawl:
            self.do_crawl(initial_crawl)
        if initial_regime:
            self.do_switch(initial_regime)

    def _init_engine(self):
        from high_agent_engine import RegimeEngine
        self.engine = RegimeEngine()
        self.engine.seed_graph()
        self._refresh()

    def _refresh(self):
        self.snap = self.engine.snapshot()
        self.phi = self.engine.compute_phi()
        self.regime = self.engine.current_regime

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _print_metrics(self):
        coeffs = self.engine.regime_coeffs()
        print(f"""
{CYAN}Live Metrics{RESET}  {DIM}(regime: {color_regime(self.regime)}){RESET}
{'─' * 55}
  Φ(G)       = {color_phi(self.phi['phi'])}
  Q(G)       = {self.phi['q']:.4f}  (modularity — higher=better)
  Č(G)       = {self.phi['coupling']:.4f}  (coupling — lower=better)
  mean(V)    = {self.phi['mean_v']:.2f}  (cyclomatic — lower=better)
  max(V)      = {self.snap['max_v']:.2f}
  Graph:     {self.snap['n_nodes']} nodes, {self.snap['n_edges']} edges
  History:   {len(self.engine.history)} snapshots, {len(self.engine.transitions)} transitions

Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)
     = {coeffs.alpha}·{self.phi['q']:.4f} − {coeffs.beta}·{self.phi['coupling']:.4f} − {coeffs.gamma}·{self.phi['mean_v']:.2f}
     = {color_phi(self.phi['phi'])}
""")

    def _print_phi_header(self):
        print(f"\r{color_phi(self.phi['phi'])}  [{color_regime(self.regime)}]  "
              f"Q={self.phi['q']:.3f}  Č={self.phi['coupling']:.3f}  V={self.phi['mean_v']:.1f}  ", end="", flush=True)

    # ── Built-in commands ──────────────────────────────────────────────────

    def do_metrics(self, arg):
        """Show live Φ(G) metrics."""
        self._refresh()
        self._print_metrics()

    def do_phi(self, arg):
        """Show Φ(G) mathematical breakdown."""
        self._refresh()
        self._print_metrics()

    def do_theory(self, arg):
        """Full Theory Mode explanation."""
        self._refresh()
        print(self.engine.theory_explain())

    def do_sweep(self, arg):
        """Evaluate all regimes and show Φ(G) for each."""
        self._refresh()
        results = self.engine.sweep_regimes()
        print(f"\n{CYAN}Regime Sweep:{RESET}")
        print(f"  {'Regime':<12} {'Φ(G)':>10}")
        print("  " + "─" * 24)
        best = max(results, key=lambda x: x[1])
        for regime, phi in sorted(results, key=lambda x: x[1], reverse=True):
            tag = f" {GREEN}← BEST{RESET}" if regime == best[0] else ""
            cur = f" {YELLOW}[current]{RESET}" if regime == self.regime else ""
            print(f"  {regime:<12} {phi:>+10.4f}{tag}{cur}")
        self.engine.switch_regime(best[0])
        self._refresh()

    def do_switch(self, arg):
        """Switch regime: switch <Simple|Advanced|Hybrid>"""
        r = arg.strip()
        valid = ["Simple", "Advanced", "Hybrid"]
        if r not in valid:
            print(f"Choose from: {', '.join(valid)}")
            return
        old = self.engine.switch_regime(r)
        self._refresh()
        print(f"{GREEN}{old} → {r}{RESET}  Φ(G)={color_phi(self.phi['phi'])}")

    def do_history(self, arg):
        """Show metric history: history [n]"""
        n = int(arg) if arg.strip().isdigit() else 10
        entries = self.engine.history[-n:]
        print(f"\n{DIM}Last {len(entries)} snapshots:{RESET}")
        print(f"  {'#':>3}  {'Φ(G)':>10}  {'Q':>8}  {'Č':>8}  {'V':>8}  Regime")
        print("  " + "─" * 58)
        for i, e in enumerate(reversed(entries)):
            print(f"  {len(entries)-i:>3}  {color_phi(e['phi'])}  "
                  f"{e['q']:>8.4f}  {e['coupling']:>8.4f}  {e['mean_v']:>8.2f}  "
                  f"{color_regime(e['regime'])}")

    def do_crawl(self, arg):
        """Crawl a directory: crawl <path> [--recursive|-r]"""
        parts = arg.strip().split()
        if not parts:
            print("Usage: crawl <path> [--recursive|-r]")
            return
        path = parts[0]
        recursive = "--recursive" in parts or "-r" in parts
        print(f"{DIM}Crawling {path}...{RESET}")
        try:
            from high_agent_engine.crawler import CodebaseCrawler
            crawler = CodebaseCrawler(recursive=recursive)
            graph = crawler.crawl(path)
            self.engine.graph = graph
            self.engine.seed_graph()
            self._refresh()
            print(f"{GREEN}✓{RESET} Built: {self.snap['n_nodes']} nodes, {self.snap['n_edges']} edges")
            print(f"   Φ(G)={color_phi(self.phi['phi'])}  [{color_regime(self.regime)}]")
        except Exception as e:
            print(f"{RED}✗{RESET} Crawl failed: {e}")

    def do_load(self, arg):
        """Load graph from JSON: load <path>"""
        if not arg.strip():
            print("Usage: load <path/to/graph.json>")
            return
        try:
            with open(arg.strip()) as f:
                data = f.read()
            self.engine.load_from_json(data)
            self._refresh()
            print(f"{GREEN}✓{RESET} Loaded: {self.snap['n_nodes']} nodes, {self.snap['n_edges']} edges")
        except FileNotFoundError:
            print(f"{RED}✗{RESET} File not found: {arg}")
        except Exception as e:
            print(f"{RED}✗{RESET} Load error: {e}")

    def do_hot(self, arg):
        """Show hot spots (high cyclomatic complexity)."""
        self._refresh()
        if not hasattr(self.engine.graph, "hot_spots"):
            print("hot_spots not available on this graph")
            return
        try:
            spots = self.engine.graph.hot_spots(5.0)[:10]
            if not spots:
                print("No hot spots found (all functions V ≤ 5.0)")
                return
            print(f"\n{CYAN}Hot Spots (V > 5.0):{RESET}")
            for n in spots:
                bar = "█" * min(int(n.cyclomatic), 30)
                print(f"  {n.id:<40} {n.cyclomatic:>5.1f}  {RED}{bar}{RESET}")
        except Exception as e:
            print(f"Error: {e}")

    def do_coupling(self, arg):
        """Show coupling violations (cross-module edges)."""
        self._refresh()
        if not hasattr(self.engine.graph, "coupling_violations"):
            print("coupling_violations not available on this graph")
            return
        try:
            viols = self.engine.graph.coupling_violations()
            if not viols:
                print(f"{GREEN}✓{RESET} No coupling violations")
                return
            print(f"\n{CYAN}Coupling Violations ({len(viols)} total):{RESET}")
            for e in viols[:10]:
                print(f"  {RED}✗{RESET} {e.from_} → {e.to_}  (weight: {e.weight:.2f})")
            if len(viols) > 10:
                print(f"  {DIM}... and {len(viols) - 10} more{RESET}")
        except Exception as e:
            print(f"Error: {e}")

    def do_simulate(self, arg):
        """Simulate regime deviation (for demos)."""
        self.engine.simulate_deviation()
        self._refresh()
        print(f"{YELLOW}~{RESET} Deviation simulated")
        print(f"   Φ(G)={color_phi(self.phi['phi'])}  [{color_regime(self.regime)}]")

    def do_skills(self, arg):
        """List available skills."""
        try:
            from high_agent_engine.skills import SkillManager
            sm = SkillManager()
            if not sm.skills:
                print("No skills yet. Use 'learn <name>: <description>' to add one.")
                return
            print(f"\n{CYAN}Skills ({len(sm.skills)}):{RESET}")
            for s in sm.skills:
                print(f"  • {BOLD}{s.name}{RESET}: {s.description[:70]}")
        except Exception as e:
            print(f"Error: {e}")

    def do_learn(self, arg):
        """Learn a skill: learn <name>: <description>"""
        parts = arg.split(":", 1)
        if len(parts) < 2:
            print("Usage: learn <name>: <description>")
            return
        name = parts[0].strip()
        desc = parts[1].strip()
        if not name:
            print("Name cannot be empty")
            return
        try:
            from high_agent_engine.skills import Skill, SkillManager
            skill = Skill(name=name, description=desc,
                          prompt_template=f"Apply {name}: {desc}")
            sm = SkillManager()
            sm.add(skill)
            sm.save()
            print(f"{GREEN}✓{RESET} Learned: {BOLD}{name}{RESET}")
            print(f"   {desc}")
        except Exception as e:
            print(f"{RED}✗{RESET} Save failed: {e}")

    def do_status(self, arg):
        """Show system status (LLM + graph)."""
        self._refresh()
        print(f"\n{CYAN}System Status{RESET}")
        print(f"  Graph:    {self.snap['n_nodes']} nodes, {self.snap['n_edges']} edges")
        print(f"  Regime:   {color_regime(self.regime)}")
        print(f"  Φ(G):     {color_phi(self.phi['phi'])}")
        print(f"  History:  {len(self.engine.history)} snapshots, {len(self.engine.transitions)} switches")
        if self.llm:
            avail = self.llm.is_available()
            status = f"{GREEN}✓{RESET} available" if avail else f"{RED}✗{RESET} not available"
            print(f"  LLM:      {status} ({self.llm.provider}/{self.llm.model})")
        else:
            print(f"  LLM:      {YELLOW}not configured{RESET} (use 'setup')")

    def do_setup(self, arg):
        """Set up LLM: setup [provider] [model] [api_key]"""
        parts = arg.strip().split(maxsplit=3)
        if not parts:
            self.llm = auto_setup_llm()
            return

        provider = parts[0] if len(parts) > 0 else "openai"
        model = parts[1] if len(parts) > 1 else None
        api_key = parts[2] if len(parts) > 2 else None

        try:
            from high_agent_engine.llm import LLMClient
            kwargs = {"provider": provider}
            if model:
                kwargs["model"] = model
            if api_key:
                kwargs["api_key"] = api_key
            self.llm = LLMClient(**kwargs)
            if self.llm.is_available():
                print(f"[{self.llm.provider}] Connected — {self.llm.model}")
            else:
                print(f"[{self.llm.provider}] Failed to connect")
        except Exception as e:
            print(f"{RED}✗{RESET} Setup failed: {e}")

    # ── Neural chat ────────────────────────────────────────────────────────

    def do_chat(self, arg):
        """Chat with the AI agent: chat <message>"""
        if not arg.strip():
            print("Usage: chat <message>")
            print("  Example: chat Analyze my codebase for coupling issues")
            return

        if not self.llm or not self.llm.is_available():
            print(f"{YELLOW}No LLM available. Use 'setup' to configure.{RESET}")
            return

        print(f"{DIM}Thinking...{RESET}", end="", flush=True)
        try:
            from high_agent_engine.chat import NeuralAgent
            agent = NeuralAgent(engine=self.engine, llm_client=self.llm)
            # Copy conversation from REPL context
            response = agent.chat(arg)
            print(f"\r{' ' * 30}\r", end="")
            print(f"{CYAN}┌─ Agent:{RESET}")
            for line in response.split("\n"):
                print(f"{CYAN}│{RESET} {line}")
            print(f"{CYAN}└{RESET}")
            self._refresh()
        except Exception as e:
            print(f"\r{' ' * 30}\r{RED}✗{RESET} Chat error: {e}")

    def do_swarm(self, arg):
        """Run the agent swarm on a task: swarm <task>"""
        if not arg.strip():
            print("Usage: swarm <task>")
            print("  Example: swarm Reduce coupling and complexity")
            return

        print(f"{DIM}Running swarm...{RESET}")
        try:
            from high_agent_engine.agent import Swarm
            swarm = Swarm(self.engine, self.llm)
            result = swarm.solve(arg)
            print(f"\r{' ' * 25}\r", end="")
            print(result["report"])
            self._refresh()
        except Exception as e:
            print(f"{RED}✗{RESET} Swarm error: {e}")

    def do_refactor(self, arg):
        """Auto-fix worst coupling violation."""
        try:
            from high_agent_engine.agent import RefactorAgent
            agent = RefactorAgent(self.engine)
            result = agent.execute("reduce coupling")
            print(f"Action: {result['action']}")
            print(f"Φ(G): {result['phi_before']:+.4f} → {result['phi_after']:+.4f} "
                  f"({result['phi_delta']:+.4f})")
            self._refresh()
        except Exception as e:
            print(f"Error: {e}")

    # ── Shell passthrough ──────────────────────────────────────────────────

    def do_sh(self, arg):
        """Run a shell command: sh <command>"""
        os.system(arg)

    def do_reload(self, arg):
        """Reload the engine (reset to seed graph)."""
        self._init_engine()
        print(f"{GREEN}✓{RESET} Engine reloaded")

    # ── Override Cmd methods ───────────────────────────────────────────────

    def default(self, line: str):
        """Unhandled input → neural chat."""
        if not line.strip():
            return
        if line.startswith("/") or line.startswith("--"):
            print(f"Unknown command. Type 'help' for available commands.")
            return
        # Treat as chat
        self.do_chat(line)

    def emptyline(self):
        self._refresh()
        self._print_phi_header()

    def do_help(self, arg):
        """Show help."""
        if arg.strip():
            super().do_help(arg)
            return
        print(textwrap.dedent(f"""\
            {CYAN}Graph_x_0x0 Commands{RESET}
            {'─' * 55}
            {BOLD}Metrics:{RESET}
              metrics, phi     — Live Φ(G) breakdown
              theory           — Full Theory Mode explanation
              sweep            — Evaluate all 3 regimes
              history [n]      — Show metric history (last n snapshots)

            {BOLD}Regime:{RESET}
              switch <R>       — Switch regime: Simple|Advanced|Hybrid
              simulate         — Simulate a regime deviation

            {BOLD}Codebase:{RESET}
              crawl <path> [-r]  — Crawl and analyze a directory
              load <file>        — Load graph from JSON
              hot                — Show hot spots (V > 5.0)
              coupling           — Show coupling violations

            {BOLD}Agents:{RESET}
              chat <msg>        — Neural chat with Φ(G)-powered agent
              swarm <task>      — Run deep agent swarm on a task
              refactor          — Auto-fix worst coupling violation
              skills            — List available skills
              learn <n>: <d>    — Save a new skill

            {BOLD}System:{RESET}
              setup [prov] [m] [k] — Configure LLM provider
              status             — Show system + LLM status
              reload             — Reset engine to seed graph
              sh <cmd>           — Run shell command
              quit, exit, Ctrl+D — Exit

            {BOLD}Natural language:{RESET}
              Anything not matching a command is sent to the neural agent.
        """))

    def do_quit(self, arg):
        """Exit."""
        print("Goodbye!")
        return True

    def do_exit(self, arg):
        return self.do_quit(arg)

    def do_EOF(self, arg):
        print("\nGoodbye!")
        return True

    def postloop(self):
        try:
            readline.write_history_file(os.path.expanduser("~/.high-agent/repl_history"))
        except Exception:
            pass


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm"
    )
    parser.add_argument("--model", "-m", default=None, help="Model (e.g. llama3.2:3b, gpt-4o)")
    parser.add_argument("--api-key", "-k", default=None, help="API key")
    parser.add_argument("--provider", "-p", default=None,
                        choices=["openai", "openrouter", "groq", "deepseek", "ollama"])
    parser.add_argument("--crawl", "-c", default=None, help="Initial crawl path")
    parser.add_argument("--regime", "-r", default=None,
                        choices=["Simple", "Advanced", "Hybrid"])
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM auto-setup")
    args = parser.parse_args()

    print_banner()

    # Auto-setup LLM
    llm_client = None
    if not args.no_llm:
        if args.model or args.api_key or args.provider:
            try:
                from high_agent_engine.llm import LLMClient
                kwargs = {}
                if args.model:
                    kwargs["model"] = args.model
                if args.api_key:
                    kwargs["api_key"] = args.api_key
                if args.provider:
                    kwargs["provider"] = args.provider
                llm_client = LLMClient(**kwargs)
                if llm_client.is_available():
                    print(f"[{llm_client.provider}] Connected — {llm_client.model}")
                else:
                    print(f"[{llm_client.provider}] Not available")
                    llm_client = None
            except Exception as e:
                print(f"LLM setup failed: {e}")
        else:
            llm_client = auto_setup_llm()

    repl = AgentRepl(llm_client=llm_client,
                     initial_crawl=args.crawl,
                     initial_regime=args.regime)

    # Print initial state
    repl._refresh()
    print(f"\n{CYAN}Ready.{RESET} Type 'help' or '?' for commands.")
    repl._print_phi_header()
    print()

    # Show hot spots on seed graph
    if hasattr(repl.engine.graph, "hot_spots"):
        spots = repl.engine.graph.hot_spots(3.0)[:3]
        if spots:
            print(f"{DIM}Hot spots: {', '.join(n.id for n in spots)}{RESET}")

    repl.cmdloop()


if __name__ == "__main__":
    main()
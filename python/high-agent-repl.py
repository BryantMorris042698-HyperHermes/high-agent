"""High-Agent REPL — interactive shell with sweep, theory, history, watch, ollama commands."""

from __future__ import annotations
import cmd
import json
import os
import readline
import sys
import time
from high_agent_engine.engine import RegimeEngine
from high_agent_engine.ollama import OllamaClient

HISTORY_FILE = os.path.expanduser("~/.high-agent/repl_history")

class Repl(cmd.Cmd):
    intro = """╔══════════════════════════════════════════════════╗
║     Graph_x_0x0 — AIOS Deep Agents REPL        ║
║  Type 'help' or '?' for commands                ║
╚══════════════════════════════════════════════════╝"""
    prompt = "high-agent> "

    def __init__(self):
        super().__init__()
        self.engine = RegimeEngine()
        self.ollama = OllamaClient()
        self.engine.seed_graph()
        self.watch_mode = False
        self.watch_interval = 5
        try: readline.read_history_file(HISTORY_FILE)
        except: pass

    def do_sweep(self, arg):
        """Evaluate all 3 regimes and show Φ(G) for each."""
        results = self.engine.sweep_regimes()
        print("\nRegime Sweep:")
        print(f"  {'Regime':<10} {'Φ(G)':>10}")
        print("  " + "-" * 22)
        for regime, phi in sorted(results, key=lambda x: x[1], reverse=True):
            marker = " ← BEST" if regime == results[0][0] else ""
            current = " [current]" if regime == self.engine.current_regime else ""
            print(f"  {regime:<10} {phi:>+10.4f}{marker}{current}")
        self.engine.switch_regime(results[0][0])

    def do_theory(self, arg):
        """Show Theory Mode mathematical explanation."""
        print(self.engine.theory_explain())

    def do_history(self, arg):
        """Show recent metric history."""
        n = int(arg) if arg.strip() else 10
        entries = self.engine.history[-n:]
        print(f"\nLast {len(entries)} snapshots:")
        print(f"  {'#':>3}  {'Φ(G)':>10}  {'Q':>8}  {'Č':>8}  {'V':>8}  Regime")
        print("  " + "-" * 60)
        for i, e in enumerate(entries):
            print(f"  {len(entries)-i:>3}  {e['phi']:>+10.4f}  {e['q']:>8.4f}  {e['coupling']:>8.4f}  {e['mean_v']:>8.2f}  {e['regime']}")

    def do_watch(self, arg):
        """Watch mode: continuously display metrics. Ctrl+C to stop."""
        try:
            self.watch_mode = True
            print(f"Watching... Press Ctrl+C to stop.")
            while self.watch_mode:
                self.engine.update_metrics()
                phi = self.engine.metrics.phi
                color = "\033[92m" if phi > 0 else "\033[93m" if phi > -2 else "\033[91m"
                reset = "\033[0m"
                print(f"  Φ(G)={color}{phi:+.4f}{reset}  Q={self.engine.metrics.q:.4f}  Č={self.engine.metrics.coupling:.4f}  V={self.engine.metrics.mean_v:.2f}  [{self.engine.current_regime}]")
                time.sleep(self.watch_interval)
                self.engine.detect_and_evaluate()
        except KeyboardInterrupt:
            self.watch_mode = False
            print("\nStopped watching.")

    def do_task(self, arg):
        """Process a task: refactor|feature|test|complexity"""
        task = arg.strip() if arg.strip() else "refactor"
        if task not in ("refactor", "feature", "test", "complexity"):
            print(f"Unknown task: {task}. Use: refactor, feature, test, complexity")
            return
        before = self.engine.metrics.phi
        self.engine.process_task(task)
        after = self.engine.metrics.phi
        delta = after - before
        print(f"Task '{task}': Φ {before:+.4f} → {after:+.4f} ({delta:+.4f})")

    def do_simulate(self, arg):
        """Run N iterations of deviation simulation (default 5)."""
        n = int(arg) if arg.strip() else 5
        print(f"Running {n} iterations...")
        for i in range(n):
            before = self.engine.metrics.phi
            self.engine.simulate_deviation()
            after = self.engine.metrics.phi
            print(f"  [{i+1}] Φ {before:+.4f} → {after:+.4f} [{self.engine.current_regime}]")

    def do_switch(self, arg):
        """Switch regime: simple|advanced|hybrid"""
        regime = arg.strip()
        if regime not in ("simple", "advanced", "hybrid"):
            print("Usage: switch <simple|advanced|hybrid>")
            return
        old = self.engine.switch_regime(regime)
        print(f"Switched: {old} → {regime}  Φ(G)={self.engine.metrics.phi:+.4f}")

    def do_ollama(self, arg):
        """Ollama commands: status|list|pull <model>|generate <prompt>|chat <msg>"""
        parts = arg.strip().split(None, 1)
        cmd = parts[0] if parts else "status"
        arg1 = parts[1] if len(parts) > 1 else ""

        if cmd == "status":
            available = self.ollama.is_available()
            print(f"Ollama: {'✓ Available' if available else '✗ Not running'}")
            print(f"  Host: {self.ollama.base_url}")
            print(f"  Default model: {self.ollama.default_model}")
            if available:
                models = self.ollama.list_models()
                print(f"  Models: {[m.get('name', '?') for m in models]}")
        elif cmd == "list":
            models = self.ollama.list_models()
            for m in models:
                print(f"  {m.get('name','?')}  {m.get('size',0)/1e6:.1f}MB")
        elif cmd == "pull":
            if not arg1:
                print("Usage: ollama pull <model>")
                return
            print(f"Pulling {arg1}... (this may take a while)")
            self.ollama.pull_model(arg1)
            print("Done.")
        elif cmd == "generate":
            if not arg1:
                print("Usage: ollama generate <prompt>")
                return
            resp = self.ollama.generate(arg1)
            print(resp)
        elif cmd == "chat":
            if not arg1:
                print("Usage: ollama chat <message>")
                return
            resp = self.ollama.chat([("user", arg1)])
            print(resp)
        elif cmd == "analyze":
            result = self.engine.ai_analyze(self.ollama)
            print(result)
        else:
            print(f"Unknown ollama command: {cmd}")

    def do_skill(self, arg):
        """Skill commands: list|search <query>|load <name>"""
        parts = arg.strip().split(None, 1)
        cmd = parts[0] if parts else "list"
        arg1 = parts[1] if len(parts) > 1 else ""
        # Placeholder — actual skill management would import SkillManager
        print(f"[Skill] {cmd} {arg1} — (skill system loaded via Rust core)")

    def do_repo(self, arg):
        """Repo commands: list|add <name> <url>|sync <name>"""
        parts = arg.strip().split(None, 2)
        cmd = parts[0] if parts else "list"
        print(f"[Repo] {cmd} — (repo system loaded via Rust core)")

    def do_build(self, arg):
        """Build commands: detect <path>|build <name>|test <name>"""
        print("[Build] Use: build detect <path> | build <name> | test <name>")

    def do_analyze(self, arg):
        """AI-powered graph analysis via Ollama."""
        if not self.ollama.is_available():
            print("Ollama not available. Start it with: ollama serve")
            return
        result = self.engine.ai_analyze(self.ollama)
        print(result)

    def do_graph(self, arg):
        """Show graph stats."""
        print(f"Graph: {self.engine.graph.n_nodes()} nodes, {self.engine.graph.n_edges()} edges, {len(self.engine.graph.modules())} modules")
        print(f"Modules: {self.engine.graph.modules()}")
        print(f"Hot spots (V>5): {[n.id for n in self.engine.graph.hot_spots(5.0)]}")
        print(f"Coupling violations: {len(self.engine.graph.coupling_violations())}")

    def do_importance(self, arg):
        """Show node importance via PageRank."""
        pr = self.engine.graph.node_importance(20)
        sorted_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)
        print("Node importance (PageRank):")
        for node_id, score in sorted_pr[:10]:
            print(f"  {node_id}: {score:.4f}")

    def do_json(self, arg):
        """Export graph as JSON."""
        print(self.engine.graph.to_json())

    def do_load(self, arg):
        """Load graph from JSON file."""
        if not arg.strip():
            print("Usage: load <json_file>")
            return
        try:
            content = open(arg.strip()).read()
            self.engine.load_from_json(content)
            print(f"Loaded: {self.engine.graph.n_nodes()} nodes, {self.engine.graph.n_edges()} edges")
        except Exception as e:
            print(f"Error: {e}")

    def do_state(self, arg):
        """Write current state to JSON."""
        self.engine.write_state()
        print(f"State written to {self.engine.state_file}")

    def do_quit(self, arg):
        """Exit the REPL."""
        print("Goodbye.")
        try: readline.write_history_file(HISTORY_FILE)
        except: pass
        return True

    def do_exit(self, arg): return self.do_quit(arg)
    def do_EOF(self, arg): return self.do_quit(arg)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--daemon" in args:
        from high_agent_engine.daemon import Daemon
        Daemon(5).start()
    elif "--ollama-pull" in args:
        idx = args.index("--ollama-pull")
        model = args[idx + 1] if idx + 1 < len(args) else "llama3.2:3b"
        client = OllamaClient()
        print(f"Pulling {model}...")
        client.pull_model(model)
        print("Done.")
    else:
        Repl().cmdloop()
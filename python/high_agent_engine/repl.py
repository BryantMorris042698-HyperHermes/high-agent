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
            interval = int(arg) if arg.strip() else 5
        except ValueError:
            print("Usage: watch [interval_seconds]")
            return
        print(f"Watching every {interval}s. Press Ctrl+C to stop.\n")
        try:
            while True:
                self.engine.update()
                snap = self.engine.snapshot()
                phi = self.engine.compute_phi()
                print(f"\rΦ(G)={phi['phi']:+.4f}  Q={phi['q']:.4f}  Č={phi['coupling']:.4f}  V={phi['mean_v']:.2f}  regime={self.engine.current_regime}", end="", flush=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Stopped]")

    def do_ollama(self, arg):
        """Query Ollama for a regime recommendation: ollama <prompt>"""
        if not arg.strip():
            print("Usage: ollama <question about your codebase>")
            return
        print(f"Asking Ollama: {arg[:60]}...")
        resp = self.ollama.chat(arg)
        print(resp)

    def do_load(self, arg):
        """Load a codebase graph from JSON: load <path/to/graph.json>"""
        if not arg.strip():
            print("Usage: load <path/to/graph.json>")
            return
        try:
            self.engine.load_from_json(arg)
            print(f"Loaded: {self.engine.graph.n_nodes} nodes, {self.engine.graph.n_edges} edges")
        except FileNotFoundError:
            print(f"File not found: {arg}")
        except Exception as e:
            print(f"Error loading {arg}: {e}")

    def do_crawl(self, arg):
        """Crawl a directory and build a graph: crawl <path> [--recursive]"""
        parts = arg.strip().split()
        if not parts:
            print("Usage: crawl <path> [--recursive]")
            return
        path = parts[0]
        recursive = "--recursive" in parts or "-r" in parts
        print(f"Crawling {path} (recursive={recursive})...")
        from high_agent_engine.crawler import CodebaseCrawler
        crawler = CodebaseCrawler(recursive=recursive)
        graph = crawler.crawl(path)
        self.engine.graph = graph
        print(f"Built: {graph.n_nodes} nodes, {graph.n_edges} edges")
        self.engine.seed_graph()
        snap = self.engine.snapshot()
        phi = self.engine.compute_phi()
        print(f"Φ(G)={phi['phi']:+.4f}  regime={self.engine.current_regime}")

    def do_stats(self, arg):
        """Show current graph statistics."""
        snap = self.engine.snapshot()
        phi = self.engine.compute_phi()
        print(f"""
Graph Statistics:
  Nodes:        {snap['n_nodes']}
  Edges:        {snap['n_edges']}
  Modularity Q: {snap['q']:.4f}
  Coupling Č:   {snap['coupling']:.4f}
  Mean Cycl:    {snap['mean_v']:.2f}
  Φ(G):         {phi['phi']:+.4f}
  Regime:       {self.engine.current_regime}
  Direction:    {snap.get('direction', 'N/A')}
""")

    def do_switch(self, arg):
        """Switch regime: switch <Simple|Advanced|Hybrid>"""
        r = arg.strip()
        if r not in ("Simple", "Advanced", "Hybrid"):
            print(f"Unknown regime: {r}. Choose: Simple, Advanced, Hybrid")
            return
        self.engine.switch_regime(r)
        phi = self.engine.compute_phi()
        print(f"Switched to {r}. Φ(G)={phi['phi']:+.4f}")

    def do_quit(self, arg):
        """Exit the REPL."""
        print("Goodbye!")
        return True

    def do_exit(self, arg):
        """Exit the REPL."""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """Exit on Ctrl+D."""
        print("\nGoodbye!")
        return True

    def postloop(self):
        try: readline.write_history_file(HISTORY_FILE)
        except: pass

    def emptyline(self):
        pass

def main():
    """Entry point for high-agent-repl CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Graph_x_0x0 — AIOS Deep Agents REPL")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (watch mode)")
    parser.add_argument("--interval", type=int, default=5, help="Watch interval in seconds")
    args = parser.parse_args()

    repl = Repl()
    if args.daemon:
        print("Running in daemon/watch mode. Press Ctrl+C to stop.")
        try:
            while True:
                repl.engine.update()
                snap = repl.engine.snapshot()
                phi = repl.engine.compute_phi()
                print(f"\rΦ(G)={phi['phi']:+.4f}  Q={phi['q']:.4f}  Č={phi['coupling']:.4f}  V={phi['mean_v']:.2f}  regime={repl.engine.current_regime}", end="", flush=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n[Daemon stopped]")
    else:
        repl.cmdloop()

if __name__ == "__main__":
    main()

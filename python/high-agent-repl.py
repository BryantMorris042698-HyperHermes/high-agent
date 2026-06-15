#!/usr/bin/env python3
"""Graph_x_0x0 REPL — run this directly: python high-agent-repl.py"""

import cmd, os, readline, sys, time

# Add parent dir to path so we can import high_agent_engine
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from high_agent_engine.engine import RegimeEngine
from high_agent_engine.ollama import OllamaClient
from high_agent_engine.crawler import CodebaseCrawler

HISTORY_FILE = os.path.expanduser("~/.high-agent/repl_history")

BANNER = """╔══════════════════════════════════════════════════╗
║     Graph_x_0x0 — AIOS Deep Agents REPL        ║
║  Type 'help' or '?' for commands                ║
╚══════════════════════════════════════════════════╝"""


class Repl(cmd.Cmd):
    prompt = "high-agent> "

    def __init__(self):
        super().__init__()
        self.engine = RegimeEngine()
        self.ollama = OllamaClient()
        self.engine.seed_graph()
        try:
            readline.read_history_file(HISTORY_FILE)
        except:
            pass

    # ── Commands ───────────────────────────────────────────

    def do_help(self, arg):
        """Show this help."""
        print(BANNER)
        print("""
Commands:
  sweep          Evaluate all 3 regimes, show Φ(G) for each
  theory         Show Theory Mode mathematical explanation
  stats          Show current graph statistics
  history [N]    Show last N snapshots (default 10)
  switch <R>     Switch regime: Simple | Advanced | Hybrid
  crawl <path>   Crawl a directory and build graph
  load <file>    Load graph from JSON file
  ollama <q>     Ask Ollama for regime recommendation
  watch [sec]    Watch mode (default 5s interval)
  quit / exit    Exit REPL

Keybindings:
  Ctrl+D         Exit
  Ctrl+C         Stop watch mode
""")

    def do_sweep(self, arg):
        """sweep — evaluate all 3 regimes, show Φ(G) for each"""
        results = self.engine.sweep_regimes()
        print("\nRegime Sweep:")
        print(f"  {'Regime':<10} {'Φ(G)':>10}")
        print("  " + "-" * 22)
        best = max(results, key=lambda x: x[1])
        for regime, phi in sorted(results, key=lambda x: x[1], reverse=True):
            tag = " ← BEST" if regime == best[0] else ""
            cur = " [current]" if regime == self.engine.current_regime else ""
            print(f"  {regime:<10} {phi:>+10.4f}{tag}{cur}")

    def do_theory(self, arg):
        """theory — show Theory Mode explanation"""
        print(self.engine.theory_explain())

    def do_stats(self, arg):
        """stats — show current graph statistics"""
        snap = self.engine.snapshot()
        phi = self.engine.compute_phi()
        print(f"""
  Nodes:        {snap['n_nodes']}
  Edges:        {snap['n_edges']}
  Modularity Q: {snap['q']:.4f}
  Coupling Č:   {snap['coupling']:.4f}
  Mean Cycl:    {snap['mean_v']:.2f}
  Φ(G):         {phi['phi']:+.4f}
  Regime:       {self.engine.current_regime}
  Direction:    {snap.get('direction', 'N/A')}
""")

    def do_history(self, arg):
        """history [N] — show last N snapshots"""
        n = int(arg) if arg.strip() else 10
        entries = self.engine.history[-n:]
        print(f"\nLast {len(entries)} snapshots:")
        print(f"  {'#':>3}  {'Φ(G)':>10}  {'Q':>8}  {'Č':>8}  {'V':>8}  Regime")
        print("  " + "-" * 55)
        for i, e in enumerate(entries):
            print(f"  {i+1:>3}  {e['phi']:>+10.4f}  {e['q']:>8.4f}  {e['coupling']:>8.4f}  {e['mean_v']:>8.2f}  {e['regime']}")

    def do_switch(self, arg):
        """switch <Simple|Advanced|Hybrid>"""
        r = arg.strip()
        if r not in ("Simple", "Advanced", "Hybrid"):
            print("Usage: switch Simple | Advanced | Hybrid")
            return
        self.engine.switch_regime(r)
        phi = self.engine.compute_phi()
        print(f"Switched to {r}.  Φ(G)={phi['phi']:+.4f}")

    def do_crawl(self, arg):
        """crawl <path> — crawl a directory and build graph"""
        if not arg.strip():
            print("Usage: crawl <path>")
            return
        print(f"Crawling {arg}...")
        crawler = CodebaseCrawler(recursive=True)
        graph = crawler.crawl(arg)
        self.engine.graph = graph
        print(f"Built: {graph.n_nodes} nodes, {graph.n_edges} edges")
        snap = self.engine.snapshot()
        phi = self.engine.compute_phi()
        print(f"Φ(G)={phi['phi']:+.4f}  regime={self.engine.current_regime}")

    def do_load(self, arg):
        """load <file.json> — load graph from JSON"""
        if not arg.strip():
            print("Usage: load <file.json>")
            return
        try:
            self.engine.load_from_json(arg)
            print(f"Loaded: {self.engine.graph.n_nodes} nodes, {self.engine.graph.n_edges} edges")
        except Exception as e:
            print(f"Error: {e}")

    def do_ollama(self, arg):
        """ollama <question> — ask Ollama for recommendation"""
        if not arg.strip():
            print("Usage: ollama <question>")
            return
        print(f"→ Ollama: {arg[:60]}...")
        resp = self.ollama.chat(arg)
        print(resp)

    def do_watch(self, arg):
        """watch [sec] — watch mode, Ctrl+C to stop"""
        try:
            interval = int(arg) if arg.strip() else 5
        except ValueError:
            interval = 5
        print(f"Watch mode every {interval}s. Press Ctrl+C to stop.\n")
        try:
            while True:
                self.engine.update()
                snap = self.engine.snapshot()
                phi = self.engine.compute_phi()
                print(f"\rΦ(G)={phi['phi']:+.4f}  Q={phi['q']:.4f}  "
                      f"Č={phi['coupling']:.4f}  V={phi['mean_v']:.2f}  "
                      f"regime={self.engine.current_regime}", end="", flush=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[Stopped]")

    def do_quit(self, arg):
        """quit — exit REPL"""
        print("Goodbye!")
        return True

    def do_exit(self, arg):
        """exit — exit REPL"""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """Ctrl+D"""
        print("\nGoodbye!")
        return True

    def emptyline(self):
        pass

    def postloop(self):
        try:
            readline.write_history_file(HISTORY_FILE)
        except:
            pass


if __name__ == "__main__":
    print(BANNER)
    Repl().cmdloop()

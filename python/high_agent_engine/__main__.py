"""high-agent CLI entry point: python -m high_agent_engine"""

import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description="Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm\n"
                    "Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)"
    )
    parser.add_argument("command", nargs="?", default="repl",
                        choices=["repl", "crawl", "daemon", "stats", "version"],
                        help="Command to run (default: repl)")
    parser.add_argument("path", nargs="?", help="Path to crawl or load")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursive crawl")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch mode")
    parser.add_argument("--interval", type=int, default=5, help="Watch interval (seconds)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.command == "version":
        print("high-agent v0.1.0")
        print("Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm")
        return

    from high_agent_engine.engine import RegimeEngine
    engine = RegimeEngine()
    engine.seed_graph()

    if args.command == "crawl" and args.path:
        from high_agent_engine.crawler import CodebaseCrawler
        crawler = CodebaseCrawler(recursive=args.recursive)
        graph = crawler.crawl(args.path)
        engine.graph = graph
        snap = engine.snapshot()
        phi = engine.compute_phi()
        if args.json:
            import json
            print(json.dumps({**snap, **phi}, indent=2))
        else:
            print(f"Crawled: {graph.n_nodes} nodes, {graph.n_edges} edges")
            print(f"Φ(G)={phi['phi']:+.4f}  regime={engine.current_regime}")

    elif args.command in ("repl", "daemon"):
        from high_agent_engine.repl import Repl
        repl = Repl()
        if args.command == "daemon" or args.watch:
            print(f"Watch mode every {args.interval}s. Ctrl+C to stop.\n")
            import time
            try:
                while True:
                    repl.engine.update()
                    snap = repl.engine.snapshot()
                    phi = repl.engine.compute_phi()
                    marker = " ← SWITCHED" if repl.engine.just_switched else ""
                    print(f"\rΦ(G)={phi['phi']:+.4f}  Q={phi['q']:.4f}  Č={phi['coupling']:.4f}  "
                          f"V={phi['mean_v']:.2f}  regime={repl.engine.current_regime}{marker}",
                          end="", flush=True)
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n[Stopped]")
        else:
            print("Starting REPL. Type 'help' for commands.\n")
            repl.cmdloop()

    elif args.command == "stats":
        snap = engine.snapshot()
        phi = engine.compute_phi()
        if args.json:
            import json
            print(json.dumps({**snap, **phi}, indent=2))
        else:
            print(f"""
Graph Statistics:
  Nodes:        {snap['n_nodes']}
  Edges:        {snap['n_edges']}
  Modularity Q: {snap['q']:.4f}
  Coupling Č:   {snap['coupling']:.4f}
  Mean Cycl:    {snap['mean_v']:.2f}
  Φ(G):         {phi['phi']:+.4f}
  Regime:       {engine.current_regime}
  Direction:    {snap.get('direction', 'N/A')}
""")

if __name__ == "__main__":
    main()

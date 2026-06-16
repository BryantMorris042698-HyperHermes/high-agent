"""high_agent_engine.__main__ — CLI entry point.

Usage:
  python -m high_agent_engine
  python -m high_agent_engine --crawl /path/to/codebase
  python -m high_agent_engine chat "Analyze my codebase"
  python -m high_agent_engine swarm "Reduce coupling"
  python -m high_agent_engine --model gpt-4o --api-key sk-... chat "Explain the hot spots"
"""

from __future__ import annotations
import argparse
import sys

from high_agent_engine import RegimeEngine
from high_agent_engine.crawler import CodebaseCrawler


def cmd_metrics(engine: RegimeEngine):
    snap = engine.snapshot()
    phi = engine.compute_phi()
    coeffs = engine.regime_coeffs()
    print(f"""Graph Metrics
{'─' * 50}
Φ(G)       = {phi['phi']:+.4f}
Q(G)       = {phi['q']:.4f}
Č(G)       = {phi['coupling']:.4f}
mean(V)    = {phi['mean_v']:.2f}
max(V)      = {snap['max_v']:.2f}
Graph:     {snap['n_nodes']} nodes, {snap['n_edges']} edges, {snap['n_modules']} modules
Regime:    {engine.current_regime} (α={coeffs.alpha}, β={coeffs.beta}, γ={coeffs.gamma})
History:   {len(engine.history)} snapshots, {len(engine.transitions)} regime switches
""")


def cmd_sweep(engine: RegimeEngine):
    results = engine.sweep_regimes()
    print("\nRegime Sweep:")
    print(f"  {'Regime':<12} {'Φ(G)':>10}")
    print("  " + "-" * 24)
    best = max(results, key=lambda x: x[1])
    for regime, phi in sorted(results, key=lambda x: x[1], reverse=True):
        tag = " ← BEST" if regime == best[0] else ""
        cur = " [current]" if regime == engine.current_regime else ""
        print(f"  {regime:<12} {phi:>+10.4f}{tag}{cur}")
    print()


def cmd_theory(engine: RegimeEngine):
    print(engine.theory_explain())


def cmd_crawl(path: str, recursive: bool = True):
    print(f"Crawling {path} (recursive={recursive})...")
    crawler = CodebaseCrawler(recursive=recursive)
    graph = crawler.crawl(path)
    engine = RegimeEngine()
    engine.graph = graph
    engine.seed_graph()
    snap = engine.snapshot()
    phi = engine.compute_phi()
    print(f"Built: {graph.n_nodes} nodes, {graph.n_edges} edges")
    print(f"Φ(G)={phi['phi']:+.4f}  regime={engine.current_regime}")


def cmd_chat(message: str, model: str = None, api_key: str = None, provider: str = None):
    try:
        from high_agent_engine.llm import LLMClient, auto_setup
    except ImportError:
        print("LLM support requires 'requests'. Install with: pip install high-agent[ollama]")
        sys.exit(1)

    llm_kwargs = {}
    if model:
        llm_kwargs["model"] = model
    if api_key:
        llm_kwargs["api_key"] = api_key
    if provider:
        llm_kwargs["provider"] = provider

    if llm_kwargs:
        llm = LLMClient(**llm_kwargs)
    else:
        llm = auto_setup()

    if not llm.is_available():
        print(f"No LLM provider available ({llm.provider}/{llm.model})")
        print("Set up with: python -m high_agent_engine setup --model <model> --api-key <key>")
        sys.exit(1)

    from high_agent_engine.chat import NeuralAgent
    agent = NeuralAgent(llm_client=llm)
    print(agent.chat(message))


def cmd_swarm(task: str, model: str = None, api_key: str = None):
    engine = RegimeEngine()
    engine.seed_graph()

    llm = None
    if model or api_key:
        try:
            from high_agent_engine.llm import LLMClient
            kwargs = {}
            if model:
                kwargs["model"] = model
            if api_key:
                kwargs["api_key"] = api_key
            llm = LLMClient(**kwargs)
        except ImportError:
            pass

    from high_agent_engine.agent import Swarm
    swarm = Swarm(engine, llm)
    result = swarm.solve(task)
    print(result["report"])


def cmd_status(model: str = None, api_key: str = None, provider: str = None):
    from high_agent_engine.llm import print_status
    print_status()

    engine = RegimeEngine()
    engine.seed_graph()
    snap = engine.snapshot()
    phi = engine.compute_phi()
    print(f"\nEngine: {snap['n_nodes']} nodes, {snap['n_edges']} edges")
    print(f"Φ(G)={phi['phi']:+.4f}  regime={engine.current_regime}")


def cmd_setup(model: str = None, api_key: str = None, provider: str = None):
    try:
        from high_agent_engine.llm import LLMClient, print_status
    except ImportError:
        print("LLM support requires 'requests'. Install with: pip install high-agent[ollama]")
        sys.exit(1)

    kwargs = {}
    if model:
        kwargs["model"] = model
    if api_key:
        kwargs["api_key"] = api_key
    if provider:
        kwargs["provider"] = provider

    if not kwargs:
        print_status()
        return

    client = LLMClient(**kwargs)
    if client.is_available():
        print(f"[{client.provider}] Connected — {client.model}")
    else:
        print(f"[{client.provider}] Not available with {client.model}")
        print(f"  Check your API key or try: pip install high-agent[ollama]")


def main():
    parser = argparse.ArgumentParser(
        description="Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m high_agent_engine                    # Interactive REPL
  python -m high_agent_engine metrics            # Show live metrics
  python -m high_agent_engine sweep              # Evaluate all regimes
  python -m high_agent_engine theory             # Full math explanation
  python -m high_agent_engine crawl ./src        # Crawl and analyze
  python -m high_agent_engine chat "..."         # Neural chat
  python -m high_agent_engine swarm "..."        # Run agent swarm
  python -m high_agent_engine status             # System + LLM status
  python -m high_agent_engine setup -m gpt-4o -k sk-...  # Configure LLM

With chat/swarm, pass --model and --api-key for cloud LLMs,
or just use Ollama (auto-detected).
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("tui",     help="Chat-first ANSI TUI dashboard (default)")
    subparsers.add_parser("metrics", help="Show live Φ(G) metrics")
    subparsers.add_parser("sweep", help="Evaluate all 3 regimes")
    subparsers.add_parser("theory", help="Full Theory Mode explanation")
    subparsers.add_parser("status", help="System + LLM status")

    crawl_p = subparsers.add_parser("crawl", help="Crawl and analyze a codebase")
    crawl_p.add_argument("path", help="Directory to crawl")
    crawl_p.add_argument("--no-recursive", action="store_true", help="Disable recursive crawl")

    chat_p = subparsers.add_parser("chat", help="Neural chat with the agent")
    chat_p.add_argument("message", help="Message to send to the agent")
    chat_p.add_argument("--model", "-m", default=None)
    chat_p.add_argument("--api-key", "-k", default=None)
    chat_p.add_argument("--provider", "-p", default=None,
                        choices=["openai", "openrouter", "groq", "deepseek", "ollama"])

    swarm_p = subparsers.add_parser("swarm", help="Run agent swarm on a task")
    swarm_p.add_argument("task", help="Task for the swarm")
    swarm_p.add_argument("--model", "-m", default=None)
    swarm_p.add_argument("--api-key", "-k", default=None)

    setup_p = subparsers.add_parser("setup", help="Configure LLM provider")
    setup_p.add_argument("--model", "-m", default=None)
    setup_p.add_argument("--api-key", "-k", default=None)
    setup_p.add_argument("--provider", "-p", default=None,
                         choices=["openai", "openrouter", "groq", "deepseek", "ollama"])

    args = parser.parse_args()

    # Default: run the TUI
    if args.command is None or args.command == "tui":
        try:
            from high_agent_engine.tui import run_tui
            run_tui()
        except Exception as e:
            print(f"TUI unavailable ({e}), falling back to REPL.")
            from high_agent_engine.repl import main as repl_main
            repl_main()
        return

    engine = RegimeEngine()
    engine.seed_graph()

    if args.command == "metrics":
        cmd_metrics(engine)
    elif args.command == "sweep":
        cmd_sweep(engine)
    elif args.command == "theory":
        cmd_theory(engine)
    elif args.command == "crawl":
        cmd_crawl(args.path, recursive=not args.no_recursive)
    elif args.command == "chat":
        cmd_chat(args.message, args.model, args.api_key, args.provider)
    elif args.command == "swarm":
        cmd_swarm(args.task, args.model, args.api_key)
    elif args.command == "status":
        cmd_status(args.model, args.api_key, args.provider)
    elif args.command == "setup":
        cmd_setup(args.model, args.api_key, args.provider)


if __name__ == "__main__":
    main()
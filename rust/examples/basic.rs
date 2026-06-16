//! Graph_x_0x0 — Basic usage example
//!
//! Demonstrates the full Graph_x_0x0 engine: graph construction,
//! Φ(G) computation, regime evaluation, regime switching, deviation
//! detection, and Ollama integration.
//!
//! Run with:  cargo run --example basic --features tui
//! Or (CLI only, no TUI deps):  cargo run --example basic

use high_agent::{
    DirectedGraph, Edge, EdgeType, GraphSnapshot, Node,
    Metrics, Orchestrator,
    Regime, RegimeEngine, RegimeTransition, TaskType,
    OllamaClient,
};

fn main() {
    println!("=== Graph_x_0x0 — Basic Example ===\n");

    // ── 1. Build a graph ──────────────────────────────────────────────────────
    println!("1. Building code graph (7 modules, 8 edges)…");

    let mut g = DirectedGraph::new();

    // Core module
    g.add_node(Node::new("orchestrate".into(), "core".into(), "core.rs".into())
        .with_cyclomatic(4.0).with_quality(0.85).with_lines(180));
    g.add_node(Node::new("evaluate".into(), "core".into(), "core.rs".into())
        .with_cyclomatic(3.0).with_quality(0.90).with_lines(120));
    g.add_node(Node::new("detect".into(), "core".into(), "core.rs".into())
        .with_cyclomatic(5.0).with_quality(0.80).with_lines(95));

    // CLI module
    g.add_node(Node::new("handle_command".into(), "cli".into(), "cli.rs".into())
        .with_cyclomatic(2.0).with_quality(0.82).with_lines(60));
    g.add_node(Node::new("parse_args".into(), "cli".into(), "cli.rs".into())
        .with_cyclomatic(2.0).with_quality(0.91).with_lines(40));

    // Skills module
    g.add_node(Node::new("load_skill".into(), "skills".into(), "skills.rs".into())
        .with_cyclomatic(4.0).with_quality(0.87).with_lines(150));
    g.add_node(Node::new("create_skill".into(), "skills".into(), "skills.rs".into())
        .with_cyclomatic(3.0).with_quality(0.83).with_lines(200));

    // Intra-module edges (good — low coupling)
    g.add_edge(Edge::new("orchestrate".into(), "evaluate".into())
        .with_weight(1.0).with_type(EdgeType::Call));
    g.add_edge(Edge::new("evaluate".into(), "detect".into())
        .with_weight(0.9).with_type(EdgeType::Call));
    g.add_edge(Edge::new("detect".into(), "orchestrate".into())
        .with_weight(0.8).with_type(EdgeType::Call));

    // Cross-module edges (some coupling — realistic)
    g.add_edge(Edge::new("handle_command".into(), "orchestrate".into())
        .with_weight(1.0).with_type(EdgeType::Call));
    g.add_edge(Edge::new("handle_command".into(), "parse_args".into())
        .with_weight(1.0).with_type(EdgeType::Call));
    g.add_edge(Edge::new("load_skill".into(), "evaluate".into())
        .with_weight(0.7).with_type(EdgeType::Call));
    g.add_edge(Edge::new("create_skill".into(), "load_skill".into())
        .with_weight(0.6).with_type(EdgeType::Call));
    g.add_edge(Edge::new("handle_command".into(), "load_skill".into())
        .with_weight(0.5).with_type(EdgeType::Import));

    println!("   Nodes: {}, Edges: {}", g.n_nodes(), g.n_edges());

    // ── 2. Compute metrics ─────────────────────────────────────────────────────
    println!("\n2. Computing metrics…");

    let q = g.modularity();
    let coupling = g.mean_coupling();
    let mean_v = g.mean_cyclomatic();

    println!("   Q(G):      {:>7.4}  (modularity — higher = better cohesion)", q);
    println!("   C(G):      {:>7.4}  (coupling   — lower = less spaghetti)", coupling);
    println!("   mean(V):   {:>7.2}  (cyclomatic complexity)", mean_v);

    // ── 3. Compute Φ(G) for all 3 regimes ─────────────────────────────────────
    println!("\n3. Φ(G) across all regimes…");
    println!("   Φ(G) = alpha*Q(G) - beta*C(G) - gamma*mean(V)");
    println!("   ──────────────────────────────────────────────");

    for regime in Regime::all() {
        let coeffs = regime.coeffs();
        let phi = g.phi_regime(regime);
        println!("   {:8}  alpha={:.1} beta={:.1} gamma={:.1}  -> Phi = {:+.4}",
                 regime, coeffs.alpha, coeffs.beta, coeffs.gamma, phi);
    }

    // ── 4. RegimeEngine ────────────────────────────────────────────────────────
    println!("\n4. RegimeEngine (orchestrated regime switching)…");

    let mut engine = RegimeEngine::new();
    engine.seed_graph();
    engine.update_metrics();

    let m = &engine.metrics;
    println!("   Regime:  {}", m.regime);
    println!("   Phi:     {:+.4}", m.phi);
    println!("   Q:       {:.4}  C: {:.4}  mean(V): {:.2}", m.q, m.coupling, m.mean_v);

    // ── 5. Sweep all regimes ───────────────────────────────────────────────────
    println!("\n5. Sweeping all regimes…");

    let results = engine.sweep_regimes();
    for (regime, phi) in &results {
        let marker = if regime == &engine.orchestrator.current_regime { " <-- current" } else { "" };
        println!("   {:8}: Phi = {:+.4}{}", regime, phi, marker);
    }

    // ── 6. Regime switch demo ─────────────────────────────────────────────────
    println!("\n6. Manual regime switch…");

    for regime in Regime::all() {
        if regime != engine.orchestrator.current_regime {
            let old = engine.orchestrator.current_regime;
            let new_regime = engine.switch_regime(regime);
            println!("   Switched: {} -> {}", old, new_regime);
            println!("   New Phi:  {:+.4}", engine.metrics.phi);
            break;
        }
    }

    // ── 7. Task processing ───────────────────────────────────────────────────
    println!("\n7. Processing tasks (refactor / feature / test)…");

    for task in [TaskType::Refactor, TaskType::Feature, TaskType::Test] {
        let phi_before = engine.metrics.phi;
        engine.process_task(task);
        let phi_after = engine.metrics.phi;
        let delta = phi_after - phi_before;
        println!("   {:25}  Phi: {:+.4} -> {:+.4}  (delta: {:+.4})",
                 format!("{:?}", task), phi_before, phi_after, delta);
    }

    // ── 8. Deviation detection ────────────────────────────────────────────────
    println!("\n8. Simulating deviation + auto-switch…");
    engine.simulate_deviation_and_switch();
    println!("   Current regime after demo: {}", engine.orchestrator.current_regime);

    // ── 9. Theory explanation ─────────────────────────────────────────────────
    println!("\n9. Theory Mode explanation (first 400 chars)…");
    let theory = engine.theory_explain();
    let preview = &theory[..theory.len().min(400)];
    println!("   {}", preview.replace('\n', "\n   "));

    // ── 10. Ollama integration ───────────────────────────────────────────────
    println!("\n10. Ollama client (non-blocking — tries to connect)…");
    let client = OllamaClient::new("http://localhost:11434", "llama3.2:1b");
    println!("    Base URL:  {}", client.base_url);
    println!("    Model:     {}", client.default_model);
    println!("    (Use OLLAMA_HOST env var to override base URL)");

    // ── Done ──────────────────────────────────────────────────────────────────
    println!("\n=== Done ===");
}

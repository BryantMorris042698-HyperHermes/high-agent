use high_agent::{RegimeEngine, Regime, TaskType};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        print_usage();
        return;
    }

    match args[1].as_str() {
        "seed" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            println!("Graph seeded: {} nodes, {} edges",
                engine.graph.n_nodes(), engine.graph.n_edges());
            println!("Φ(G) = {:+.4}  Regime: {}", engine.metrics.phi, engine.orchestrator.current_regime);
        }
        "eval" | "evaluate" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            let results = engine.sweep_regimes();
            println!("Regime evaluation:");
            for (regime, phi) in &results {
                let marker = if *regime == engine.orchestrator.current_regime { " ← current" } else { "" };
                println!("  {}: Φ={:+.4}{}", regime, phi, marker);
            }
        }
        "theory" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            println!("{}", engine.theory_explain());
        }
        "switch" => {
            if args.len() < 3 { eprintln!("Usage: high-agent-rs switch <simple|advanced|hybrid>"); return; }
            let regime = Regime::from_str(&args[2]).expect("Invalid regime");
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            let old = engine.switch_regime(regime);
            println!("Switched: {} → {}", old, regime);
            println!("Φ(G) = {:+.4}", engine.metrics.phi);
        }
        "task" => {
            if args.len() < 3 { eprintln!("Usage: high-agent-rs task <refactor|feature|test|complexity>"); return; }
            let task = match args[2].as_str() {
                "refactor" => TaskType::Refactor,
                "feature" => TaskType::Feature,
                "test" => TaskType::Test,
                "complexity" => TaskType::ComplexityReduction,
                _ => { eprintln!("Unknown task: {}", args[2]); return; }
            };
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            let phi_before = engine.metrics.phi;
            engine.process_task(task);
            let phi_after = engine.metrics.phi;
            println!("Task processed: {} → {}", old_regime_str(engine.orchestrator.current_regime), regime_str(engine.orchestrator.current_regime));
            println!("Φ(G): {:+.4} → {:+.4} ({:+.4})", phi_before, phi_after, phi_after - phi_before);
        }
        "simulate" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            for i in 0..5 {
                println!("\n--- Iteration {} ---", i + 1);
                engine.simulate_deviation_and_switch();
                engine.update_metrics();
                println!("Φ(G) = {:+.4}  Regime: {}", engine.metrics.phi, engine.orchestrator.current_regime);
            }
        }
        "load" => {
            if args.len() < 3 { eprintln!("Usage: high-agent-rs load <json_file>"); return; }
            let content = std::fs::read_to_string(&args[2]).expect("Failed to read file");
            let mut engine = RegimeEngine::new();
            engine.load_from_json(&content).expect("Failed to parse JSON");
            engine.update_metrics();
            println!("Loaded: {} nodes, {} edges", engine.graph.n_nodes(), engine.graph.n_edges());
            println!("Φ(G) = {:+.4}  Regime: {}", engine.metrics.phi, engine.orchestrator.current_regime);
        }
        "state" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            engine.write_state().expect("Failed to write state");
            println!("State written to ~/.high-agent/state.json");
        }
        "detect" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            let (transition, alert) = engine.detect_and_switch();
            if let Some(t) = transition {
                println!("Regime transition: {} → {}", t.from, t.to);
                println!("Reason: {}", t.reason);
                println!("Φ: {:+.4} → {:+.4}", t.phi_before, t.phi_after);
            } else if let Some(a) = alert {
                println!("Deviation detected: {:?}", a.direction);
                println!("z-scores: Q={:.2}, Č={:.2}, V={:.2}", a.z_q, a.z_coupling, a.z_v);
            } else {
                println!("No deviation, regime stays: {}", engine.orchestrator.current_regime);
            }
        }
        "hotspots" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            let threshold = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(5.0);
            let spots = engine.hot_spots(threshold);
            if spots.is_empty() {
                println!("No hot spots above threshold {}", threshold);
            } else {
                println!("Hot spots (V > {}):", threshold);
                for n in spots {
                    println!("  {} ({}:{}) V={:.1}, q={:.2}", n.id, n.module, n.file, n.cyclomatic, n.quality);
                }
            }
        }
        "coupling" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            let violations = engine.coupling_violations();
            println!("Coupling violations ({}):", violations.len());
            for e in violations {
                println!("  {} → {}", e.from, e.to);
            }
        }
        "importance" => {
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            engine.update_metrics();
            let pr = engine.node_importance();
            let mut sorted: Vec<_> = pr.iter().collect();
            sorted.sort_by(|a, b| b.1.partial_cmp(a.1).unwrap());
            println!("Node importance (PageRank):");
            for (id, score) in sorted.iter().take(10) {
                println!("  {}: {:.4}", id, score);
            }
        }
        "daemon" => {
            println!("Daemon mode — writing state every 5s. Press Ctrl+C to stop.");
            let mut engine = RegimeEngine::new();
            engine.seed_graph();
            let mut counter = 0;
            loop {
                engine.update_metrics();
                engine.write_state().ok();
                counter += 1;
                println!("[{}] Φ(G)={:+.4} regime={}", counter, engine.metrics.phi, engine.orchestrator.current_regime);
                std::thread::sleep(std::time::Duration::from_secs(5));
                // Simulate some changes
                if counter % 3 == 0 { engine.process_task(TaskType::Refactor); }
                else if counter % 5 == 0 { engine.process_task(TaskType::Test); }
                let (t, _) = engine.detect_and_switch();
                if t.is_some() {
                    println!("  Regime switched!");
                }
            }
        }
        _ => { print_usage(); }
    }
}

fn print_usage() {
    eprintln!("Graph_x_0x0 — AIOS for Mobile TUI Deep Agents
Usage: high-agent-rs <command> [args]

Commands:
  seed         Seed the graph with default nodes
  eval         Evaluate all 3 regimes against current graph
  theory       Show Theory Mode explanation
  switch       Switch regime: simple|advanced|hybrid
  task         Process a task: refactor|feature|test|complexity
  simulate     Run 5 iterations of deviation simulation
  load <file>  Load graph from JSON file
  state        Write current state to ~/.high-agent/state.json
  detect       Run deviation detection
  hotspots [n] Show nodes with cyclomatic > n (default 5)
  coupling     Show cross-module coupling violations
  importance   Show node importance via PageRank
  daemon       Run in daemon mode (writes state every 5s)
");
}

fn regime_str(r: Regime) -> &'static str {
    match r { Regime::Simple => "Simple", Regime::Advanced => "Advanced", Regime::Hybrid => "Hybrid" }
}

fn old_regime_str(r: Regime) -> &'static str { regime_str(r) }
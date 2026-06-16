//! Core engine — RegimeEngine wrapping graph + orchestrator + skills + repos.

use crate::error::{HighAgentError, Result};
use crate::graph::{DirectedGraph, GraphSnapshot, Node, Edge, EdgeType};
use crate::metrics::{Metrics, History};
use crate::ollama::{OllamaClient, ModelInfo};
use crate::orchestrator::Orchestrator;
use crate::regime::Regime;
use crate::skills::SkillManager;
use crate::repos::RepoManager;
use crate::build::{BuildManager, BuildResult};
use crate::agent::{Agent, AgentId, AgentRole};
use crate::swarm::Swarm;
use parking_lot::RwLock;
use std::sync::Arc;

pub struct RegimeEngine {
    pub graph: DirectedGraph,
    pub orchestrator: Orchestrator,
    pub metrics: Metrics,
    pub history: History,
    pub ollama: OllamaClient,
    pub skills: SkillManager,
    pub repos: RepoManager,
    pub builds: BuildManager,
    pub swarm: Swarm,
    pub state_file: String,
    pub codebase_name: String,
}

impl RegimeEngine {
    pub fn new() -> Self {
        Self {
            graph: DirectedGraph::new(),
            orchestrator: Orchestrator::new(),
            metrics: Metrics::default(),
            history: History::new(),
            ollama: OllamaClient::default(),
            skills: SkillManager::new(),
            repos: RepoManager::new(),
            builds: BuildManager::new(),
            swarm: Swarm::new(),
            state_file: "~/.high-agent/state.json".into(),
            codebase_name: "default".into(),
        }
    }

    /// Seed with a starter graph (7 nodes, 8 edges across core/cli/skills modules).
    pub fn seed_graph(&mut self) {
        let modules = [
            ("core", "src/core.rs"),
            ("cli", "src/cli.rs"),
            ("skills", "src/skills.rs"),
            ("graph", "src/graph.rs"),
            ("orchestrator", "src/orchestrator.rs"),
            ("ollama", "src/ollama.rs"),
            ("build", "src/build.rs"),
        ];

        for (module, file) in modules {
            self.graph.add_node(
                Node::new(format!("fn_{}", module), module.into(), file.into())
                    .with_cyclomatic(2.0 + (rand_simple() * 4.0))
                    .with_quality(0.6 + (rand_simple() * 0.35))
                    .with_lines(50 + (rand_simple() * 200.0) as u32)
            );
        }

        // Intra-module edges (good — within same module)
        self.graph.add_edge(Edge::new("fn_core".into(), "fn_graph".into()).with_weight(1.0).with_type(EdgeType::Call));
        self.graph.add_edge(Edge::new("fn_orchestrator".into(), "fn_core".into()).with_weight(1.0).with_type(EdgeType::Call));
        self.graph.add_edge(Edge::new("fn_orchestrator".into(), "fn_graph".into()).with_weight(0.8).with_type(EdgeType::Call));
        self.graph.add_edge(Edge::new("fn_skills".into(), "fn_core".into()).with_weight(0.7).with_type(EdgeType::Call));

        // Cross-module edges (mixed — some coupling)
        self.graph.add_edge(Edge::new("fn_cli".into(), "fn_core".into()).with_weight(1.0).with_type(EdgeType::Call));
        self.graph.add_edge(Edge::new("fn_ollama".into(), "fn_core".into()).with_weight(0.9).with_type(EdgeType::Call));
        self.graph.add_edge(Edge::new("fn_build".into(), "fn_graph".into()).with_weight(0.6).with_type(EdgeType::Call));
        self.graph.add_edge(Edge::new("fn_cli".into(), "fn_skills".into()).with_weight(0.5).with_type(EdgeType::Import));

        self.update_metrics();
    }

    /// Update metrics from current graph state.
    pub fn update_metrics(&mut self) {
        let snapshot = self.graph.snapshot_full(self.orchestrator.current_regime);
        self.metrics = Metrics::from_snapshot(&snapshot, self.orchestrator.current_regime);
        self.history.push_snapshot(&self.metrics);
    }

    /// Evaluate all regimes and pick the best one.
    pub fn sweep_regimes(&self) -> Vec<(Regime, f64)> {
        Regime::all().iter().map(|r| (*r, self.graph.phi_regime(*r))).collect()
    }

    /// Force a regime switch (for user commands).
    pub fn switch_regime(&mut self, regime: Regime) -> Regime {
        let old = self.orchestrator.current_regime;
        self.orchestrator.set_regime(regime);
        self.update_metrics();
        let transition = crate::regime::RegimeTransition::new(
            old, regime, "Manual switch requested", self.graph.phi_regime(old), self.graph.phi_regime(regime),
        );
        self.history.push_transition(transition);
        regime
    }

    /// Detect deviation and auto-switch regimes.
    pub fn detect_and_switch(&mut self) -> (Option<crate::regime::RegimeTransition>, Option<crate::graph::DeviationAlert>) {
        let result = self.orchestrator.detect_and_switch(&self.graph);
        self.update_metrics();
        if let Some(ref t) = result.0 {
            self.history.push_transition(t.clone());
        }
        result
    }

    /// Process a task — perturbs the graph based on task type.
    pub fn process_task(&mut self, task: TaskType) {
        match task {
            TaskType::Refactor => {
                // Simulate refactoring: reduce coupling by removing a cross-module edge
                let violations: Vec<_> = self.graph.coupling_violations();
                if let Some(e) = violations.first() {
                    let (from, to) = (e.from.clone(), e.to.clone());
                    self.graph.remove_edge(&from, &to);
                }
            }
            TaskType::Feature => {
                // Simulate adding a feature: new node, new edges
                let id = format!("fn_feature_{}", self.graph.n_nodes());
                self.graph.add_node(
                    Node::new(id, "features".into(), "features/mod.rs".into())
                        .with_cyclomatic(3.0).with_quality(0.7)
                );
            }
            TaskType::Test => {
                // Simulate test coverage improving quality
                for node in self.graph.nodes.values_mut() {
                    node.quality = (node.quality + 0.05).min(1.0);
                }
            }
            TaskType::ComplexityReduction => {
                // Reduce cyclomatic complexity
                for node in self.graph.nodes.values_mut() {
                    node.cyclomatic = (node.cyclomatic * 0.9).max(1.0);
                }
            }
        }
        self.update_metrics();
    }

    /// Simulate deviation and regime switch for demos.
    pub fn simulate_deviation_and_switch(&mut self) {
        // Perturb the graph to simulate code changes
        let perturbation = match self.orchestrator.current_regime {
            Regime::Simple => {
                // Push toward more modularity
                for node in self.graph.nodes.values_mut() {
                    node.quality = (node.quality + 0.05).min(1.0);
                }
                "Quality boost"
            }
            Regime::Advanced => {
                // Push toward less coupling
                let violations: Vec<_> = self.graph.coupling_violations();
                if violations.len() > 1 {
                    if let Some(e) = violations.get(1) {
                        let (from, to) = (e.from.clone(), e.to.clone());
                        self.graph.remove_edge(&from, &to);
                    }
                }
                "Coupling reduction"
            }
            Regime::Hybrid => {
                // Balanced perturbation
                for node in self.graph.nodes.values_mut() {
                    node.cyclomatic = (node.cyclomatic * 0.95).max(1.0);
                }
                "Cyclomatic reduction"
            }
        };

        let phi_before = self.metrics.phi;
        self.update_metrics();
        let (transition, _alert) = self.detect_and_switch();
        let phi_after = self.metrics.phi;

        if let Some(t) = transition {
            eprintln!("[Demo] {} → regime switch: {} → {} (Φ: {:+.4} → {:+.4})",
                perturbation, t.from, t.to, phi_before, phi_after);
        } else {
            eprintln!("[Demo] {} → Φ: {:+.4} → {:+.4} (no regime change)",
                perturbation, phi_before, phi_after);
        }
    }

    /// Generate Theory Mode explanation.
    pub fn theory_explain(&self) -> String {
        let coeffs = self.orchestrator.current_regime.coeffs();
        let snapshot = self.graph.snapshot_full(self.orchestrator.current_regime);
        let regime_desc = self.orchestrator.current_regime.description();

        format!(r#"═══════════════════════════════════════════════════════════
              THEORY MODE — Mathematical Foundation
═══════════════════════════════════════════════════════════

OBJECTIVE FUNCTION:  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)

WHERE:
  G = (V, E)  —  Codebase as directed graph
  V = {{nn}} —  Functions / methods
  E = {{ne}} —  Calls / imports / inherits
  G has {nn} nodes and {ne} edges

CURRENT REGIME: {regime} ({desc})

COEFFICIENTS (this regime):
  α = {alpha}   (modularity weight, positive)
  β = {beta}    (coupling weight, negative)
  γ = {gamma}   (cyclomatic weight, negative)

LIVE METRICS:
  Φ(G)  = {phi:+10.4}
  Q(G)  = {q:10.4}  (modularity, higher = better cohesion)
  Č(G)  = {coup:10.4}  (mean coupling, lower = less spaghetti)
  mean(V) = {mv:10.4}  (cyclomatic, lower = simpler)

COMPONENT BREAKDOWN:
  α·Q(G)  = {alpha} × {q:10.4} = {aq:+.4}
  β·Č(G)  = {beta} × {coup:10.4} = {bc:+.4}
  γ·mean(V) = {gamma} × {mv:10.4} = {gmv:+.4}

  ─────────────────────────────────
  Φ(G) = {aq:+.4} − {bc:+.4} − {gmv:+.4} = {phi:+10.4}

REGIME INTERPRETATION:
  Regime is optimizing for: {desc}
  Current graph has {nn} nodes across {nm} modules with {ne} edges.

═══════════════════════════════════════════════════════════"#,
            regime = self.orchestrator.current_regime,
            desc = regime_desc,
            alpha = coeffs.alpha, beta = coeffs.beta, gamma = coeffs.gamma,
            phi = snapshot.phi, q = snapshot.q, coup = snapshot.coupling, mv = snapshot.mean_v,
            nn = snapshot.n_nodes, nm = snapshot.n_modules, ne = snapshot.n_edges,
            aq = coeffs.alpha * snapshot.q,
            bc = coeffs.beta * snapshot.coupling,
            gmv = coeffs.gamma * snapshot.mean_v,
        )
    }

    /// Load a graph from JSON.
    pub fn load_from_json(&mut self, json: &str) -> Result<()> {
        self.graph = DirectedGraph::from_json(json)?;
        self.update_metrics();
        Ok(())
    }

    /// Write current state to JSON file.
    pub fn write_state(&self) -> Result<()> {
        let path = self.state_file.replace('~', &std::env::var("HOME").unwrap_or_default());
        self.metrics.write_state(&path)?;
        Ok(())
    }

    /// Get current regime.
    pub fn current_regime(&self) -> Regime { self.orchestrator.current_regime }

    /// Hot spots (high cyclomatic complexity).
    pub fn hot_spots(&self, threshold: f64) -> Vec<&Node> { self.graph.hot_spots(threshold) }

    /// Coupling violations.
    pub fn coupling_violations(&self) -> Vec<&Edge> { self.graph.coupling_violations() }

    /// Node importance (PageRank).
    pub fn node_importance(&self) -> ahash::AHashMap<String, f64> {
        self.graph.node_importance(20)
    }

    // ─── Ollama integration ──────────────────────────────────────────────

    /// Check Ollama availability.
    pub async fn check_ollama(&self) -> bool {
        self.ollama.is_available().await
    }

    /// List available models.
    pub async fn list_models(&self) -> std::result::Result<Vec<ModelInfo>, HighAgentError> {
        self.ollama.list_models().await
    }

    /// Pull a model.
    pub async fn pull_model(&self, model: &str) -> std::result::Result<(), HighAgentError> {
        self.ollama.pull_model(model).await
    }

    /// Generate text with Ollama.
    pub async fn generate(&self, prompt: &str, model: Option<&str>) -> std::result::Result<String, HighAgentError> {
        self.ollama.generate(prompt, model).await
    }

    /// Chat with Ollama.
    pub async fn chat(&self, messages: Vec<(String, String)>, model: Option<&str>) -> std::result::Result<String, HighAgentError> {
        self.ollama.chat(messages, model).await
    }

    /// Ask Ollama to analyze the graph and suggest improvements.
    pub async fn ai_analyze(&self) -> std::result::Result<String, HighAgentError> {
        let prompt = format!(
            "Analyze this codebase graph for architectural issues:\n\
            Nodes: {} functions across {} modules\n\
            Edges: {} dependencies\n\
            Metrics: Φ={:.4}, Q={:.4}, Č={:.4}, V={:.4}\n\
            Regime: {}\n\
            Hot spots (high complexity): {:?}\n\
            Coupling violations: {} cross-module edges\n\n\
            Provide specific refactoring suggestions based on the graph structure.",
            self.metrics.n_nodes, self.metrics.n_modules, self.metrics.n_edges,
            self.metrics.phi, self.metrics.q, self.metrics.coupling, self.metrics.mean_v,
            self.orchestrator.current_regime,
            self.hot_spots(5.0).iter().map(|n| n.id.as_str()).collect::<Vec<_>>(),
            self.graph.coupling_violations().len()
        );
        self.generate(&prompt, None).await
    }
}

impl Default for RegimeEngine {
    fn default() -> Self { Self::new() }
}

#[derive(Debug, Clone, Copy)]
pub enum TaskType {
    Refactor,
    Feature,
    Test,
    ComplexityReduction,
}

// Simple pseudo-random for seeding
fn rand_simple() -> f64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    let nanos = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().subsec_nanos();
    (nanos as f64 % 1000.0) / 1000.0
}
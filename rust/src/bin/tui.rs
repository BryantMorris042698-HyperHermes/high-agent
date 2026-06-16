//! Graph_x_0x0 TUI — 6-tab dashboard with live chat + 8-agent build swarm, built on ratatui 0.29.

#![allow(unused)]

use high_agent::{
    DirectedGraph, GraphSnapshot, Metrics, History, HistoryEntry,
    OllamaClient, ModelInfo, SkillManager, RepoManager, BuildManager,
    Regime, RegimeCoeffs, RegimeTransition,
    BuildType, EdgeType,
};
use ratatui::{
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Style, Stylize},
    text::{Line, Span},
    widgets::{Block, BorderType, Borders, List, ListItem, Paragraph, Wrap, Clear},
    Frame,
};
use crossterm::event::{KeyCode, KeyEventKind};
use std::time::{Duration, Instant};
use std::collections::HashMap;

// ─── Palette (Catppuccin Mocha) ──────────────────────────────────────────────

mod palette {
    use ratatui::style::Color;
    use high_agent::Regime;
    pub const BASE: Color = Color::Rgb(30, 30, 46);
    pub const SURFACE: Color = Color::Rgb(49, 50, 68);
    pub const SURFACE0: Color = Color::Rgb(88, 91, 112);
    pub const SURFACE1: Color = Color::Rgb(98, 102, 124);
    pub const SURFACE2: Color = Color::Rgb(108, 113, 136);
    pub const OVERLAY: Color = Color::Rgb(69, 71, 90);
    pub const SUBTEXT: Color = Color::Rgb(166, 173, 200);
    pub const TEXT: Color = Color::Rgb(205, 214, 244);
    pub const TEXTM1: Color = Color::Rgb(186, 194, 222);
    pub const LOVELACE: Color = Color::Rgb(181, 232, 229);
    pub const GREEN: Color = Color::Rgb(166, 227, 161);
    pub const YELLOW: Color = Color::Rgb(249, 226, 175);
    pub const PEACH: Color = Color::Rgb(250, 179, 135);
    pub const MAROON: Color = Color::Rgb(235, 160, 172);
    pub const RED: Color = Color::Rgb(243, 139, 168);
    pub const MAUVE: Color = Color::Rgb(203, 166, 247);
    pub const BLUE: Color = Color::Rgb(137, 180, 250);
    pub const TEAL: Color = Color::Rgb(148, 226, 213);
    pub const FLAMINGO: Color = Color::Rgb(242, 205, 205);
    pub const PINK: Color = Color::Rgb(245, 194, 231);
    pub const LAVENDER: Color = Color::Rgb(180, 190, 254);

    pub fn regime_color(r: Regime) -> Color {
        match r { Regime::Simple => BLUE, Regime::Advanced => GREEN, Regime::Hybrid => PEACH }
    }
    pub fn phi_color(c: high_agent::metrics::PhiColor) -> Color {
        match c { high_agent::metrics::PhiColor::Green => GREEN, high_agent::metrics::PhiColor::Yellow => YELLOW, high_agent::metrics::PhiColor::Red => RED }
    }
    pub fn trend_arrow(t: high_agent::metrics::Trend) -> &'static str {
        match t { high_agent::metrics::Trend::Up => "↑", high_agent::metrics::Trend::Down => "↓", high_agent::metrics::Trend::Stable => "→" }
    }
}

// ─── Chat System ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct ChatMessage {
    pub role: ChatRole,
    pub content: String,
    pub timestamp: Instant,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChatRole { User, Assistant, System }

impl ChatMessage {
    pub fn user(content: String) -> Self {
        Self { role: ChatRole::User, content, timestamp: Instant::now() }
    }
    pub fn assistant(content: String) -> Self {
        Self { role: ChatRole::Assistant, content, timestamp: Instant::now() }
    }
    pub fn system(content: String) -> Self {
        Self { role: ChatRole::System, content, timestamp: Instant::now() }
    }
}

/// Intent detection: parse user message and decide what the agent should do.
pub fn detect_intent(msg: &str) -> (&str, String, Option<String>) {
    let lower = msg.to_lowercase();

    if lower.contains("build ") || lower.contains("compile ") {
        let lang = if lower.contains("rust") || lower.contains("cargo") { "rust" }
            else if lower.contains("python") { "python" }
            else if lower.contains("node") || lower.contains("npm") { "node" }
            else if lower.contains("go") || lower.contains("golang") { "go" }
            else if lower.contains("java") { "java" }
            else if lower.contains("c++") || lower.contains("cpp") { "cpp" }
            else if lower.contains("c ") || lower.contains(" c,") { "c" }
            else { "auto" };
        let path = extract_path(msg);
        ("build", path, Some(lang.to_string()))
    } else if lower.contains("test ") || lower.contains("run tests") || lower.contains("run the tests") {
        ("test", extract_path(msg), None)
    } else if lower.contains("create ") || lower.contains("make ") || lower.contains("let's build") || lower.contains("lets build") {
        let name = extract_name(msg);
        let kind = if lower.contains("api") || lower.contains("server") { "api" }
            else if lower.contains("cli") || lower.contains("command-line") { "cli" }
            else if lower.contains("web") || lower.contains("website") || lower.contains("app") { "web" }
            else if lower.contains("bot") || lower.contains("agent") { "agent" }
            else if lower.contains("skill") { "skill" }
            else { "app" };
        ("create", format!("{}/{}", kind, name), None)
    } else if lower.contains("analyze ") || lower.contains("review ") || lower.contains("audit ") || lower.contains("check code") {
        ("analyze", extract_path(msg), None)
    } else if lower.contains("skill") {
        let name = extract_name(msg);
        let action = if lower.contains("add") || lower.contains("install") || lower.contains("enable") { "add" }
            else if lower.contains("remove") || lower.contains("delete") { "remove" }
            else { "list" };
        ("skill", name, Some(action.to_string()))
    } else if lower.contains("clone ") || lower.contains("repo ") || lower.contains("repository") {
        let url = extract_url(msg).unwrap_or_else(|| "https://github.com/example/repo".into());
        ("repo", url, Some("clone".to_string()))
    } else if lower.contains("clean") || lower.contains("reset") {
        ("clean", extract_path(msg), None)
    } else {
        ("chat", msg.to_string(), None)
    }
}

fn extract_name(msg: &str) -> String {
    let words: Vec<&str> = msg.split_whitespace().collect();
    let skip = ["create", "make", "build", "a", "an", "the", "new", "project", "file", "skill", "app", "let's", "lets", "called", "named", "add", "remove", "list"];
    for w in words {
        let lower = w.to_lowercase();
        if !skip.contains(&lower.as_str()) && !w.starts_with("--") && w.len() > 2 {
            return w.trim_matches(|c| c == '"' || c == '\'' || c == '.' || c == ',')
                .replace(['-', '/'], "_").chars().filter(|c| c.is_alphanumeric() || *c == '_').collect();
        }
    }
    "my_project".into()
}

fn extract_path(msg: &str) -> String {
    for w in msg.split_whitespace() {
        if w.starts_with("./") || w.starts_with("/") || (w.contains('/') && w.len() > 2) {
            return w.trim_matches(|c| c == '"' || c == '\'' || c == '.' || c == ',').into();
        }
    }
    ".".into()
}

fn extract_url(msg: &str) -> Option<String> {
    for w in msg.split_whitespace() {
        if w.starts_with("http://") || w.starts_with("https://") || w.ends_with(".git") {
            return Some(w.trim_matches(|c| c == '"' || c == '\'' || c == ',' || c == '.').into());
        }
    }
    None
}

// ─── App State ────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Tab { Dashboard, Graph, Theory, History, Agents, Chat }

pub struct App {
    pub metrics: Metrics,
    pub history: History,
    pub graph: DirectedGraph,
    pub tab: Tab,
    pub running: bool,
    pub show_help: bool,
    pub ollama_available: bool,
    pub error_msg: Option<String>,
    pub codebase: String,
    // Chat state
    pub messages: Vec<ChatMessage>,
    pub input_buffer: String,
    pub cursor_pos: usize,
    pub selected_model: String,
    pub typing_start: Option<Instant>,
    pub build_output: Option<String>,
}

impl App {
    pub fn new() -> Self {
        let mut engine = high_agent::RegimeEngine::new();
        engine.seed_graph();
        engine.update_metrics();
        let model = std::env::var("OLLAMA_MODEL").unwrap_or_else(|_| "llama3.2:3b".into());
        Self {
            metrics: engine.metrics.clone(),
            history: engine.history.clone(),
            graph: engine.graph.clone(),
            tab: Tab::Dashboard,
            running: true,
            show_help: false,
            ollama_available: false,
            error_msg: None,
            codebase: "high-agent-rs".into(),
            messages: vec![
                ChatMessage::system("Graph_x_0x0 ready — 8-agent swarm online. Try: 'build rust', 'create api', 'analyze ./src', 'test .', or just chat.".into()),
            ],
            input_buffer: String::new(),
            cursor_pos: 0,
            selected_model: model,
            typing_start: None,
            build_output: None,
        }
    }

    pub fn update_metrics(&mut self, m: Metrics) {
        self.history.push_snapshot(&m);
        self.metrics = m;
    }

    pub fn refresh(&mut self) {
        let state_path = std::env::var("HOME")
            .map(|h| format!("{}/.high-agent/state.json", h))
            .unwrap_or_default();
        if let Some(m) = Metrics::read_state(&state_path) {
            self.update_metrics(m);
        }
    }

    /// Execute a chat action through the agent swarm. Returns the response.
    pub fn execute_action(&mut self, intent: &str, target: &str, extra: Option<String>, engine: &mut high_agent::RegimeEngine) -> String {
        match intent {
            "build" => {
                let lang = extra.as_deref().unwrap_or("auto");
                let path = target;
                let lang_label = if lang == "auto" {
                    engine.builds.detect(path).map(|l| format!("{:?}", l)).unwrap_or_else(|_| "Unknown".into())
                } else {
                    lang.to_string()
                };
                engine.builds.detect(path).ok();
                let result = engine.builds.build(path, None);
                match result {
                    Ok(r) => format!(
                        "Build {}  [{}]\n  Exit: {}  |  Warnings: {}  |  Errors: {}  |  Duration: {}ms\n\n{}",
                        if r.success { "✓ SUCCESS" } else { "✗ FAILED" },
                        lang_label,
                        r.exit_code,
                        r.warnings,
                        r.errors,
                        r.duration_ms,
                        if r.stdout.len() > r.stderr.len() { &r.stdout[..r.stdout.len().min(1500)] } else { &r.stderr[..r.stderr.len().min(1500)] }
                    ),
                    Err(e) => format!("Build error: {}", e),
                }
            }
            "test" => {
                let path = target;
                engine.builds.detect(path).ok();
                let result = engine.builds.build(path, Some("test"));
                match result {
                    Ok(r) => format!(
                        "Tests {}  [{}]\n  Exit: {}  |  Warnings: {}  |  Errors: {}  |  Duration: {}ms\n\n{}",
                        if r.success { "✓ PASSED" } else { "✗ FAILED" },
                        "test",
                        r.exit_code,
                        r.warnings,
                        r.errors,
                        r.duration_ms,
                        if r.stdout.len() > r.stderr.len() { &r.stdout[..r.stdout.len().min(1500)] } else { &r.stderr[..r.stderr.len().min(1500)] }
                    ),
                    Err(e) => format!("Test error: {}", e),
                }
            }
            "create" => {
                let parts: Vec<&str> = target.splitn(2, '/').collect();
                let kind = parts.get(0).unwrap_or(&"app");
                let name = parts.get(1).unwrap_or(&"project");
                let response = self.scaffold_project(kind, name, engine);
                response
            }
            "analyze" => {
                let path = target;
                let snapshot = engine.graph.snapshot();
                let coeffs = engine.orchestrator.current_regime.coeffs();
                let phi = engine.graph.multi_objective(&coeffs);
                format!(
                    "Φ(G) Analysis — {}\n  Φ(G)   = {:+.4}\n  Q(G)   = {:.4}  (modularity — higher=better)\n  Č(G)   = {:.4}  (coupling — lower=better)\n  V(G)   = {:.1}   (cyclomatic — lower=better)\n  Nodes  = {}  |  Edges = {}  |  Modules = {}\n  Regime = {:?}",
                    path, phi, snapshot.q, snapshot.coupling,
                    snapshot.mean_v, snapshot.n_nodes, snapshot.n_edges, snapshot.n_modules,
                    engine.orchestrator.current_regime
                )
            }
            "skill" => {
                let name = target;
                let action = extra.as_deref().unwrap_or("list");
                match action {
                    "add" => {
                        let skill = high_agent::Skill::new(name, "Auto-created skill", "# Skill\n\nAuto-generated by Graph_x_0x0 chat.\n");
                        engine.skills.save(skill).map(|_| format!("Skill '{}' added successfully.", name))
                            .unwrap_or_else(|e| format!("Failed to add skill: {}", e))
                    }
                    "remove" => {
                        engine.skills.delete(name).map(|_| format!("Skill '{}' removed.", name))
                            .unwrap_or_else(|e| format!("Failed to remove skill: {}", e))
                    }
                    _ => {
                        let all = engine.skills.list();
                        if all.is_empty() {
                            "No skills loaded. Add one with 'skill add <name>'.".into()
                        } else {
                            let list: Vec<String> = all.iter().map(|s| format!("  • {}", s.name)).collect();
                            format!("Loaded skills:\n{}", list.join("\n"))
                        }
                    }
                }
            }
            "repo" => {
                let url = target;
                let action = extra.as_deref().unwrap_or("add");
                match action {
                    "clone" => {
                        let name = url.split('/').last().unwrap_or("repo").trim_end_matches(".git");
                        let local_path = format!("./repos/{}", name);
                        engine.repos.add(name, url, &local_path, "main").map(|_| format!("Cloning {} into repos/...", url))
                            .unwrap_or_else(|e| format!("Clone failed: {}", e))
                    }
                    _ => {
                        let all = engine.repos.list();
                        if all.is_empty() {
                            "No repos tracked. Clone one with 'clone <url>'.".into()
                        } else {
                            let list: Vec<String> = all.iter().map(|r| format!("  • {}: {}", r.name, r.url)).collect();
                            format!("Tracked repos:\n{}", list.join("\n"))
                        }
                    }
                }
            }
            "clean" => {
                engine.builds.detect(target).ok();
                let result = engine.builds.build(target, Some("clean"));
                match result {
                    Ok(r) => format!("Clean {}  |  {}ms\n{}",
                        if r.success { "✓ OK" } else { "✗ FAILED" },
                        r.duration_ms,
                        &r.stderr[..r.stderr.len().min(500)]
                    ),
                    Err(e) => format!("Clean error: {}", e),
                }
            }
            _ => {
                // Ollama generate fallback
                let ollama = high_agent::OllamaClient::default();
                let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
                let response = rt.block_on(ollama.generate(target, None));
                match response {
                    Ok(text) => text,
                    Err(_) => generate_response(target),
                }
            }
        }
    }

    fn scaffold_project(&mut self, kind: &str, name: &str, engine: &mut high_agent::RegimeEngine) -> String {
        let dir = std::path::Path::new(".")
            .join("generated")
            .join(kind)
            .join(name);

        let mut created = Vec::new();

        let readme = format!("# {} — generated by Graph_x_0x0\n\nKind: {}\nDate: {}\nPhi(G) scaffolded.", name, kind, chrono_now());
        let readme_path = dir.join("README.md");
        if std::fs::create_dir_all(&dir).is_ok() {
            let _ = std::fs::write(&readme_path, readme);
            created.push("README.md");
        }

        match kind {
            "api" => {
                let src_dir = dir.join("src");
                let _ = std::fs::create_dir_all(&src_dir);
                let _ = std::fs::write(src_dir.join("lib.rs"), "// API library\n");
                let _ = std::fs::write(dir.join("Cargo.toml"), &format!("[package]\nname = \"{}\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\ntokio = {{ version = \"1\", features = [\"full\"] }}\n", name));
                let _ = std::fs::write(src_dir.join("main.rs"), &format!("fn main() {{\n    println!(\"API server starting...: {{}}\", \"{}\");\n}}\n", name));
                created.push("Cargo.toml"); created.push("src/main.rs"); created.push("src/lib.rs");
            }
            "cli" => {
                let src_dir = dir.join("src");
                let _ = std::fs::create_dir_all(&src_dir);
                let _ = std::fs::write(dir.join("Cargo.toml"), &format!("[package]\nname = \"{}\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n", name));
                let _ = std::fs::write(src_dir.join("main.rs"), &format!("fn main() {{ println!(\"Hello from {{}}!\", \"{}\"); }}\n", name));
                created.push("Cargo.toml"); created.push("src/main.rs");
            }
            "web" => {
                let _ = std::fs::create_dir_all(dir.join("src"));
                let _ = std::fs::write(dir.join("index.html"), &format!("<!DOCTYPE html>\n<html><head><title>{}</title></head>\n<body>\n  <h1>{}</h1>\n  <p>Generated by Graph_x_0x0</p>\n</body></html>\n", name, name));
                let _ = std::fs::write(dir.join("package.json"), &format!("{{\n  \"name\": \"{}\",\n  \"version\": \"1.0.0\"\n}}\n", name));
                created.push("index.html"); created.push("package.json");
            }
            "agent" => {
                let _ = std::fs::create_dir_all(dir.join("src"));
                let _ = std::fs::write(dir.join("Cargo.toml"), &format!("[package]\nname = \"{}\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n[dependencies]\n", name));
                let _ = std::fs::write(dir.join("src/main.rs"), &format!("//! {} — AI Agent built with Graph_x_0x0\n\nfn main() {{\n    println!(\"Agent {{}} initialized\", \"{}\");\n}}\n", name, name));
                created.push("Cargo.toml"); created.push("src/main.rs");
            }
            "skill" => {
                let _ = std::fs::write(dir.join("SKILL.md"), &format!("# {} Skill\n\n## Description\nAuto-generated skill for Graph_x_0x0.\n\n## Triggers\n- `{}`\n\n## Actions\n1. Step one\n2. Step two\n\n## Verification\nRun: `echo \"Skill verified\"`\n", name, name));
                created.push("SKILL.md");
            }
            _ => {
                let _ = std::fs::write(dir.join("Cargo.toml"), &format!("[package]\nname = \"{}\"\nversion = \"0.1.0\"\nedition = \"2021\"\n", name));
                let _ = std::fs::write(dir.join("src/main.rs"), &format!("fn main() {{ println!(\"Hello from {{}}!\", \"{0}\"); }}\n", name));
                created.push("Cargo.toml"); created.push("src/main.rs");
            }
        }

        // Add to graph
        engine.graph.add_node(high_agent::Node::new(
            format!("{}_{}_main", kind, name),
            format!("generated.{}", kind),
            format!("generated/{}/{}/main.rs", kind, name),
        ));
        engine.update_metrics();

        if created.is_empty() {
            "Could not create project. Check permissions.".into()
        } else {
            format!("Created {} project '{}' at ./generated/{}/{}\n\nFiles: {}\n\nΦ(G) updated — graph now has {} nodes.",
                kind, name, kind, name, created.join(", "), engine.graph.nodes.len())
        }
    }
}

fn chrono_now() -> String {
    use std::time::SystemTime;
    let dur = SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}

impl Default for App { fn default() -> Self { Self::new() } }

// ─── Drawing ─────────────────────────────────────────────────────────────────

pub fn draw(f: &mut Frame, app: &mut App) {
    let area = f.area();
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(0), Constraint::Length(1)])
        .split(area);

    draw_tab_bar(f, chunks[0], app);
    draw_content(f, chunks[1], app);
    draw_status_bar(f, chunks[2], app);

    if app.show_help { draw_help_overlay(f, area); }
}

fn draw_tab_bar(f: &mut Frame, area: Rect, app: &App) {
    let titles = [
        ("[1] Dashboard", Tab::Dashboard),
        ("[2] Graph", Tab::Graph),
        ("[3] Theory", Tab::Theory),
        ("[4] History", Tab::History),
        ("[5] Agents", Tab::Agents),
        ("[6] Chat", Tab::Chat),
    ];
    let mut line = Line::default();
    for (label, tab) in &titles {
        let color = if *tab == app.tab { palette::MAUVE } else { palette::SUBTEXT };
        let style = if *tab == app.tab { Style::new().fg(color).bold() } else { Style::new().fg(color) };
        line.spans.push(Span::raw("  "));
        line.spans.push(Span::styled(*label, style));
    }
    line.spans.push(Span::raw("  "));

    let block = Block::new()
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::BOTTOM)
        .border_type(BorderType::Plain);

    let para = Paragraph::new(line).block(block);
    f.render_widget(para, area);
}

fn draw_content(f: &mut Frame, area: Rect, app: &mut App) {
    match app.tab {
        Tab::Dashboard => draw_dashboard(f, area, app),
        Tab::Graph => draw_graph_tab(f, area, app),
        Tab::Theory => draw_theory(f, area, app),
        Tab::History => draw_history(f, area, app),
        Tab::Agents => draw_agents_tab(f, area, app),
        Tab::Chat => draw_chat_tab(f, area, app),
    }
}

fn draw_dashboard(f: &mut Frame, area: Rect, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(10), Constraint::Min(0)])
        .split(area);

    let phi_color = palette::phi_color(app.metrics.phi_color);
    let regime_color = palette::regime_color(app.metrics.regime);
    let phi_arrow = palette::trend_arrow(app.metrics.phi_trend);

    let headline = Line::from(vec![
        Span::raw("  Φ(G) = "),
        Span::styled(format!("{:+.4}", app.metrics.phi), Style::new().fg(phi_color).bold()),
        Span::raw("  "),
        Span::styled(phi_arrow, Style::new().fg(phi_color)),
        Span::raw("   "),
        Span::styled("Regime:", Style::new().fg(palette::SUBTEXT)),
        Span::raw("  "),
        Span::styled(app.metrics.regime_str.as_str(), Style::new().fg(regime_color).bold()),
    ]);

    let block = Block::new()
        .title("  Graph_x_0x0 — Live Metrics  ")
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let para = Paragraph::new(headline)
        .block(block)
        .alignment(ratatui::layout::Alignment::Center);
    f.render_widget(para, chunks[0]);

    let q_ratio = (app.metrics.q / 1.0).min(1.0);
    let c_ratio = (app.metrics.coupling / 2.0).min(1.0);
    let v_ratio = (app.metrics.mean_v / 20.0).min(1.0);

    let mut lines: Vec<Line> = Vec::new();
    for (label, ratio, color) in [
        (format!("Q(G) Modularity   {:.4}", app.metrics.q), q_ratio, palette::GREEN),
        (format!("C(G) Coupling     {:.4}", app.metrics.coupling), c_ratio, palette::RED),
        (format!("V(G) Cyclomatic   {:.1}", app.metrics.mean_v), v_ratio, palette::YELLOW),
    ] {
        let bar_len = 30usize;
        let filled = (ratio * bar_len as f64) as usize;
        let empty = (bar_len - filled).max(0);
        let bar_str = format!("{}{}", "█".repeat(filled.min(bar_len)), "░".repeat(empty));
        lines.push(Line::from(vec![
            Span::styled("  ", Style::new()),
            Span::styled(label, Style::new().fg(palette::TEXTM1)),
        ]));
        lines.push(Line::from(vec![
            Span::styled("  ", Style::new()),
            Span::styled(bar_str, Style::new().fg(color)),
        ]));
        lines.push(Line::from(vec![Span::raw("")]));
    }

    lines.push(Line::from(vec![
        Span::styled("  Nodes: ", Style::new().fg(palette::SUBTEXT)),
        Span::styled(format!("{}", app.metrics.n_nodes), Style::new().fg(palette::TEXT).bold()),
        Span::raw("  Edges: "),
        Span::styled(format!("{}", app.metrics.n_edges), Style::new().fg(palette::TEXT).bold()),
        Span::raw("  Regime: "),
        Span::styled(&app.metrics.regime_str, Style::new().fg(regime_color)),
    ]));
    lines.push(Line::from(vec![Span::raw("")]));
    lines.push(Line::from(vec![
        Span::styled("  [r] Refresh  [s] Sweep  [d] Deviate  [6] Chat", Style::new().fg(palette::OVERLAY)),
    ]));

    let block2 = Block::new()
        .title("  Metrics  ")
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let para2 = Paragraph::new(lines)
        .block(block2)
        .wrap(Wrap { trim: true });
    f.render_widget(para2, chunks[1]);
}

fn draw_graph_tab(f: &mut Frame, area: Rect, app: &App) {
    let mut lines: Vec<Line> = vec![
        Line::from(vec![Span::styled("  Graph Topology", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![
            Span::styled("  Nodes: ", Style::new().fg(palette::SUBTEXT)),
            Span::styled(format!("{}", app.metrics.n_nodes), Style::new().fg(palette::BLUE).bold()),
            Span::raw("  Edges: "),
            Span::styled(format!("{}", app.metrics.n_edges), Style::new().fg(palette::BLUE).bold()),
            Span::raw("  Modules: "),
            Span::styled(format!("{}", app.metrics.n_modules), Style::new().fg(palette::BLUE).bold()),
        ]),
        Line::from(vec![Span::raw("")]),
    ];

    let mut by_module: HashMap<String, Vec<String>> = HashMap::new();
    for node in app.graph.nodes.values() {
        by_module.entry(node.module.clone()).or_default().push(node.id.clone());
    }

    let mut modules: Vec<_> = by_module.into_iter().collect();
    modules.sort_by_key(|(m, _)| m.clone());
    for (module, nodes) in modules.into_iter().take(8) {
        let n_nodes = nodes.len();
        lines.push(Line::from(vec![
            Span::styled(format!("  ┌─ {} ", "─".repeat(module.len().min(20))), Style::new().fg(palette::MAUVE)),
        ]));
        for node_id in nodes.clone().into_iter().take(5) {
            let node = app.graph.nodes.get(&node_id);
            let v_str = node.map(|n| format!("V={:.0}", n.cyclomatic)).unwrap_or_default();
            lines.push(Line::from(vec![
                Span::styled("  │  ● ", Style::new().fg(palette::TEAL)),
                Span::styled(node_id, Style::new().fg(palette::TEXT)),
                Span::raw("  "),
                Span::styled(v_str, Style::new().fg(palette::SUBTEXT)),
            ]));
        }
        if n_nodes > 5 {
            lines.push(Line::from(vec![Span::styled("  │  ...", Style::new().fg(palette::SUBTEXT))]));
        }
    }

    if app.graph.nodes.is_empty() {
        lines.push(Line::from(vec![
            Span::styled("  No graph data. Press [r] to refresh.", Style::new().fg(palette::SUBTEXT)),
        ]));
    }

    lines.push(Line::from(vec![Span::raw("")]));
    lines.push(Line::from(vec![
        Span::styled("  Press [6] → Chat to analyze, build, or create.", Style::new().fg(palette::OVERLAY)),
    ]));

    let block = Block::new()
        .title("  Graph  ")
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let para = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: true });
    f.render_widget(para, area);
}

fn draw_theory(f: &mut Frame, area: Rect, app: &App) {
    let coeffs = app.metrics.regime.coeffs();

    let lines: Vec<Line> = vec![
        Line::from(vec![Span::styled("  Mathematical Foundation", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)", Style::new().fg(palette::TEAL).bold())]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  G = (V, E)", Style::new().fg(palette::BLUE).bold()), Span::raw("  Codebase as directed graph. Nodes=functions, Edges=calls/imports.")]),
        Line::from(vec![Span::styled("  Q(G)    ", Style::new().fg(palette::BLUE).bold()), Span::raw("  Newman-Girvan modularity. How well functions cluster within modules.")]),
        Line::from(vec![Span::styled("  Č(G)    ", Style::new().fg(palette::BLUE).bold()), Span::raw("  Mean inter-module coupling per node. Lower = less spaghetti.")]),
        Line::from(vec![Span::styled("  V       ", Style::new().fg(palette::BLUE).bold()), Span::raw("  Cyclomatic complexity (McCabe). Branches, loops, conditionals.")]),
        Line::from(vec![Span::styled("  α, β, γ  ", Style::new().fg(palette::BLUE).bold()), Span::raw("  Regime-dependent coefficients that shift what the system optimizes.")]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Current Regime Coefficients", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![
            Span::styled("  α = ", Style::new().fg(palette::SUBTEXT)),
            Span::styled(format!("{:.1}", coeffs.alpha), Style::new().fg(palette::BLUE).bold()),
            Span::raw("   β = "),
            Span::styled(format!("{:.1}", coeffs.beta), Style::new().fg(palette::RED).bold()),
            Span::raw("   γ = "),
            Span::styled(format!("{:.1}", coeffs.gamma), Style::new().fg(palette::YELLOW).bold()),
        ]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Three Regimes", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Simple   ", Style::new().fg(palette::BLUE).bold()), Span::raw("  α=0.8 β=0.9 γ=0.2  — minimize coupling, fast iteration")]),
        Line::from(vec![Span::styled("  Advanced ", Style::new().fg(palette::GREEN).bold()), Span::raw("  α=1.2 β=0.5 γ=0.3  — maximize modularity, PR review")]),
        Line::from(vec![Span::styled("  Hybrid   ", Style::new().fg(palette::PEACH).bold()), Span::raw("  α=1.0 β=0.6 γ=0.4  — balance all terms, team handoff")]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Deviation Detection", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Sliding window → z-score → if |z| > 2.0: change-point detected", Style::new().fg(palette::TEXTM1))]),
        Line::from(vec![Span::raw("")]),
        Line::from(vec![Span::styled("  Hysteresis: regime switch only if ΔΦ(G) > 0.05", Style::new().fg(palette::TEXTM1))]),
    ];

    let block = Block::new()
        .title("  Theory  ")
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let para = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: true });
    f.render_widget(para, area);
}

fn draw_history(f: &mut Frame, area: Rect, app: &App) {
    let mut lines: Vec<Line> = vec![
        Line::from(vec![Span::styled("  Metric History", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
    ];

    if app.history.entries.is_empty() {
        lines.push(Line::from(vec![
            Span::styled("  No history yet. Press [r] to collect snapshots.", Style::new().fg(palette::SUBTEXT)),
        ]));
    } else {
        lines.push(Line::from(vec![
            Span::styled("  #  ", Style::new().fg(palette::SUBTEXT)),
            Span::styled(format!("{:>8}", "Φ(G)"), Style::new().fg(palette::TEXTM1).bold()),
            Span::raw("  "),
            Span::styled(format!("{:>8}", "Q(G)"), Style::new().fg(palette::TEXTM1).bold()),
            Span::raw("  "),
            Span::styled(format!("{:>8}", "Č(G)"), Style::new().fg(palette::TEXTM1).bold()),
            Span::raw("  "),
            Span::styled(format!("{:>8}", "V(G)"), Style::new().fg(palette::TEXTM1).bold()),
            Span::raw("  "),
            Span::styled(format!("{:>8}", "Regime"), Style::new().fg(palette::TEXTM1).bold()),
        ]));
        lines.push(Line::from(vec![
            Span::raw("  "),
            Span::styled("─".repeat(58), Style::new().fg(palette::SURFACE2)),
        ]));

        for (i, entry) in app.history.entries.iter().rev().take(15).enumerate() {
            let idx = app.history.entries.len() - i;
            let regime = Regime::from_str(&entry.regime).unwrap_or(Regime::Hybrid);
            let regime_color = palette::regime_color(regime);
            let regime_short = entry.regime.chars().take(6).collect::<String>();
            let phi_c = if entry.phi > 0.0 { high_agent::metrics::PhiColor::Green }
                else if entry.phi > -2.0 { high_agent::metrics::PhiColor::Yellow }
                else { high_agent::metrics::PhiColor::Red };
            let phi_color = palette::phi_color(phi_c);

            lines.push(Line::from(vec![
                Span::styled(format!("  {:2}", idx), Style::new().fg(palette::SUBTEXT)),
                Span::raw(" "),
                Span::styled(format!("{:+.4}", entry.phi), Style::new().fg(phi_color).bold()),
                Span::raw("  "),
                Span::styled(format!("{:.4}", entry.q), Style::new().fg(palette::TEXTM1)),
                Span::raw("  "),
                Span::styled(format!("{:.4}", entry.coupling), Style::new().fg(palette::TEXTM1)),
                Span::raw("  "),
                Span::styled(format!("{:.1}", entry.mean_v), Style::new().fg(palette::TEXTM1)),
                Span::raw("  "),
                Span::styled(format!("{:6}", regime_short), Style::new().fg(regime_color)),
            ]));
        }
    }

    let block = Block::new()
        .title("  History  ")
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let para = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: true });
    f.render_widget(para, area);
}

fn draw_agents_tab(f: &mut Frame, area: Rect, _app: &App) {
    let agents = [
        ("Orchestrator", "Regime-aware task routing + Φ(G) optimization", palette::MAUVE),
        ("Refactor", "Code restructuring + coupling reduction", palette::BLUE),
        ("Quality", "Code review + quality scoring", palette::GREEN),
        ("Test", "Test generation + coverage analysis", palette::YELLOW),
        ("Skill", "Skill discovery + management", palette::TEAL),
        ("Repo", "Repository analysis + cloning", palette::PEACH),
        ("Build", "Build orchestration + multi-language support", palette::FLAMINGO),
        ("Planner", "Task decomposition + execution planning", palette::PINK),
    ];

    let mut lines: Vec<Line> = vec![
        Line::from(vec![Span::styled("  Agent Swarm — 8-Deep Agent System", Style::new().fg(palette::TEXT).bold())]),
        Line::from(vec![Span::raw("")]),
    ];

    for (name, desc, color) in &agents {
        lines.push(Line::from(vec![
            Span::styled("  ● ", Style::new().fg(*color)),
            Span::styled(format!("{:12}", name), Style::new().fg(*color).bold()),
            Span::raw("  "),
            Span::styled(*desc, Style::new().fg(palette::TEXTM1)),
        ]));
    }

    lines.push(Line::from(vec![Span::raw("")]));
    lines.push(Line::from(vec![Span::styled("  Chat [6] → Type commands like:", Style::new().fg(palette::SUBTEXT))]));
    lines.push(Line::from(vec![Span::styled("  'build rust'  'create api myapi'  'analyze ./src'  'test .'", Style::new().fg(palette::TEXTM1))]));

    let block = Block::new()
        .title("  Agents  ")
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let para = Paragraph::new(lines)
        .block(block)
        .wrap(Wrap { trim: true });
    f.render_widget(para, area);
}

fn draw_chat_tab(f: &mut Frame, area: Rect, app: &mut App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(0), Constraint::Length(6)])
        .split(area);

    let items: Vec<ListItem> = app.messages.iter().map(|msg| {
        let (name, color) = match msg.role {
            ChatRole::User => ("You", palette::BLUE),
            ChatRole::Assistant => ("Φ", palette::GREEN),
            ChatRole::System => ("SYS", palette::SUBTEXT),
        };
        let truncated = if msg.content.len() > 300 {
            format!("{}...", &msg.content[..300])
        } else {
            msg.content.clone()
        };
            let line = Line::from(vec![
                Span::styled(format!("{}: ", name), Style::new().fg(color).bold()),
                Span::styled(truncated.clone(), Style::new().fg(palette::TEXT)),
            ]);
            ListItem::new(line)
    }).collect();

    let list = List::new(items)
        .block(Block::new()
            .title("  Chat  ")
            .title_style(Style::new().fg(palette::MAUVE).bold())
            .style(Style::new().bg(palette::SURFACE))
            .borders(Borders::ALL)
            .border_type(BorderType::Rounded));

    f.render_widget(list, chunks[0]);

    let (input_display, hint_line) = if app.input_buffer.is_empty() {
        (Line::from(vec![Span::styled("  > ", Style::new().fg(palette::MAUVE).bold())]),
         Line::from(vec![Span::styled("  Commands: build [lang] | create [type] [name] | analyze [path] | test [path]", Style::new().fg(palette::SUBTEXT))]))
    } else {
        let pos = app.cursor_pos.min(app.input_buffer.len());
        let before = &app.input_buffer[..pos];
        let after = &app.input_buffer[pos..];
        (Line::from(vec![
            Span::styled("  > ", Style::new().fg(palette::MAUVE).bold()),
            Span::raw(before),
            Span::styled("█", Style::new().fg(palette::BLUE).bold()),
            Span::raw(after),
        ]), Line::from(vec![Span::styled("  Press Enter to send  |  Tab for autocomplete  |  Esc to clear", Style::new().fg(palette::OVERLAY))]))
    };

    let input_block = Block::new()
        .title(format!("  Input — Model: {}  ", app.selected_model))
        .title_style(Style::new().fg(palette::TEXT).bold())
        .style(Style::new().bg(palette::SURFACE0))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let input_para = Paragraph::new(vec![input_display, hint_line])
        .block(input_block)
        .wrap(Wrap { trim: true });

    f.render_widget(input_para, chunks[1]);
}

fn draw_status_bar(f: &mut Frame, area: Rect, app: &App) {
    let regime_color = palette::regime_color(app.metrics.regime);
    let phi_color = palette::phi_color(app.metrics.phi_color);

    let line = Line::from(vec![
        Span::styled("Graph_x_0x0", Style::new().fg(palette::MAUVE).bold()),
        Span::raw("  |  "),
        Span::styled(&app.codebase, Style::new().fg(palette::SUBTEXT)),
        Span::raw("  |  Φ="),
        Span::styled(app.metrics.phi_formatted.as_str(), Style::new().fg(phi_color).bold()),
        Span::raw("  ["),
        Span::styled(&app.metrics.regime_str, Style::new().fg(regime_color).bold()),
        Span::raw("]  "),
        Span::styled("[r] Refresh", Style::new().fg(palette::OVERLAY)),
        Span::raw("  "),
        Span::styled("[?] Help", Style::new().fg(palette::OVERLAY)),
        Span::raw("  "),
        Span::styled("[q] Quit", Style::new().fg(palette::OVERLAY)),
    ]);

    let para = Paragraph::new(line)
        .style(Style::new().bg(palette::SURFACE0))
        .alignment(ratatui::layout::Alignment::Left);
    f.render_widget(para, area);
}

fn draw_help_overlay(f: &mut Frame, area: Rect) {
    let text = r#"══════════════════════════════════════════
           Graph_x_0x0 — Keybindings
══════════════════════════════════════════

  [1] Dashboard    — Φ(G) metrics + gauges
  [2] Graph        — ASCII topology view
  [3] Theory       — Mathematical explanation
  [4] History      — Metric timeline
  [5] Agents       — Agent swarm overview
  [6] Chat         — Chat + 8-agent build system

  [r] Refresh      — Reload state from disk
  [s] Sweep        — Evaluate all 3 regimes
  [d] Deviate      — Simulate deviation (demo)
  [o] Ollama check — Check Ollama availability

  Chat commands:
    build [lang]   — Build project (rust/python/node/go/java)
    create [type] [name] — Scaffold project (api/cli/web/agent)
    analyze [path] — Run Φ(G) analysis
    test [path]    — Run tests
    skill [name]   — Manage skills
    clone [url]    — Clone repository
    Or just chat with the swarm.

  [Enter] Send  [Esc] Clear/close  [Tab] Autocomplete
  [?] This help [q] Quit

══════════════════════════════════════════"#;

    let lines: Vec<Line> = text.lines().map(|l| {
        if l.starts_with("══") { Line::from(Span::styled(l, Style::new().fg(palette::MAUVE))) }
        else if l.contains('[') { Line::from(Span::styled(l, Style::new().fg(palette::BLUE))) }
        else { Line::from(Span::styled(l, Style::new().fg(palette::TEXT))) }
    }).collect();

    let block = Block::new()
        .title("  Help  ")
        .title_style(Style::new().fg(palette::MAUVE).bold())
        .style(Style::new().bg(palette::SURFACE))
        .borders(Borders::ALL)
        .border_type(BorderType::Rounded);

    let inner = block.inner(area);
    let overlay_para = Paragraph::new(lines)
        .alignment(ratatui::layout::Alignment::Left);

    f.render_widget(Clear, area);
    f.render_widget(block, area);
    f.render_widget(overlay_para, inner);
}

// ─── Event Loop ──────────────────────────────────────────────────────────────

pub fn run(mut app: App, tick_rate: Duration) -> std::io::Result<()> {
    use ratatui::backend::CrosstermBackend;
    use std::io;
    use crossterm::{execute, terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen}};

    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    enable_raw_mode()?;

    let backend = CrosstermBackend::new(stdout);
    let mut terminal = ratatui::Terminal::new(backend)?;

    let mut engine = high_agent::RegimeEngine::new();
    engine.seed_graph();
    engine.update_metrics();
    app.update_metrics(engine.metrics.clone());

    let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
    app.ollama_available = rt.block_on(engine.ollama.is_available());

    loop {
        terminal.draw(|f| draw(f, &mut app))?;

        if crossterm::event::poll(tick_rate)? {
            if let crossterm::event::Event::Key(key) = crossterm::event::read()? {
                if key.kind == KeyEventKind::Press {
                    handle_key(key.code, &mut app, &mut engine);
                }
            }
        }

        if !app.running { break; }
    }

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    Ok(())
}

fn handle_key(key: KeyCode, app: &mut App, engine: &mut high_agent::RegimeEngine) {
    match key {
        KeyCode::Char('q') => { app.running = false; }
        KeyCode::Char('?') => { app.show_help = !app.show_help; }
        KeyCode::Char('r') => {
            engine.update_metrics();
            app.update_metrics(engine.metrics.clone());
        }
        KeyCode::Char('s') => {
            let results = engine.sweep_regimes();
            if let Some((best_regime, _)) = results.iter().max_by(|a, b| a.1.partial_cmp(&b.1).unwrap()) {
                let _ = engine.switch_regime(*best_regime);
                app.update_metrics(engine.metrics.clone());
                let _ = engine.write_state();
            }
        }
        KeyCode::Char('d') => {
            engine.simulate_deviation_and_switch();
            app.update_metrics(engine.metrics.clone());
        }
        KeyCode::Char('o') => {
            let rt = tokio::runtime::Builder::new_current_thread().enable_all().build().unwrap();
            app.ollama_available = rt.block_on(engine.ollama.is_available());
        }
        KeyCode::Char('1') => app.tab = Tab::Dashboard,
        KeyCode::Char('2') => app.tab = Tab::Graph,
        KeyCode::Char('3') => app.tab = Tab::Theory,
        KeyCode::Char('4') => app.tab = Tab::History,
        KeyCode::Char('5') => app.tab = Tab::Agents,
        KeyCode::Char('6') => app.tab = Tab::Chat,

        // Chat input — only active when on Chat tab
        _ if app.tab == Tab::Chat => match key {
            KeyCode::Enter => {
                let msg = app.input_buffer.trim().to_string();
                app.input_buffer.clear();
                app.cursor_pos = 0;

                if msg.is_empty() { return; }

                app.messages.push(ChatMessage::user(msg.clone()));

                let (intent, target, extra) = detect_intent(&msg);
                let response = app.execute_action(intent, &target, extra, engine);

                app.messages.push(ChatMessage::assistant(response));
                engine.update_metrics();
                app.update_metrics(engine.metrics.clone());
            }
            KeyCode::Backspace => {
                if app.cursor_pos > 0 && !app.input_buffer.is_empty() {
                    let pos = app.cursor_pos.saturating_sub(1);
                    app.input_buffer.remove(pos);
                    app.cursor_pos = pos;
                }
            }
            KeyCode::Delete => {
                if app.cursor_pos < app.input_buffer.len() {
                    app.input_buffer.remove(app.cursor_pos);
                }
            }
            KeyCode::Left => {
                if app.cursor_pos > 0 { app.cursor_pos -= 1; }
            }
            KeyCode::Right => {
                if app.cursor_pos < app.input_buffer.len() { app.cursor_pos += 1; }
            }
            KeyCode::Esc => {
                app.input_buffer.clear();
                app.cursor_pos = 0;
            }
            KeyCode::Char(c) => {
                let pos = app.cursor_pos.min(app.input_buffer.len());
                app.input_buffer.insert(pos, c);
                app.cursor_pos += 1;
            }
            KeyCode::Tab => {
                let hints = ["build rust", "build python", "create api ", "create cli ",
                    "create web ", "analyze ./src", "test .", "skill list", "clone "];
                if let Some(hint) = hints.iter().find(|h| h.starts_with(&app.input_buffer)) {
                    app.input_buffer = hint.to_string();
                    app.cursor_pos = app.input_buffer.len();
                }
            }
            _ => {}
        },
        KeyCode::Esc => { app.show_help = false; }
        _ => {}
    }
}

/// Generate a contextual response when Ollama is unavailable.
fn generate_response(msg: &str) -> String {
    let lower = msg.to_lowercase();

    if lower.contains("help") || lower.contains("what can you do") {
        return "I can execute these commands:\n\n  build [lang]    — Compile (rust, python, node, go, java)\n  create [type] [name] — Scaffold project (api, cli, web, agent)\n  analyze [path]  — Run Φ(G) metric analysis\n  test [path]     — Run tests\n  skill [name]    — Manage skills (add, remove, list)\n  clone [url]     — Clone a repository\n  clean           — Clean build artifacts\n\nOr just chat — I'll respond when Ollama is available.".into();
    }

    if lower.contains("hello") || lower.contains("hi") || lower.contains("hey") {
        return "Hello! I'm Graph_x_0x0, a self-aware AIOS with 8 agents. Type 'build rust', 'create api', or 'analyze ./src' to get started.".into();
    }

    if lower.contains("phi") || lower.contains("formula") || lower.contains("equation") {
        return "Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)\n\nQ=modularity (higher=better), Č=coupling (lower=better), V=cyclomatic complexity.\nThe α,β,γ coefficients shift by regime: Simple/Advanced/Hybrid.".into();
    }

    if lower.contains("regime") || lower.contains("mode") {
        return "Three regimes:\n  Simple (α=0.8, β=0.9) — minimize coupling, fast iteration\n  Advanced (α=1.2, β=0.5) — maximize modularity, PR review\n  Hybrid (α=1.0, β=0.6) — balance all terms, team handoff\n\nPress [s] to sweep and find the best regime for current graph.".into();
    }

    if lower.contains("agent") || lower.contains("swarm") {
        return "8-agent swarm: Orchestrator, Refactor, Quality, Test, Skill, Repo, Build, Planner.\nEach agent owns one domain. The Orchestrator routes tasks based on Φ(G) optimization.\nType 'build rust' or 'create api' to see them in action.".into();
    }

    if lower.contains("thanks") || lower.contains("thank you") {
        return "You're welcome! Say 'build', 'create', 'analyze', or 'test' to put the swarm to work.".into();
    }

    format!(
        "I understand: '{}'. Try: 'build rust', 'create api myapi', 'analyze ./src', or 'test .'\n\
        For chat responses, start Ollama: ollama serve",
        if msg.len() > 50 { &msg[..50] } else { msg }
    )
}

fn main() {
    let tick_rate = Duration::from_millis(250);
    let app = App::new();
    if let Err(e) = run(app, tick_rate) {
        eprintln!("Error: {:?}", e);
    }
}
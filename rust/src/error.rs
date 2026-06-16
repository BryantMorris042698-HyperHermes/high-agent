//! Error types for the high-agent library.

use thiserror::Error;

#[derive(Error, Debug)]
pub enum HighAgentError {
    #[error("Graph error: {0}")]
    Graph(String),
    #[error("Regime error: {0}")]
    Regime(String),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("YAML error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("Skill error: {0}")]
    Skill(String),
    #[error("Repo error: {0}")]
    Repo(String),
    #[error("Build error: {0}")]
    Build(String),
    #[error("Ollama error: {0}")]
    Ollama(String),
    #[error("Agent error: {0}")]
    Agent(String),
    #[error("TUI error: {0}")]
    Tui(String),
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
}

pub type Result<T> = std::result::Result<T, HighAgentError>;
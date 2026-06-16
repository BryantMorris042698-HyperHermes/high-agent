//! Agent definitions — Deep Agent types with roles, memory, and capabilities.

use crate::error::{HighAgentError, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash, Default)]
pub enum AgentRole {
    Orchestrator,
    Refactor,
    Quality,
    Test,
    Skill,
    Repo,
    Build,
    Planner,
    #[default]
    General,
}

impl AgentRole {
    pub fn description(&self) -> &'static str {
        match self {
            Self::Orchestrator => "Central coordinator, owns Φ(G), manages regime",
            Self::Refactor => "Optimizes graph structure — split nodes, merge edges",
            Self::Quality => "Monitors cyclomatic complexity, flags violations",
            Self::Test => "Ensures test coverage per module",
            Self::Skill => "Manages skill library — load, create, update skills",
            Self::Repo => "Manages repository connections — clone, sync, fetch",
            Self::Build => "Handles build system — compile, test, clean",
            Self::Planner => "Plans multi-step agent tasks, coordinates sub-agents",
            Self::General => "General purpose — handles any request",
        }
    }
    pub fn icon(&self) -> &'static str {
        match self {
            Self::Orchestrator => "⚡", Self::Refactor => "🔧", Self::Quality => "🔍",
            Self::Test => "🧪", Self::Skill => "📚", Self::Repo => "📦",
            Self::Build => "🏗", Self::Planner => "🗺", Self::General => "🤖",
        }
    }
}

impl std::fmt::Display for AgentRole {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Self::Orchestrator => "Orchestrator", Self::Refactor => "Refactor",
            Self::Quality => "Quality", Self::Test => "Test",
            Self::Skill => "Skill", Self::Repo => "Repo",
            Self::Build => "Build", Self::Planner => "Planner",
            Self::General => "General",
        };
        write!(f, "{}", s)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentMemory {
    pub entries: Vec<MemoryEntry>,
    pub max_entries: usize,
}

impl AgentMemory {
    pub fn new(max_entries: usize) -> Self { Self { entries: Vec::new(), max_entries } }
    pub fn push(&mut self, role: &str, content: &str) {
        self.entries.push(MemoryEntry { role: role.to_string(), content: content.to_string(), timestamp: chrono_now() });
        if self.entries.len() > self.max_entries { self.entries.remove(0); }
    }
    pub fn recent(&self, n: usize) -> Vec<&MemoryEntry> {
        self.entries.iter().rev().take(n).collect()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEntry {
    pub role: String,
    pub content: String,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentConfig {
    pub model: String,
    pub temperature: f64,
    pub max_tokens: i32,
    pub system_prompt: String,
}

impl AgentConfig {
    pub fn default_for(role: AgentRole) -> Self {
        let (model, temp, max_tokens) = match role {
            AgentRole::Orchestrator => ("llama3.2:3b", 0.3, 1024),
            AgentRole::Refactor => ("llama3.2:3b", 0.4, 512),
            AgentRole::Quality => ("llama3.2:3b", 0.3, 512),
            AgentRole::Test => ("llama3.2:3b", 0.4, 512),
            AgentRole::Skill => ("llama3.2:3b", 0.5, 512),
            AgentRole::Repo => ("llama3.2:3b", 0.3, 512),
            AgentRole::Build => ("llama3.2:3b", 0.3, 512),
            AgentRole::Planner => ("llama3.2:3b", 0.5, 1024),
            AgentRole::General => ("llama3.2:3b", 0.7, 512),
        };
        Self {
            model: model.to_string(), temperature: temp, max_tokens,
            system_prompt: format!("You are a {} agent in the Graph_x_0x0 swarm. {}", role, role.description()),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Agent {
    pub id: AgentId,
    pub role: AgentRole,
    pub name: String,
    pub config: AgentConfig,
    pub memory: AgentMemory,
    pub active: bool,
    pub tasks_completed: u32,
    pub tasks_failed: u32,
}

pub type AgentId = u32;

impl Agent {
    pub fn new(id: AgentId, role: AgentRole, name: &str) -> Self {
        Self {
            id, role, name: name.to_string(),
            config: AgentConfig::default_for(role),
            memory: AgentMemory::new(50),
            active: true,
            tasks_completed: 0,
            tasks_failed: 0,
        }
    }
    pub fn mark_success(&mut self) { self.tasks_completed += 1; }
    pub fn mark_failure(&mut self) { self.tasks_failed += 1; }
    pub fn success_rate(&self) -> f64 {
        let total = self.tasks_completed + self.tasks_failed;
        if total == 0 { 0.0 } else { self.tasks_completed as f64 / total as f64 }
    }
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
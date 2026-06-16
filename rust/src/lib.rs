//! Graph_x_0x0 — AIOS for Mobile TUI Deep Agents Storm Swarm
//!
//! Core exports re-exported for both CLI and TUI binaries.

pub use crate::error::{HighAgentError, Result};
pub use crate::graph::{DirectedGraph, Node, Edge, EdgeType, GraphSnapshot, SegmentedRegimeDetector, DeviationAlert, DeviationDirection};
pub use crate::regime::{Regime, RegimeCoeffs, RegimeTransition, HYSTERESIS_MARGIN};
pub use crate::metrics::{Metrics, History, HistoryEntry, PhiColor, Trend};
pub use crate::orchestrator::Orchestrator;
pub use crate::core::{RegimeEngine, TaskType};
pub use crate::ollama::{OllamaClient, ModelInfo};
pub use crate::skills::{Skill, SkillManager};
pub use crate::repos::{Repo, RepoStatus, RepoManager};
pub use crate::build::{BuildManager, BuildConfig, BuildResult, BuildType, Language};
pub use crate::agent::{Agent, AgentId, AgentRole, AgentConfig, AgentMemory, MemoryEntry};
pub use crate::swarm::{Swarm, SwarmTask, TaskStatus, DispatchEntry, SwarmStats};
pub use crate::planner::{Planner, Plan, PlanStep, StepStatus, PlanStatus};

pub mod error;
pub mod graph;
pub mod regime;
pub mod metrics;
pub mod orchestrator;
pub mod core;
pub mod ollama;
pub mod skills;
pub mod repos;
pub mod build;
pub mod agent;
pub mod swarm;
pub mod planner;
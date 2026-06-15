//! Swarm — multi-agent coordination system.

use crate::agent::{Agent, AgentId, AgentRole, AgentMemory};
use crate::error::{HighAgentError, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Swarm {
    pub agents: HashMap<AgentId, Agent>,
    pub next_id: AgentId,
    pub active_tasks: Vec<SwarmTask>,
    pub completed_tasks: Vec<SwarmTask>,
    pub dispatch_log: Vec<DispatchEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwarmTask {
    pub id: u32,
    pub description: String,
    pub assigned_to: Option<AgentId>,
    pub status: TaskStatus,
    pub created_at: String,
    pub result: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum TaskStatus { Pending, Running, Completed, Failed, Cancelled }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DispatchEntry {
    pub from: AgentId,
    pub to: AgentId,
    pub task_id: u32,
    pub message: String,
    pub timestamp: String,
}

impl Swarm {
    pub fn new() -> Self { Self::default() }

    pub fn spawn(&mut self, role: AgentRole, name: &str) -> AgentId {
        let id = self.next_id;
        self.next_id += 1;
        let agent = Agent::new(id, role, name);
        self.agents.insert(id, agent);
        id
    }

    pub fn spawn_all_defaults(&mut self) {
        let roles = [
            (AgentRole::Orchestrator, "Φ-Orchestrator"),
            (AgentRole::Refactor, "Refactor-Agent"),
            (AgentRole::Quality, "Quality-Agent"),
            (AgentRole::Test, "Test-Agent"),
            (AgentRole::Skill, "Skill-Agent"),
            (AgentRole::Repo, "Repo-Agent"),
            (AgentRole::Build, "Build-Agent"),
            (AgentRole::Planner, "Planner-Agent"),
        ];
        for (role, name) in roles {
            self.spawn(role, name);
        }
    }

    pub fn get(&self, id: AgentId) -> Option<&Agent> { self.agents.get(&id) }
    pub fn get_mut(&mut self, id: AgentId) -> Option<&mut Agent> { self.agents.get_mut(&id) }

    pub fn list_by_role(&self, role: AgentRole) -> Vec<&Agent> {
        self.agents.values().filter(|a| a.role == role).collect()
    }

    pub fn dispatch(&mut self, from: AgentId, to: AgentId, task_id: u32, message: &str) -> Result<()> {
        if !self.agents.contains_key(&from) { return Err(HighAgentError::Agent(format!("Agent {} not found", from))); }
        if !self.agents.contains_key(&to) { return Err(HighAgentError::Agent(format!("Agent {} not found", to))); }
        self.dispatch_log.push(DispatchEntry {
            from, to, task_id, message: message.to_string(), timestamp: chrono_now(),
        });
        Ok(())
    }

    pub fn create_task(&mut self, description: &str) -> u32 {
        let id = self.active_tasks.len() as u32 + self.completed_tasks.len() as u32;
        self.active_tasks.push(SwarmTask {
            id, description: description.to_string(), assigned_to: None,
            status: TaskStatus::Pending, created_at: chrono_now(), result: None,
        });
        id
    }

    pub fn assign_task(&mut self, task_id: u32, agent_id: AgentId) -> Result<()> {
        let task = self.active_tasks.iter_mut().find(|t| t.id == task_id)
            .ok_or_else(|| HighAgentError::Agent(format!("Task {} not found", task_id)))?;
        if !self.agents.contains_key(&agent_id) {
            return Err(HighAgentError::Agent(format!("Agent {} not found", agent_id)));
        }
        task.assigned_to = Some(agent_id);
        task.status = TaskStatus::Running;
        Ok(())
    }

    pub fn complete_task(&mut self, task_id: u32, result: &str) {
        if let Some(pos) = self.active_tasks.iter().position(|t| t.id == task_id) {
            let mut task = self.active_tasks.remove(pos);
            task.status = TaskStatus::Completed;
            task.result = Some(result.to_string());
            self.completed_tasks.push(task);
        }
    }

    pub fn fail_task(&mut self, task_id: u32) {
        if let Some(pos) = self.active_tasks.iter().position(|t| t.id == task_id) {
            let mut task = self.active_tasks.remove(pos);
            task.status = TaskStatus::Failed;
            self.completed_tasks.push(task);
        }
    }

    pub fn active_agents(&self) -> Vec<&Agent> {
        self.agents.values().filter(|a| a.active).collect()
    }

    pub fn stats(&self) -> SwarmStats {
        SwarmStats {
            total_agents: self.agents.len(),
            active_agents: self.active_agents().len(),
            pending_tasks: self.active_tasks.iter().filter(|t| t.status == TaskStatus::Pending).count(),
            running_tasks: self.active_tasks.iter().filter(|t| t.status == TaskStatus::Running).count(),
            completed_tasks: self.completed_tasks.len(),
            failed_tasks: self.completed_tasks.iter().filter(|t| t.status == TaskStatus::Failed).count(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwarmStats {
    pub total_agents: usize,
    pub active_agents: usize,
    pub pending_tasks: usize,
    pub running_tasks: usize,
    pub completed_tasks: usize,
    pub failed_tasks: usize,
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
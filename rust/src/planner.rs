//! Planner — multi-step task planning and sub-agent coordination.

use crate::agent::{AgentId, AgentRole};
use crate::error::{HighAgentError, Result};
use crate::swarm::{Swarm, SwarmTask, TaskStatus};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlanStep {
    pub step_id: u32,
    pub description: String,
    pub agent_role: AgentRole,
    pub dependencies: Vec<u32>,
    pub status: StepStatus,
    pub result: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum StepStatus { Pending, Running, Done, Skipped, Failed }

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Plan {
    pub id: u32,
    pub description: String,
    pub steps: Vec<PlanStep>,
    pub status: PlanStatus,
    pub created_at: String,
    pub completed_at: Option<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Default)]
pub enum PlanStatus { Planning, Executing, Completed, Failed, #[default] Cancelled }

impl Plan {
    pub fn new(id: u32, description: &str) -> Self {
        Self {
            id, description: description.to_string(), steps: Vec::new(),
            status: PlanStatus::Planning, created_at: chrono_now(), completed_at: None,
        }
    }
    pub fn add_step(&mut self, description: &str, role: AgentRole, dependencies: Vec<u32>) -> u32 {
        let id = self.steps.len() as u32;
        self.steps.push(PlanStep {
            step_id: id, description: description.to_string(), agent_role: role,
            dependencies, status: StepStatus::Pending, result: None,
        });
        id
    }
    pub fn ready_steps(&self) -> Vec<&PlanStep> {
        self.steps.iter().filter(|s| {
            s.status == StepStatus::Pending && s.dependencies.iter().all(|dep| {
                self.steps.iter().any(|other| other.step_id == *dep && other.status == StepStatus::Done)
            })
        }).collect()
    }
    pub fn all_done(&self) -> bool {
        self.steps.iter().all(|s| s.status == StepStatus::Done || s.status == StepStatus::Skipped)
    }
    pub fn any_failed(&self) -> bool {
        self.steps.iter().any(|s| s.status == StepStatus::Failed)
    }
}

pub struct Planner {
    pub plans: Vec<Plan>,
    pub next_plan_id: u32,
}

impl Planner {
    pub fn new() -> Self { Self { plans: Vec::new(), next_plan_id: 0 } }

    pub fn create_plan(&mut self, description: &str) -> u32 {
        let id = self.next_plan_id;
        self.next_plan_id += 1;
        self.plans.push(Plan::new(id, description));
        id
    }

    pub fn get_plan(&mut self, id: u32) -> Option<&mut Plan> {
        self.plans.iter_mut().find(|p| p.id == id)
    }

    /// Execute a plan by coordinating with the swarm.
    pub fn execute_plan(&mut self, plan_id: u32, swarm: &mut Swarm) -> Result<String> {
        let plan = self.get_plan(plan_id).ok_or_else(|| HighAgentError::Agent(format!("Plan {} not found", plan_id)))?;
        plan.status = PlanStatus::Executing;

        while !plan.all_done() && !plan.any_failed() {
            let ready: Vec<u32> = plan.ready_steps().iter().map(|s| s.step_id).collect();
            if ready.is_empty() { break; }

            for step_id in ready {
                let step = plan.steps.iter_mut().find(|s| s.step_id == step_id).unwrap();
                let agent_role = step.agent_role;
                if let Some(agent) = swarm.list_by_role(agent_role).first() {
                    step.status = StepStatus::Running;
                    step.result = Some(format!("Step {} executed by agent {:?}", step.step_id, agent.id));
                    step.status = StepStatus::Done;
                }
            }
        }

        if plan.any_failed() { plan.status = PlanStatus::Failed; }
        else if plan.all_done() { plan.status = PlanStatus::Completed; plan.completed_at = Some(chrono_now()); }

        Ok(format!("Plan {}: {:?} ({} steps)", plan_id, plan.status, plan.steps.len()))
    }

    /// Parse a natural language request into a plan with steps.
    pub fn plan_from_request(&mut self, request: &str, available_agents: &[(AgentRole, &str)]) -> u32 {
        let plan_id = self.create_plan(request);

        // Simple heuristic: break request into steps based on keywords
        let segments: Vec<&str> = request.split(&['.', ';'][..])
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .collect();

        let role_map: Vec<(AgentRole, &str)> = available_agents.iter().map(|(r, n)| (*r, *n)).collect();

        for (i, segment) in segments.iter().enumerate() {
            let role = if segment.contains("skill") || segment.contains("learn") || segment.contains("teach") {
                AgentRole::Skill
            } else if segment.contains("build") || segment.contains("compile") || segment.contains("test") {
                AgentRole::Build
            } else if segment.contains("refactor") || segment.contains("split") || segment.contains("merge") {
                AgentRole::Refactor
            } else if segment.contains("repo") || segment.contains("clone") || segment.contains("sync") {
                AgentRole::Repo
            } else {
                AgentRole::General
            };

            self.get_plan(plan_id).unwrap().add_step(segment, role, if i > 0 { vec![i as u32 - 1] } else { vec![] });
        }

        plan_id
    }

    pub fn cancel_plan(&mut self, plan_id: u32) -> Result<()> {
        let plan = self.get_plan(plan_id).ok_or_else(|| HighAgentError::Agent(format!("Plan {} not found", plan_id)))?;
        plan.status = PlanStatus::Cancelled;
        for step in &mut plan.steps {
            if step.status == StepStatus::Pending || step.status == StepStatus::Running {
                step.status = StepStatus::Skipped;
            }
        }
        Ok(())
    }
}

impl Default for Planner {
    fn default() -> Self { Self::new() }
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
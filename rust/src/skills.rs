//! Skill management — load, create, update, delete skills on demand.

use crate::error::{HighAgentError, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Skill {
    pub name: String,
    pub category: Option<String>,
    pub description: String,
    pub content: String,
    pub triggers: Vec<String>,
    pub tags: Vec<String>,
    pub created_at: String,
    pub updated_at: String,
}

impl Skill {
    pub fn new(name: &str, description: &str, content: &str) -> Self {
        let now = chrono_now();
        Self {
            name: name.to_string(),
            category: None,
            description: description.to_string(),
            content: content.to_string(),
            triggers: vec![],
            tags: vec![],
            created_at: now.clone(),
            updated_at: now,
        }
    }
    pub fn with_category(mut self, cat: &str) -> Self { self.category = Some(cat.to_string()); self }
    pub fn with_triggers(mut self, triggers: Vec<&str>) -> Self { self.triggers = triggers.iter().map(|s| s.to_string()).collect(); self }
    pub fn with_tags(mut self, tags: Vec<&str>) -> Self { self.tags = tags.iter().map(|s| s.to_string()).collect(); self }
}

pub struct SkillManager {
    pub skills: HashMap<String, Skill>,
    pub skills_dir: PathBuf,
}

impl SkillManager {
    pub fn new() -> Self {
        let skills_dir = std::env::var("HERMES_SKILLS_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                let mut p = std::env::var("HOME").map(PathBuf::from).unwrap_or_else(|_| PathBuf::from("."));
                p.push(".hermes/skills");
                p
            });
        let mut mgr = Self { skills: HashMap::new(), skills_dir };
        mgr.load_all().ok();
        mgr
    }

    /// Load all .md skill files from the skills directory.
    pub fn load_all(&mut self) -> std::io::Result<()> {
        self.skills.clear();
        if !self.skills_dir.exists() { return Ok(()); }

        for entry in walkdir(&self.skills_dir)? {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("md") {
                if let Ok(content) = std::fs::read_to_string(&path) {
                    let name = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
                    let skill = Self::parse_skill_md(&name, &content);
                    self.skills.insert(name, skill);
                }
            }
        }
        Ok(())
    }

    fn parse_skill_md(name: &str, content: &str) -> Skill {
        let mut description = String::new();
        let mut triggers = Vec::new();
        let mut tags = Vec::new();
        let mut category = None;

        for line in content.lines() {
            if line.starts_with("description:") {
                description = line.trim_start_matches("description:").trim().to_string();
            } else if line.starts_with("triggers:") {
                triggers = line.trim_start_matches("triggers:").split(',')
                    .map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect();
            } else if line.starts_with("tags:") {
                tags = line.trim_start_matches("tags:").split(',')
                    .map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect();
            } else if line.starts_with("category:") {
                category = Some(line.trim_start_matches("category:").trim().to_string());
            }
        }

        Skill {
            name: name.to_string(),
            category,
            description: if description.is_empty() { "No description".into() } else { description },
            content: content.to_string(),
            triggers,
            tags,
            created_at: chrono_now(),
            updated_at: chrono_now(),
        }
    }

    pub fn get(&self, name: &str) -> Option<&Skill> { self.skills.get(name) }

    pub fn list(&self) -> Vec<&Skill> { self.skills.values().collect() }

    pub fn search(&self, query: &str) -> Vec<&Skill> {
        let q = query.to_lowercase();
        self.skills.values().filter(|s| {
            s.name.to_lowercase().contains(&q)
            || s.description.to_lowercase().contains(&q)
            || s.tags.iter().any(|t| t.to_lowercase().contains(&q))
            || s.triggers.iter().any(|t| t.to_lowercase().contains(&q))
        }).collect()
    }

    pub fn save(&mut self, skill: Skill) -> Result<()> {
        let path = self.skills_dir.join(format!("{}.md", skill.name));
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&path, &skill.content)?;
        self.skills.insert(skill.name.clone(), skill);
        Ok(())
    }

    pub fn delete(&mut self, name: &str) -> Result<()> {
        let path = self.skills_dir.join(format!("{}.md", name));
        std::fs::remove_file(&path)?;
        self.skills.remove(name);
        Ok(())
    }

    pub fn update(&mut self, name: &str, content: &str) -> Result<()> {
        let skill = self.skills.get(name).cloned().ok_or_else(|| HighAgentError::Skill(format!("Skill '{}' not found", name)))?;
        let mut updated = skill;
        updated.content = content.to_string();
        updated.updated_at = chrono_now();
        self.save(updated)
    }

    /// Suggest a skill based on user intent.
    pub fn suggest(&self, intent: &str) -> Vec<&Skill> {
        self.search(intent)
    }

    /// Create skill from conversation content.
    pub fn create_from_content(&mut self, name: &str, description: &str, content: &str) -> Result<()> {
        let skill = Skill::new(name, description, content);
        self.save(skill)
    }
}

impl Default for SkillManager {
    fn default() -> Self { Self::new() }
}

fn walkdir(dir: &PathBuf) -> std::io::Result<Vec<std::fs::DirEntry>> {
    let mut results = Vec::new();
    let mut stack = vec![dir.clone()];
    while let Some(current) = stack.pop() {
        if let Ok(entries) = std::fs::read_dir(&current) {
            for entry in entries.flatten() {
                let ty = entry.file_type()?;
                if ty.is_dir() { stack.push(entry.path()); }
                else if ty.is_file() { results.push(entry); }
            }
        }
    }
    Ok(results)
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
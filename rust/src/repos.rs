//! Repository management — clone, fetch, sync, manage multiple repos.

use crate::error::{HighAgentError, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Repo {
    pub name: String,
    pub url: String,
    pub local_path: PathBuf,
    pub branch: String,
    pub status: RepoStatus,
    pub last_sync: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum RepoStatus {
    Clean,
    Dirty,
    Uninitialized,
    Error(String),
}

pub struct RepoManager {
    pub repos: HashMap<String, Repo>,
    pub config_file: PathBuf,
}

impl RepoManager {
    pub fn new() -> Self {
        let config_file = std::env::var("HOME").map(|h| {
            let mut p = PathBuf::from(h);
            p.push(".high-agent/repos.json");
            p
        }).unwrap_or_else(|_| PathBuf::from("~/.high-agent/repos.json"));

        let mut mgr = Self { repos: HashMap::new(), config_file };
        mgr.load().ok();
        mgr
    }

    pub fn add(&mut self, name: &str, url: &str, local_path: &str, branch: &str) -> Result<()> {
        let path = PathBuf::from(local_path);
        if path.exists() && path.join(".git").exists() {
            return Err(HighAgentError::Repo(format!("Path '{}' already exists and is a git repo", local_path)));
        }
        let repo = Repo {
            name: name.to_string(), url: url.to_string(), local_path: path,
            branch: branch.to_string(), status: RepoStatus::Uninitialized, last_sync: String::new(),
        };
        self.repos.insert(name.to_string(), repo);
        self.save()
    }

    pub fn clone_repo(&mut self, name: &str) -> Result<()> {
        let repo = self.repos.get_mut(name).ok_or_else(|| HighAgentError::Repo(format!("Repo '{}' not found", name)))?;
        if repo.local_path.exists() { return Ok(()); }

        if let Some(parent) = repo.local_path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        let output = std::process::Command::new("git")
            .args(["clone", "--branch", &repo.branch, &repo.url, repo.local_path.to_str().unwrap()])
            .output()?;
        if !output.status.success() {
            repo.status = RepoStatus::Error(String::from_utf8_lossy(&output.stderr).to_string());
            return Err(HighAgentError::Repo(format!("Clone failed: {}", String::from_utf8_lossy(&output.stderr))));
        }
        repo.status = RepoStatus::Clean;
        repo.last_sync = chrono_now();
        self.save()
    }

    pub fn sync(&mut self, name: &str) -> Result<()> {
        let repo = self.repos.get_mut(name).ok_or_else(|| HighAgentError::Repo(format!("Repo '{}' not found", name)))?;
        if !repo.local_path.exists() { return self.clone_repo(name); }

        let output = std::process::Command::new("git")
            .current_dir(&repo.local_path)
            .args(["pull", "origin", &repo.branch])
            .output()?;
        if !output.status.success() {
            repo.status = RepoStatus::Error(String::from_utf8_lossy(&output.stderr).to_string());
            return Err(HighAgentError::Repo(format!("Sync failed: {}", String::from_utf8_lossy(&output.stderr))));
        }
        repo.status = RepoStatus::Clean;
        repo.last_sync = chrono_now();
        self.save()
    }

    pub fn status(&mut self, name: &str) -> Result<RepoStatus> {
        let repo = self.repos.get(name).ok_or_else(|| HighAgentError::Repo(format!("Repo '{}' not found", name)))?;
        if !repo.local_path.exists() { return Ok(RepoStatus::Uninitialized); }

        let output = std::process::Command::new("git")
            .current_dir(&repo.local_path)
            .args(["status", "--porcelain"])
            .output()?;
        let is_dirty = !String::from_utf8_lossy(&output.stdout).trim().is_empty();
        Ok(if is_dirty { RepoStatus::Dirty } else { RepoStatus::Clean })
    }

    pub fn list(&self) -> Vec<&Repo> { self.repos.values().collect() }

    pub fn remove(&mut self, name: &str) -> Result<()> {
        self.repos.remove(name).ok_or_else(|| HighAgentError::Repo(format!("Repo '{}' not found", name)))?;
        self.save()
    }

    pub fn load(&mut self) -> std::io::Result<()> {
        if !self.config_file.exists() { return Ok(()); }
        let data = std::fs::read_to_string(&self.config_file)?;
        self.repos = serde_json::from_str(&data).unwrap_or_default();
        Ok(())
    }

    pub fn save(&self) -> Result<()> {
        if let Some(parent) = self.config_file.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let json = serde_json::to_string_pretty(&self.repos)?;
        std::fs::write(&self.config_file, json)?;
        Ok(())
    }
}

impl Default for RepoManager {
    fn default() -> Self { Self::new() }
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
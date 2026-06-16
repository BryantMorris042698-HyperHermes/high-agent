//! Build manager — detect, run, and analyze build outputs across multiple languages.

use crate::error::{HighAgentError, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildConfig {
    pub name: String,
    pub command: String,
    pub working_dir: PathBuf,
    pub language: Language,
    pub watch_patterns: Vec<String>,
    pub env: HashMap<String, String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum Language {
    Rust,
    Python,
    Go,
    Node,
    JavaScript,
    TypeScript,
    C,
    Cpp,
    Java,
    Unknown,
}

impl Language {
    pub fn detect(path: &PathBuf) -> Self {
        if path.join("Cargo.toml").exists() { return Self::Rust; }
        if path.join("pyproject.toml").exists() || path.join("requirements.txt").exists() { return Self::Python; }
        if path.join("go.mod").exists() { return Self::Go; }
        if path.join("package.json").exists() { return Self::Node; }
        if path.join("tsconfig.json").exists() { return Self::TypeScript; }
        if path.join("pom.xml").exists() { return Self::Java; }
        if path.join("CMakeLists.txt").exists() { return Self::Cpp; }
        Self::Unknown
    }

    pub fn build_cmd(&self) -> &str {
        match self {
            Self::Rust => "cargo build",
            Self::Python => "python -m pip install -e .",
            Self::Go => "go build ./...",
            Self::Node | Self::JavaScript => "npm install && npm run build",
            Self::TypeScript => "npx tsc",
            Self::Java => "mvn compile",
            Self::Cpp => "cmake . && make",
            Self::C => "make",
            Self::Unknown => "echo 'No build system detected'",
        }
    }

    pub fn test_cmd(&self) -> &str {
        match self {
            Self::Rust => "cargo test",
            Self::Python => "pytest",
            Self::Go => "go test ./...",
            Self::Node | Self::JavaScript | Self::TypeScript => "npm test",
            Self::Java => "mvn test",
            Self::Cpp => "ctest",
            Self::C => "make test",
            Self::Unknown => "echo 'No test system detected'",
        }
    }

    pub fn clean_cmd(&self) -> &str {
        match self {
            Self::Rust => "cargo clean",
            Self::Python => "rm -rf build dist *.egg-info",
            Self::Go => "go clean",
            Self::Node | Self::JavaScript | Self::TypeScript => "rm -rf dist node_modules/.cache",
            Self::Java => "mvn clean",
            Self::Cpp => "make clean",
            Self::C => "make clean",
            Self::Unknown => "echo 'No clean command'",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildResult {
    pub success: bool,
    pub exit_code: i32,
    pub stdout: String,
    pub stderr: String,
    pub duration_ms: u64,
    pub timestamp: String,
    pub build_type: BuildType,
    pub warnings: usize,
    pub errors: usize,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum BuildType { Build, Test, Clean, Custom }

impl BuildResult {
    pub fn new(success: bool, exit_code: i32, stdout: String, stderr: String, duration_ms: u64, build_type: BuildType) -> Self {
        let warnings = stderr.lines().filter(|l| l.contains("warning")).count();
        let errors = stderr.lines().filter(|l| l.contains("error")).count();
        Self { success, exit_code, stdout, stderr, duration_ms, timestamp: chrono_now(), build_type, warnings, errors }
    }
}

pub struct BuildManager {
    pub configs: HashMap<String, BuildConfig>,
    pub last_result: Option<BuildResult>,
    pub history: Vec<BuildResult>,
}

impl BuildManager {
    pub fn new() -> Self {
        Self { configs: HashMap::new(), last_result: None, history: Vec::new() }
    }

    pub fn detect(&mut self, path: &str) -> Result<Language> {
        let path = PathBuf::from(path);
        let lang = Language::detect(&path);
        if lang != Language::Unknown {
            let config = BuildConfig {
                name: path.file_name().and_then(|s| s.to_str()).unwrap_or("project").to_string(),
                command: lang.build_cmd().to_string(),
                working_dir: path.clone(),
                language: lang,
                watch_patterns: vec![],
                env: HashMap::new(),
            };
            self.configs.insert(config.name.clone(), config);
        }
        Ok(lang)
    }

    pub fn build(&mut self, name: &str, custom_cmd: Option<&str>) -> Result<BuildResult> {
        let config = self.configs.get(name).ok_or_else(|| HighAgentError::Build(format!("Config '{}' not found", name)))?;
        let cmd = custom_cmd.unwrap_or(&config.command);

        let start = SystemTime::now();
        let output = std::process::Command::new("sh")
            .arg("-c")
            .arg(cmd)
            .current_dir(&config.working_dir)
            .envs(&config.env)
            .output()?;
        let duration = SystemTime::now().duration_since(start).unwrap_or_default().as_millis() as u64;

        let result = BuildResult::new(
            output.status.success(),
            output.status.code().unwrap_or(-1),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
            duration,
            if custom_cmd.is_some() { BuildType::Custom } else { BuildType::Build },
        );
        self.last_result = Some(result.clone());
        self.history.push(result.clone());
        if self.history.len() > 100 { self.history.remove(0); }
        Ok(result)
    }

    pub fn test(&mut self, name: &str) -> Result<BuildResult> {
        let config = self.configs.get(name).ok_or_else(|| HighAgentError::Build(format!("Config '{}' not found", name)))?;
        let start = SystemTime::now();
        let output = std::process::Command::new("sh")
            .arg("-c")
            .arg(config.language.test_cmd())
            .current_dir(&config.working_dir)
            .envs(&config.env)
            .output()?;
        let duration = SystemTime::now().duration_since(start).unwrap_or_default().as_millis() as u64;
        let result = BuildResult::new(
            output.status.success(), output.status.code().unwrap_or(-1),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
            duration, BuildType::Test,
        );
        self.last_result = Some(result.clone());
        self.history.push(result.clone());
        Ok(result)
    }

    pub fn clean(&mut self, name: &str) -> Result<BuildResult> {
        let config = self.configs.get(name).ok_or_else(|| HighAgentError::Build(format!("Config '{}' not found", name)))?;
        let start = SystemTime::now();
        let output = std::process::Command::new("sh")
            .arg("-c")
            .arg(config.language.clean_cmd())
            .current_dir(&config.working_dir)
            .envs(&config.env)
            .output()?;
        let duration = SystemTime::now().duration_since(start).unwrap_or_default().as_millis() as u64;
        let result = BuildResult::new(
            output.status.success(), output.status.code().unwrap_or(-1),
            String::from_utf8_lossy(&output.stdout).to_string(),
            String::from_utf8_lossy(&output.stderr).to_string(),
            duration, BuildType::Clean,
        );
        self.last_result = Some(result.clone());
        self.history.push(result.clone());
        Ok(result)
    }

    pub fn add_config(&mut self, config: BuildConfig) { self.configs.insert(config.name.clone(), config); }
    pub fn list_configs(&self) -> Vec<&BuildConfig> { self.configs.values().collect() }
}

impl Default for BuildManager {
    fn default() -> Self { Self::new() }
}

fn chrono_now() -> String {
    let dur = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
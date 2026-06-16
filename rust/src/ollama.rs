//! Ollama API integration — model management, generation, chat, and pull.

use crate::error::{HighAgentError, Result};
use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Debug, Clone, Default)]
pub struct OllamaClient {
    pub base_url: String,
    pub default_model: String,
    pub timeout: Duration,
}

impl OllamaClient {
    pub fn new(base_url: &str, default_model: &str) -> Self {
        Self {
            base_url: base_url.to_string(),
            default_model: default_model.to_string(),
            timeout: Duration::from_secs(120),
        }
    }

    pub fn default() -> Self {
        Self {
            base_url: std::env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost:11434".into()),
            default_model: std::env::var("OLLAMA_MODEL").unwrap_or_else(|_| "llama3.2:3b".into()),
            timeout: Duration::from_secs(120),
        }
    }

    /// Check if Ollama is running and reachable.
    pub async fn is_available(&self) -> bool {
        let client = reqwest::Client::new();
        client.get(format!("{}/api/tags", self.base_url))
            .timeout(Duration::from_secs(5))
            .send()
            .await
            .is_ok()
    }

    /// List available models.
    pub async fn list_models(&self) -> std::result::Result<Vec<ModelInfo>, HighAgentError> {
        let client = reqwest::Client::new();
        let resp = client.get(format!("{}/api/tags", self.base_url))
            .timeout(self.timeout)
            .send()
            .await?;
        let data: TagsResponse = resp.json().await?;
        Ok(data.models.into_iter().map(|m| ModelInfo {
            name: m.name,
            size: m.size,
            modified: m.modified,
            digest: m.digest,
        }).collect())
    }

    /// Pull a model from Ollama registry.
    pub async fn pull_model(&self, model: &str) -> std::result::Result<(), HighAgentError> {
        let client = reqwest::Client::new();
        let resp = client.post(format!("{}/api/pull", self.base_url))
            .json(&PullRequest { name: model.to_string() })
            .timeout(Duration::from_secs(3600)) // 1 hour for large models
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(HighAgentError::Ollama(format!("Pull failed: {}", resp.status())));
        }
        Ok(())
    }

    /// Generate text with a model.
    pub async fn generate(&self, prompt: &str, model: Option<&str>) -> std::result::Result<String, HighAgentError> {
        let model = model.unwrap_or(&self.default_model);
        let client = reqwest::Client::new();
        let req = GenerateRequest {
            model: model.to_string(),
            prompt: prompt.to_string(),
            stream: false,
            options: GenerateOptions { temperature: Some(0.7), num_predict: Some(512), ..Default::default() },
            system: Some("You are Graph_x_0x0, an AI agent that analyzes code architecture using graph theory. Be concise and specific.".into()),
        };
        let resp = client.post(format!("{}/api/generate", self.base_url))
            .json(&req)
            .timeout(self.timeout)
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(HighAgentError::Ollama(format!("Generate failed: {}", resp.status())));
        }
        let data: GenerateResponse = resp.json().await?;
        Ok(data.response)
    }

    /// Chat with a model.
    pub async fn chat(&self, messages: Vec<(String, String)>, model: Option<&str>) -> std::result::Result<String, HighAgentError> {
        let model = model.unwrap_or(&self.default_model);
        let client = reqwest::Client::new();
        let ollama_msgs: Vec<OllamaMessage> = messages.into_iter()
            .map(|(role, content)| OllamaMessage { role, content })
            .collect();
        let req = ChatRequest {
            model: model.to_string(),
            messages: ollama_msgs,
            stream: false,
            options: GenerateOptions { temperature: Some(0.7), num_predict: Some(512), ..Default::default() },
        };
        let resp = client.post(format!("{}/api/chat", self.base_url))
            .json(&req)
            .timeout(self.timeout)
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(HighAgentError::Ollama(format!("Chat failed: {}", resp.status())));
        }
        let data: ChatResponse = resp.json().await?;
        Ok(data.message.content)
    }

    /// Show model info.
    pub async fn show_model(&self, model: &str) -> std::result::Result<ModelShowResponse, HighAgentError> {
        let client = reqwest::Client::new();
        let resp = client.post(format!("{}/api/show", self.base_url))
            .json(&ShowRequest { name: model.to_string() })
            .timeout(self.timeout)
            .send()
            .await?;
        let data: ModelShowResponse = resp.json().await?;
        Ok(data)
    }

    /// Copy/rename a model.
    pub async fn copy_model(&self, src: &str, dst: &str) -> std::result::Result<(), HighAgentError> {
        let client = reqwest::Client::new();
        let resp = client.post(format!("{}/api/copy", self.base_url))
            .json(&CopyRequest { source: src.to_string(), destination: dst.to_string() })
            .timeout(self.timeout)
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(HighAgentError::Ollama(format!("Copy failed: {}", resp.status())));
        }
        Ok(())
    }

    /// Delete a model.
    pub async fn delete_model(&self, model: &str) -> std::result::Result<(), HighAgentError> {
        let client = reqwest::Client::new();
        let resp = client.delete(format!("{}/api/delete", self.base_url))
            .header("Content-Type", "application/json")
            .body(format!(r#"{{"name":"{}"}}"#, model))
            .timeout(self.timeout)
            .send()
            .await?;
        if !resp.status().is_success() {
            return Err(HighAgentError::Ollama(format!("Delete failed: {}", resp.status())));
        }
        Ok(())
    }
}

// ─── Request/Response types ──────────────────────────────────────────────────

#[derive(Debug, Serialize)]
struct PullRequest { name: String }

#[derive(Debug, Deserialize)]
struct TagsResponse { models: Vec<OllamaModelRaw> }

#[derive(Debug, Deserialize)]
struct OllamaModelRaw {
    name: String,
    size: u64,
    #[serde(rename = "modified_at")]
    modified: String,
    digest: String,
}

#[derive(Debug, Serialize)]
struct GenerateRequest {
    model: String,
    prompt: String,
    stream: bool,
    options: GenerateOptions,
    system: Option<String>,
}

#[derive(Debug, Serialize, Default)]
struct GenerateOptions {
    temperature: Option<f64>,
    num_predict: Option<i32>,
    top_p: Option<f64>,
    top_k: Option<i32>,
    repeat_penalty: Option<f64>,
}

#[derive(Debug, Deserialize)]
struct GenerateResponse { response: String, done: bool }

#[derive(Debug, Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<OllamaMessage>,
    stream: bool,
    options: GenerateOptions,
}

#[derive(Debug, Serialize, Deserialize)]
struct OllamaMessage { role: String, content: String }

#[derive(Debug, Deserialize)]
struct ChatResponse { message: OllamaMessage }

#[derive(Debug, Serialize)]
struct ShowRequest { name: String }

#[derive(Debug, Deserialize)]
struct ModelShowResponse {
    license: Option<String>,
    modelfile: Option<String>,
    parameters: Option<String>,
    template: Option<String>,
}

#[derive(Debug, Serialize)]
struct CopyRequest { source: String, destination: String }

// ─── Public types ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub name: String,
    pub size: u64,
    pub modified: String,
    pub digest: String,
}

impl ModelInfo {
    pub fn size_mb(&self) -> f64 { self.size as f64 / 1_048_576.0 }
    pub fn size_gb(&self) -> f64 { self.size as f64 / 1_073_741_824.0 }
}
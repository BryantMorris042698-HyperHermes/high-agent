//! Metrics — aggregates from graph snapshots for TUI display.

use crate::graph::{GraphSnapshot, DeviationAlert, DeviationDirection};
use crate::regime::{Regime, RegimeTransition};
use serde::{Deserialize, Serialize};

/// Unified metrics struct for TUI display and JSON state.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metrics {
    pub phi: f64,
    pub phi_formatted: String,
    pub q: f64,
    pub coupling: f64,
    pub mean_v: f64,
    pub max_v: f64,
    pub quality: f64,
    pub n_nodes: u32,
    pub n_edges: u32,
    pub n_modules: u32,
    pub regime: Regime,
    pub regime_str: String,
    pub phi_color: PhiColor,
    pub timestamp: String,
    pub phi_trend: Trend,
    pub q_trend: Trend,
    pub coupling_trend: Trend,
    pub v_trend: Trend,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum Trend { Up, Down, Stable }

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum PhiColor { Green, Yellow, Red }

impl Metrics {
    pub fn from_snapshot(snapshot: &GraphSnapshot, regime: Regime) -> Self {
        let (phi_color, trend) = Self::compute_phi_style(snapshot.phi);

        Self {
            phi: snapshot.phi,
            phi_formatted: format!("{:+.4}", snapshot.phi),
            q: snapshot.q,
            coupling: snapshot.coupling,
            mean_v: snapshot.mean_v,
            max_v: snapshot.max_v,
            quality: snapshot.quality,
            n_nodes: snapshot.n_nodes,
            n_edges: snapshot.n_edges,
            n_modules: snapshot.n_modules,
            regime,
            regime_str: regime.to_string(),
            phi_color,
            phi_trend: trend,
            q_trend: Trend::Stable,
            coupling_trend: Trend::Stable,
            v_trend: Trend::Stable,
            timestamp: chrono_now(),
        }
    }

    fn compute_phi_style(phi: f64) -> (PhiColor, Trend) {
        let color = if phi > 0.0 { PhiColor::Green }
            else if phi > -2.0 { PhiColor::Yellow }
            else { PhiColor::Red };
        let trend = if phi > 0.05 { Trend::Up }
            else if phi < -0.05 { Trend::Down }
            else { Trend::Stable };
        (color, trend)
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_default()
    }

    /// Write state to JSON file for TUI/daemon sharing.
    pub fn write_state(&self, path: &str) -> std::io::Result<()> {
        use std::io::Write;
        let json = self.to_json();
        let mut f = std::fs::File::create(path)?;
        f.write_all(json.as_bytes())?;
        Ok(())
    }

    /// Read state from JSON file.
    pub fn read_state(path: &str) -> Option<Self> {
        let content = std::fs::read_to_string(path).ok()?;
        serde_json::from_str(&content).ok()
    }
}

impl Default for Metrics {
    fn default() -> Self {
        Self {
            phi: 0.0, phi_formatted: "+0.0000".into(), q: 0.0, coupling: 0.0,
            mean_v: 0.0, max_v: 0.0, quality: 0.5, n_nodes: 0, n_edges: 0, n_modules: 0,
            regime: Regime::default(), regime_str: "Simple".into(),
            phi_color: PhiColor::Yellow, phi_trend: Trend::Stable,
            q_trend: Trend::Stable, coupling_trend: Trend::Stable, v_trend: Trend::Stable,
            timestamp: chrono_now(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct History {
    pub entries: Vec<HistoryEntry>,
    pub transitions: Vec<RegimeTransition>,
}

impl History {
    pub fn new() -> Self { Self::default() }
    pub fn push_snapshot(&mut self, metrics: &Metrics) {
        self.entries.push(HistoryEntry {
            phi: metrics.phi, q: metrics.q, coupling: metrics.coupling,
            mean_v: metrics.mean_v, regime: metrics.regime_str.clone(),
            timestamp: metrics.timestamp.clone(),
        });
        if self.entries.len() > 200 { self.entries.remove(0); }
    }
    pub fn push_transition(&mut self, t: RegimeTransition) {
        self.transitions.push(t);
    }
    pub fn recent(&self, n: usize) -> Vec<&HistoryEntry> {
        self.entries.iter().rev().take(n).collect()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HistoryEntry {
    pub phi: f64,
    pub q: f64,
    pub coupling: f64,
    pub mean_v: f64,
    pub regime: String,
    pub timestamp: String,
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}
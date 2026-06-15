//! Regime definitions and coefficient profiles.

use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct RegimeCoeffs {
    pub alpha: f64,
    pub beta: f64,
    pub gamma: f64,
}

impl RegimeCoeffs {
    pub const SIMPLE: Self = Self { alpha: 0.8, beta: 0.9, gamma: 0.2 };
    pub const ADVANCED: Self = Self { alpha: 1.2, beta: 0.5, gamma: 0.3 };
    pub const HYBRID: Self = Self { alpha: 1.0, beta: 0.6, gamma: 0.4 };
}

impl Default for RegimeCoeffs {
    fn default() -> Self { Self::HYBRID }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash, Default)]
pub enum Regime {
    #[default]
    Simple,
    Advanced,
    Hybrid,
}

impl Regime {
    pub fn coeffs(self) -> RegimeCoeffs {
        match self {
            Self::Simple => RegimeCoeffs::SIMPLE,
            Self::Advanced => RegimeCoeffs::ADVANCED,
            Self::Hybrid => RegimeCoeffs::HYBRID,
        }
    }
    pub fn description(self) -> &'static str {
        match self {
            Self::Simple => "Minimize coupling. Fast iteration.",
            Self::Advanced => "Maximize modularity. PR review mode.",
            Self::Hybrid => "Balance all terms. Team handoff mode.",
        }
    }
    pub fn all() -> [Self; 3] { [Self::Simple, Self::Advanced, Self::Hybrid] }
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "simple" => Some(Self::Simple), "advanced" => Some(Self::Advanced),
            "hybrid" => Some(Self::Hybrid), _ => None,
        }
    }
}

impl fmt::Display for Regime {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self { Self::Simple => write!(f, "Simple"), Self::Advanced => write!(f, "Advanced"), Self::Hybrid => write!(f, "Hybrid") }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegimeTransition {
    pub from: Regime,
    pub to: Regime,
    pub reason: String,
    pub phi_before: f64,
    pub phi_after: f64,
    pub timestamp: String,
}

impl RegimeTransition {
    pub fn new(from: Regime, to: Regime, reason: &str, phi_before: f64, phi_after: f64) -> Self {
        Self { from, to, reason: reason.to_string(), phi_before, phi_after, timestamp: chrono_now() }
    }
    pub fn improvement(&self) -> f64 { self.phi_after - self.phi_before }
}

fn chrono_now() -> String {
    let dur = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap_or_default();
    format!("{}.{:09}", dur.as_secs(), dur.subsec_nanos())
}

pub const HYSTERESIS_MARGIN: f64 = 0.05;
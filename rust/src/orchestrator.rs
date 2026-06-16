//! Orchestrator — piecewise regime switching logic.

use crate::error::{HighAgentError, Result};
use crate::graph::{DirectedGraph, GraphSnapshot, SegmentedRegimeDetector};
use crate::regime::{HYSTERESIS_MARGIN, Regime, RegimeCoeffs, RegimeTransition};

pub struct Orchestrator {
    pub current_regime: Regime,
    pub detector: SegmentedRegimeDetector,
}

impl Orchestrator {
    pub fn new() -> Self {
        Self {
            current_regime: Regime::default(),
            detector: SegmentedRegimeDetector::new(10, 2.0),
        }
    }

    /// Evaluate all 3 regimes against the current graph, return the best one.
    pub fn best_regime(&self, graph: &DirectedGraph) -> (Regime, f64) {
        let mut best = (Regime::Simple, f64::NEG_INFINITY);
        for regime in Regime::all() {
            let phi = graph.phi_regime(regime);
            if phi > best.1 { best = (regime, phi); }
        }
        best
    }

    /// Evaluate and switch if the best regime beats current by hysteresis margin.
    pub fn evaluate_and_switch(&mut self, graph: &DirectedGraph) -> Option<RegimeTransition> {
        let (best_regime, best_phi) = self.best_regime(graph);
        let current_phi = graph.phi_regime(self.current_regime);

        if best_regime != self.current_regime && (best_phi - current_phi) > HYSTERESIS_MARGIN {
            let transition = RegimeTransition::new(
                self.current_regime, best_regime,
                &format!("Φ improved by {:.4} > hysteresis {:.4}", best_phi - current_phi, HYSTERESIS_MARGIN),
                current_phi, best_phi,
            );
            self.current_regime = best_regime;
            return Some(transition);
        }
        None
    }

    /// Feed detector, and if deviation detected, re-evaluate regime.
    pub fn detect_and_switch(&mut self, graph: &DirectedGraph) -> (Option<RegimeTransition>, Option<crate::graph::DeviationAlert>) {
        let snapshot = graph.snapshot_full(self.current_regime);
        let alert = self.detector.feed(snapshot);
        let transition = self.evaluate_and_switch(graph);
        (transition, alert)
    }

    pub fn set_regime(&mut self, regime: Regime) { self.current_regime = regime; }
    pub fn reset_detector(&mut self) { self.detector.clear(); }
}
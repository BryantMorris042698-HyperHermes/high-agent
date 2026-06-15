"""Regime definitions — mirrors Rust regime.rs."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class RegimeCoeffs:
    alpha: float
    beta: float
    gamma: float

RegimeCoeffs.SIMPLE = RegimeCoeffs(0.8, 0.9, 0.2)
RegimeCoeffs.ADVANCED = RegimeCoeffs(1.2, 0.5, 0.3)
RegimeCoeffs.HYBRID = RegimeCoeffs(1.0, 0.6, 0.4)

class Regime:
    SIMPLE = "simple"
    ADVANCED = "advanced"
    HYBRID = "hybrid"

    @staticmethod
    def coeffs(r: str) -> RegimeCoeffs:
        return {"simple": RegimeCoeffs.SIMPLE, "advanced": RegimeCoeffs.ADVANCED, "hybrid": RegimeCoeffs.HYBRID}.get(r, RegimeCoeffs.HYBRID)

    @staticmethod
    def description(r: str) -> str:
        return {"simple": "Minimize coupling. Fast iteration.", "advanced": "Maximize modularity. PR review mode.", "hybrid": "Balance all terms. Team handoff mode."}.get(r, "")

    @staticmethod
    def all() -> list:
        return ["simple", "advanced", "hybrid"]

    @staticmethod
    def default() -> str:
        return "hybrid"

    @staticmethod
    def from_str(s: str) -> Optional[str]:
        s = s.lower()
        return s if s in ("simple", "advanced", "hybrid") else None

HYSTERESIS_MARGIN = 0.05

class RegimeTransition:
    def __init__(self, from_: str, to: str, reason: str, phi_before: float, phi_after: float):
        self.from_ = from_
        self.to = to
        self.reason = reason
        self.phi_before = phi_before
        self.phi_after = phi_after
        self.timestamp = f"{time.time():.9f}"

    def improvement(self) -> float:
        return self.phi_after - self.phi_before
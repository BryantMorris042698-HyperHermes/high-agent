"""Daemon — background evaluation daemon, writes JSON for TUI."""

from __future__ import annotations
import json
import os
import signal
import sys
import time
from .engine import RegimeEngine

STATE_FILE = os.path.expanduser("~/.high-agent/state.json")

class Daemon:
    def __init__(self, interval: int = 5):
        self.interval = interval
        self.engine = RegimeEngine()
        self.running = True

    def start(self) -> None:
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)
        self.engine.seed_graph()
        print(f"Daemon started. Writing state to {STATE_FILE} every {self.interval}s")
        print("Press Ctrl+C to stop.")
        counter = 0
        while self.running:
            self.engine.update_metrics()
            self.engine.write_state(STATE_FILE)
            counter += 1
            print(f"[{counter}] Φ(G)={self.engine.metrics.phi:+.4f} regime={self.engine.metrics.regime}")
            time.sleep(self.interval)
            # Simulate changes
            if counter % 3 == 0:
                self.engine.process_task("refactor")
            elif counter % 5 == 0:
                self.engine.process_task("test")
            t, _ = self.engine.detect_and_evaluate()
            if t:
                print(f"  Regime switched: {t.from_} → {t.to}")
        print("Daemon stopped.")

    def _stop(self, signum, frame) -> None:
        self.running = False


if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    Daemon(interval).start()
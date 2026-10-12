"""Deterministic Conway Automaton Engine for QICP Decentralized Governance.

Implements a deterministic 2D toroidal cellular automaton (Game of Life and
weighted multi-state extensions) to model peer consensus, neighborhood review
dynamics, and algorithmic grant velocity.

Zero simulation or random numbers: Every transition is completely deterministic
and rooted in on-chain block/proposal cryptographic hashes.
"""
import hashlib
import struct
from typing import Dict, List, Tuple
import numpy as np


class ConwayGovernanceAutomaton:
    """Deterministic Toroidal Conway Automaton for Community Governance."""

    def __init__(self, width: int = 32, height: int = 32, seed_hash: bytes = None):
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=np.uint8)
        self.step_count = 0
        if seed_hash:
            self.seed_from_hash(seed_hash)

    def seed_from_hash(self, seed_hash: bytes) -> None:
        """Deterministically initialize grid from a cryptographic hash."""
        # Expand 32-byte hash using SHAKE-256 to cover all cells
        expanded = hashlib.shake_256(seed_hash).digest(self.width * self.height)
        arr = np.frombuffer(expanded, dtype=np.uint8)
        # Threshold at 128 for ~50% initial alive cells
        self.grid = (arr >= 128).astype(np.uint8).reshape((self.height, self.width))
        self.step_count = 0

    def step(self) -> Tuple[np.ndarray, str]:
        """Evolve the automaton by one deterministic generation using standard B3/S23 rules."""
        # Toroidal 8-neighborhood convolution
        neighbors = (
            np.roll(np.roll(self.grid, 1, 0), 1, 1) +
            np.roll(np.roll(self.grid, 1, 0), 0, 1) +
            np.roll(np.roll(self.grid, 1, 0), -1, 1) +
            np.roll(np.roll(self.grid, 0, 0), 1, 1) +
            np.roll(np.roll(self.grid, 0, 0), -1, 1) +
            np.roll(np.roll(self.grid, -1, 0), 1, 1) +
            np.roll(np.roll(self.grid, -1, 0), 0, 1) +
            np.roll(np.roll(self.grid, -1, 0), -1, 1)
        )

        # Standard B3 / S23 rules
        birth = (neighbors == 3) & (self.grid == 0)
        survive = ((neighbors == 2) | (neighbors == 3)) & (self.grid == 1)

        self.grid = (birth | survive).astype(np.uint8)
        self.step_count += 1
        return self.grid, self.get_state_hash()

    def get_state_hash(self) -> str:
        """Compute SHA-256 digest of current lattice state and step count."""
        raw_state = self.grid.tobytes() + struct.pack(">Q", self.step_count)
        return hashlib.sha256(raw_state).hexdigest()

    def get_governance_metrics(self) -> Dict[str, float]:
        """Derive objective mathematical metrics from automaton state:
        - density: proportion of active peer cells [0, 1]
        - stability: entropy of active cluster distribution
        - grant_velocity_factor: multiplier for community proposal velocity [0.5, 2.0]
        """
        total_cells = self.width * self.height
        active_count = int(np.sum(self.grid))
        density = active_count / total_cells

        # Calculate local cluster variance for entropy
        subgrid_sums = []
        for r in range(0, self.height, 4):
            for c in range(0, self.width, 4):
                subgrid_sums.append(int(np.sum(self.grid[r:r+4, c:c+4])))

        counts = np.array(subgrid_sums, dtype=np.float64)
        total_sum = np.sum(counts)
        if total_sum > 0:
            probs = counts / total_sum
            probs = probs[probs > 0]
            entropy = -float(np.sum(probs * np.log2(probs)))
        else:
            entropy = 0.0

        # Algorithmic Grant Velocity Factor:
        # Dynamic response bounded between 0.5x and 2.0x based on active consensus density
        velocity_factor = float(np.clip(0.5 + 3.0 * density * (1.0 - density), 0.5, 2.0))

        return {
            "step": self.step_count,
            "active_nodes": active_count,
            "density": round(density, 4),
            "entropy": round(entropy, 4),
            "velocity_factor": round(velocity_factor, 4),
            "state_hash": self.get_state_hash(),
        }


if __name__ == "__main__":
    print("Testing Deterministic Conway Governance Automaton...")
    proposal_hash = hashlib.sha256(b"proposal-inclusion-grant-delhi-001").digest()
    auto = ConwayGovernanceAutomaton(width=32, height=32, seed_hash=proposal_hash)
    metrics_0 = auto.get_governance_metrics()
    print(f"Gen 0: Active={metrics_0['active_nodes']}, Density={metrics_0['density']}, VelocityFactor={metrics_0['velocity_factor']}")

    for _ in range(5):
        auto.step()

    metrics_5 = auto.get_governance_metrics()
    print(f"Gen 5: Active={metrics_5['active_nodes']}, Density={metrics_5['density']}, VelocityFactor={metrics_5['velocity_factor']}")
    print(f"State Hash (Gen 5): {metrics_5['state_hash']}")

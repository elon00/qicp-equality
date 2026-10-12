# Deterministic Conway Automaton Consensus Engine

## 1. Mathematical Concept

The **Conway Automaton Governance Engine** models decentralized peer review, neighborhood consensus, and community grant velocity through a deterministic 2D cellular automaton.

Instead of relying on centralized committee votes or vulnerable off-chain random number generators (RNGs), QICP derives mathematical consensus velocity from an evolving 32x32 toroidal grid initialized from cryptographic on-chain hashes.

---

## 2. Grid Geometry & Boundary Conditions

- **Grid Dimensions**: $W = 32$, $H = 32$ (Total cells: 1,024).
- **Lattice Topology**: 2D Torus (periodic boundary conditions).
  For any coordinate $(r, c)$:
  $$r_{\text{neighbor}} = (r + \Delta r) \pmod{32}$$
  $$c_{\text{neighbor}} = (c + \Delta c) \pmod{32}$$
  where $\Delta r, \Delta c \in \{-1, 0, 1\} \setminus \{(0, 0)\}$.

---

## 3. Transition Dynamics (B3/S23)

At each discrete generation $t \to t+1$, every cell $c_{i,j}^{(t)} \in \{0, 1\}$ transitions according to its Moore 8-neighborhood sum:

$$k_{i,j} = \sum_{\Delta r = -1}^1 \sum_{\Delta c = -1}^1 c_{i+\Delta r, \; j+\Delta c}^{(t)} - c_{i,j}^{(t)}$$

1. **Birth**: If $c_{i,j}^{(t)} = 0$ and $k_{i,j} = 3 \implies c_{i,j}^{(t+1)} = 1$.
2. **Survival**: If $c_{i,j}^{(t)} = 1$ and $k_{i,j} \in \{2, 3\} \implies c_{i,j}^{(t+1)} = 1$.
3. **Death (Underpopulation / Overpopulation)**: Otherwise $\implies c_{i,j}^{(t+1)} = 0$.

---

## 4. Derived Governance Metrics

### 4.1 Active Density ($\rho$)
$$\rho = \frac{\sum_{i=1}^{32} \sum_{j=1}^{32} c_{i,j}}{1024}$$

### 4.2 Algorithmic Velocity Factor ($V_{\text{conway}}$)
The velocity factor dampens sudden capital outflows during chaotic or fragmented governance states and accelerates disbursements during dense, stable consensus:

$$V_{\text{conway}} = \text{clamp}\left(0.5 + 3.0 \cdot \rho \cdot (1 - \rho), \; 0.5, \; 2.0\right)$$

### 4.3 State Hash Verification
Each step emits an immutable SHA-256 state digest:
$$\mathcal{H}_t = \text{SHA-256}\left(\text{Grid}_t \parallel \text{uint64}(t)\right)$$

This guarantees that any validator, canister, or client can independently recompute and verify the exact governance state across the Internet Computer.

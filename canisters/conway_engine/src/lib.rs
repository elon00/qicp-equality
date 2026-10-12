//! QICP Conway Automaton Engine Canister (Rust / ic-cdk)
//! Implements deterministic 32x32 toroidal cellular automaton for community consensus metrics.

use candid::{CandidType, Deserialize};

const WIDTH: usize = 32;
const HEIGHT: usize = 32;

#[derive(CandidType, Deserialize, Clone, Debug)]
pub struct ConwayMetrics {
    pub step: u32,
    pub active_nodes: u32,
    pub density: f32,
    pub velocity_factor: f32,
    pub state_hash: String,
}

pub struct ConwayState {
    pub grid: [[u8; WIDTH]; HEIGHT],
    pub step: u32,
}

impl Default for ConwayState {
    fn default() -> Self {
        Self {
            grid: [[0; WIDTH]; HEIGHT],
            step: 0,
        }
    }
}

static mut CONWAY_STATE: Option<ConwayState> = None;

pub fn get_conway() -> &'static mut ConwayState {
    unsafe {
        if CONWAY_STATE.is_none() {
            CONWAY_STATE = Some(ConwayState::default());
        }
        CONWAY_STATE.as_mut().unwrap()
    }
}

#[ic_cdk::update]
pub fn init_automaton(seed_text: String) -> ConwayMetrics {
    let c = get_conway();
    let hash = ic_cdk::api::crypto::sha256(seed_text.as_bytes());

    for r in 0..HEIGHT {
        for col in 0..WIDTH {
            let idx = (r * WIDTH + col) % hash.len();
            c.grid[r][col] = if hash[idx] >= 128 { 1 } else { 0 };
        }
    }
    c.step = 0;
    calculate_metrics()
}

#[ic_cdk::update]
pub fn step_automaton(steps: u32) -> ConwayMetrics {
    let c = get_conway();
    for _ in 0..steps {
        let mut next = [[0u8; WIDTH]; HEIGHT];
        for r in 0..HEIGHT {
            for col in 0..WIDTH {
                let mut neighbors = 0;
                for dr in [-1, 0, 1] {
                    for dc in [-1, 0, 1] {
                        if dr == 0 && dc == 0 {
                            continue;
                        }
                        let nr = (r as isize + dr).rem_euclid(HEIGHT as isize) as usize;
                        let nc = (col as isize + dc).rem_euclid(WIDTH as isize) as usize;
                        neighbors += c.grid[nr][nc];
                    }
                }
                let alive = c.grid[r][col] == 1;
                if alive && (neighbors == 2 || neighbors == 3) {
                    next[r][col] = 1;
                } else if !alive && neighbors == 3 {
                    next[r][col] = 1;
                } else {
                    next[r][col] = 0;
                }
            }
        }
        c.grid = next;
        c.step += 1;
    }
    calculate_metrics()
}

#[ic_cdk::query]
pub fn get_current_metrics() -> ConwayMetrics {
    calculate_metrics()
}

fn calculate_metrics() -> ConwayMetrics {
    let c = get_conway();
    let mut active = 0u32;
    for r in 0..HEIGHT {
        for col in 0..WIDTH {
            if c.grid[r][col] == 1 {
                active += 1;
            }
        }
    }
    let total = (WIDTH * HEIGHT) as f32;
    let density = active as f32 / total;
    let velocity = (0.5 + 3.0 * density * (1.0 - density)).clamp(0.5, 2.0);

    let state_bytes: Vec<u8> = c.grid.iter().flat_map(|row| row.iter()).cloned().collect();
    let hash = ic_cdk::api::crypto::sha256(&state_bytes);
    let state_hash = hash.iter().map(|b| format!("{:02x}", b)).collect();

    ConwayMetrics {
        step: c.step,
        active_nodes: active,
        density,
        velocity_factor: velocity,
        state_hash,
    }
}

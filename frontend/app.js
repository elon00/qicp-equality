// QICP Equality Frontend Client Logic

let activeTab = 'grants';
let conwayMetrics = {
  step: 0,
  active_nodes: 0,
  density: 0.0,
  velocity_factor: 1.0,
  state_hash: 'computing...'
};

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initConwayCanvas();
  fetchConwayMetrics();
  fetchProposals();
  initProposalCapListener();
  initForms();
  initWalletModal();
});

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      activeTab = tab.dataset.tab;
      const targetPane = document.getElementById(`tab-${activeTab}`);
      if (targetPane) targetPane.classList.add('active');
    });
  });
}

// Conway Automaton Visualizer
let conwayCanvas, conwayCtx;
const GRID_SIZE = 32;

function initConwayCanvas() {
  conwayCanvas = document.getElementById('conway-canvas');
  if (!conwayCanvas) return;
  conwayCtx = conwayCanvas.getContext('2d');

  document.getElementById('conway-step-btn').addEventListener('click', async () => {
    const res = await fetch('/api/conway/step?steps=1', { method: 'POST' });
    if (res.ok) {
      conwayMetrics = await res.json();
      updateConwayUI();
      drawRandomizedConwayGrid(conwayMetrics.density);
    }
  });

  document.getElementById('conway-reseed-btn').addEventListener('click', async () => {
    const seed = 'qicp-reseed-' + Date.now();
    const res = await fetch('/api/conway/init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed_text: seed })
    });
    if (res.ok) {
      conwayMetrics = await res.json();
      updateConwayUI();
      drawRandomizedConwayGrid(conwayMetrics.density);
    }
  });
}

async function fetchConwayMetrics() {
  try {
    const res = await fetch('/api/conway/metrics');
    if (res.ok) {
      conwayMetrics = await res.json();
      updateConwayUI();
      drawRandomizedConwayGrid(conwayMetrics.density);
    }
  } catch (e) {
    console.error('Failed to fetch initial conway metrics:', e);
  }
}

function updateConwayUI() {
  document.getElementById('stat-active-nodes').innerText = `${conwayMetrics.active_nodes} Active Nodes`;
  document.getElementById('stat-velocity').innerText = `Conway Velocity: ${conwayMetrics.velocity_factor}x`;
  document.getElementById('conway-step-num').innerText = conwayMetrics.step;
  document.getElementById('conway-active-num').innerText = conwayMetrics.active_nodes;
  document.getElementById('conway-density-num').innerText = (conwayMetrics.density * 100).toFixed(2) + '%';
  document.getElementById('conway-velocity-num').innerText = conwayMetrics.velocity_factor + 'x';
  document.getElementById('conway-hash-num').innerText = conwayMetrics.state_hash;
}

function drawRandomizedConwayGrid(density) {
  if (!conwayCtx) return;
  const cellSize = conwayCanvas.width / GRID_SIZE;
  conwayCtx.fillStyle = '#03080e';
  conwayCtx.fillRect(0, 0, conwayCanvas.width, conwayCanvas.height);

  for (let r = 0; r < GRID_SIZE; r++) {
    for (let c = 0; c < GRID_SIZE; c++) {
      // Deterministic visual projection from hash
      const hashByte = parseInt(conwayMetrics.state_hash.substr((r * 2) % 30, 2), 16) || 0;
      const isAlive = (hashByte / 255.0) < density || ((r + c + conwayMetrics.step) % 5 === 0);
      if (isAlive) {
        conwayCtx.fillStyle = '#00d2ff';
        conwayCtx.fillRect(c * cellSize + 1, r * cellSize + 1, cellSize - 2, cellSize - 2);
      }
    }
  }
}

// Community Grant Proposals
function initProposalCapListener() {
  const benInput = document.getElementById('prop-beneficiaries');
  const amountInput = document.getElementById('prop-amount');
  const display = document.getElementById('cap-calc-display');

  const updateCap = async () => {
    const ben = parseInt(benInput.value) || 0;
    const req = parseFloat(amountInput.value) || 0;
    if (ben <= 0) return;

    try {
      const res = await fetch('/api/tokenomics/community-cap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ verified_beneficiaries: ben, velocity_factor: conwayMetrics.velocity_factor })
      });
      if (res.ok) {
        const data = await res.json();
        const cap = data.grant_cap_qicp;
        const valid = req <= cap;
        display.innerHTML = `Quadratic Cap: <strong>${cap.toLocaleString()} QICP</strong> (${data.per_capita_effective_qicp.toLocaleString()} per capita) | Status: <span style="color:${valid ? '#00e676' : '#ff5252'}">${valid ? 'ELIGIBLE' : 'EXCEEDED'}</span>`;
      }
    } catch (e) {
      console.error(e);
    }
  };

  benInput.addEventListener('input', updateCap);
  amountInput.addEventListener('input', updateCap);
  updateCap();
}

async function fetchProposals() {
  const container = document.getElementById('proposals-list');
  try {
    const res = await fetch('/api/proposals/list');
    if (res.ok) {
      const list = await res.json();
      if (list.length === 0) {
        container.innerHTML = '<div class="empty-state">No proposals submitted yet. Be the first to apply!</div>';
        return;
      }
      container.innerHTML = list.map(p => `
        <div class="proposal-item" style="background:#112238; border:1px solid #1a2f4c; border-radius:8px; padding:1rem; margin-bottom:0.75rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="color:#fff;">${p.title}</strong>
            <span class="badge success">${p.category}</span>
          </div>
          <p style="font-size:0.85rem; color:#8ca2ba; margin:0.35rem 0;">${p.description}</p>
          <div style="font-size:0.8rem; display:flex; justify-content:space-between;">
            <span>Requested: <strong>${p.requested_amount_qicp.toLocaleString()} QICP</strong></span>
            <span>Target: <em>${p.target_community}</em> (${p.beneficiary_count} people)</span>
          </div>
        </div>
      `).join('');
    }
  } catch (e) {
    container.innerHTML = '<div class="empty-state">Unable to load proposals.</div>';
  }
}

// Form Handlers
function initForms() {
  // Proposal Submit
  document.getElementById('proposal-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById('prop-title').value,
      category: document.getElementById('prop-category').value,
      target_community: document.getElementById('prop-community').value,
      beneficiary_count: parseInt(document.getElementById('prop-beneficiaries').value),
      requested_amount_qicp: parseFloat(document.getElementById('prop-amount').value),
      description: document.getElementById('prop-desc').value,
      proposer_principal: document.getElementById('prop-principal').value
    };

    const res = await fetch('/api/proposals/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert('Proposal submitted successfully to Treasury escrow!');
      fetchProposals();
      document.getElementById('proposal-form').reset();
    } else {
      const err = await res.json();
      alert('Failed to submit proposal: ' + JSON.stringify(err));
    }
  });

  // QR Form
  document.getElementById('qr-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      currency: document.getElementById('qr-currency').value,
      recipient_address: document.getElementById('qr-recipient').value,
      amount: parseFloat(document.getElementById('qr-amount').value) || null,
      memo: document.getElementById('qr-memo').value || null
    };

    const res = await fetch('/api/qr/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      const img = document.getElementById('qr-image');
      img.src = data.qr_data_uri;
      img.style.display = 'block';
      document.getElementById('qr-uri-text').innerText = data.payment_uri;
    }
  });

  // AI Chat Form
  document.getElementById('chat-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    appendChatMessage('user', msg);
    input.value = '';

    const model = document.getElementById('ai-model-select').value;
    try {
      const res = await fetch('/api/ai/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: msg, target_model: model })
      });
      if (res.ok) {
        const data = await res.json();
        appendChatMessage('bot', data.response, data.cryptographic_proof);
      }
    } catch (err) {
      appendChatMessage('bot', 'AI Agent query failed. Please check network.');
    }
  });

  // Demurrage Form
  document.getElementById('demurrage-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const bal = parseFloat(document.getElementById('dem-balance').value);
    const days = parseInt(document.getElementById('dem-days').value);

    const res = await fetch('/api/tokenomics/demurrage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ balance_qicp: bal, inactive_days: days })
    });
    if (res.ok) {
      const data = await res.json();
      const box = document.getElementById('demurrage-results');
      box.style.display = 'block';
      box.innerHTML = `
        <div class="metric-row"><span>Excess Speculative Balance:</span><strong>${data.excess_balance_qicp.toLocaleString()} QICP</strong></div>
        <div class="metric-row"><span>Total Algorithmic Decay:</span><strong style="color:#ff5252;">${data.decay_qicp.toLocaleString()} QICP</strong></div>
        <div class="metric-row"><span>Permanently Burned (50%):</span><strong>${data.burned_qicp.toLocaleString()} QICP</strong></div>
        <div class="metric-row"><span>Recycled to Treasury (50%):</span><strong style="color:#00e676;">${data.recycled_to_treasury_qicp.toLocaleString()} QICP</strong></div>
        <div class="metric-row"><span>Final Retained Balance:</span><strong>${data.post_decay_balance_qicp.toLocaleString()} QICP</strong></div>
      `;
    }
  });
}

function appendChatMessage(sender, text, proof) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${sender}`;

  let header = '';
  if (sender === 'bot') {
    header = `<div class="msg-header">QICP AI AGENT <span class="badge pqc">NIST ML-DSA-65</span></div>`;
  }
  let proofHtml = '';
  if (proof && proof.pqc_signature_hex) {
    proofHtml = `<div style="font-size:0.7rem; color:#8ca2ba; margin-top:0.35rem;">PQC Lattice Proof: <code>${proof.pqc_signature_hex.substr(0, 24)}...</code></div>`;
  }

  div.innerHTML = `${header}<p>${text}</p>${proofHtml}`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// Wallet Modal
function initWalletModal() {
  const modal = document.getElementById('wallet-modal');
  document.getElementById('connect-wallet-btn').addEventListener('click', () => {
    modal.style.display = 'flex';
  });
  document.getElementById('close-modal-btn').addEventListener('click', () => {
    modal.style.display = 'none';
  });
}

function handleWalletSelect(name) {
  const btn = document.getElementById('connect-wallet-btn');
  btn.innerText = `Connected (${name})`;
  btn.classList.remove('btn-primary');
  btn.classList.add('btn-secondary');
  document.getElementById('wallet-modal').style.display = 'none';
}

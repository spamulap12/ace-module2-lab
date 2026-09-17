const API_BASE = 'http://localhost:8000/api';

let sessionId = null;
let currentPhase = 1;
let currentKPIs = { morale: 70.0, productivity: 80.0, burnout_risk: 30.0 };
let activeMemos = [];
let isSimulationComplete = false;
let scorecardData = null;

document.addEventListener('DOMContentLoaded', () => {
  initSession();

  document.getElementById('send-btn').addEventListener('click', handleSendMessage);
  document.getElementById('message-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  document.getElementById('reset-btn').addEventListener('click', resetSimulation);
  document.getElementById('close-memo-modal').addEventListener('click', closeMemoModal);
  document.getElementById('close-memo-btn').addEventListener('click', closeMemoModal);
  document.getElementById('close-scorecard-modal').addEventListener('click', closeScorecardModal);
  document.getElementById('close-scorecard-btn').addEventListener('click', closeScorecardModal);
  document.getElementById('open-scorecard-btn').addEventListener('click', () => {
    if (scorecardData) renderScorecardModal(scorecardData);
  });
});

async function initSession() {
  try {
    const res = await fetch(`${API_BASE}/start`, { method: 'POST' });
    const data = await res.json();

    sessionId = data.session_id;
    currentPhase = data.current_phase;
    currentKPIs = data.kpis;
    activeMemos = data.memos;

    document.getElementById('session-id-display').innerText = `Session: ${sessionId.substring(0, 8)}...`;
    
    // Clear chat and render initial Agent message
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = '';
    appendChatMessage('agent', data.initial_message, 1);

    updateKPIBars(currentKPIs, { morale: 0, productivity: 0, burnout_risk: 0 });
    updatePhaseStepper(currentPhase);
    renderMemosList(activeMemos);
  } catch (err) {
    console.error('Failed to initialize simulation session:', err);
  }
}

async function handleSendMessage() {
  const inputEl = document.getElementById('message-input');
  const message = inputEl.value.trim();
  if (!message || isSimulationComplete) return;

  // Append user message immediately
  appendChatMessage('user', message, currentPhase);
  inputEl.value = '';

  // Show typing indicator
  showTypingIndicator(true);

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: message })
    });

    const data = await res.json();
    showTypingIndicator(false);

    currentPhase = data.current_phase;
    currentKPIs = data.kpis;
    isSimulationComplete = data.is_completed;

    // Append Agent response
    appendChatMessage('agent', data.agent_message, currentPhase);

    // Update KPI bars & show deltas
    updateKPIBars(currentKPIs, data.kpi_deltas);
    updatePhaseStepper(currentPhase);

    if (isSimulationComplete) {
      document.getElementById('eval-trigger-box').classList.remove('hidden');
      if (data.evaluation) {
        scorecardData = data.evaluation;
        setTimeout(() => renderScorecardModal(scorecardData), 1200);
      }
    }
  } catch (err) {
    showTypingIndicator(false);
    console.error('Error sending chat message:', err);
  }
}

function appendChatMessage(sender, text, phase) {
  const container = document.getElementById('chat-messages');
  
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-msg ${sender}`;

  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  
  const senderLabel = sender === 'agent' ? 'Agent 1 (HR Advisor)' : 'Candidate (Manager)';

  msgDiv.innerHTML = `
    <div class="msg-bubble">
      ${formatMarkdownText(text)}
      <div class="msg-meta">
        <span>${senderLabel}</span> • <span>${timeStr}</span>
      </div>
    </div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function formatMarkdownText(text) {
  // Simple markdown bolding and bullet formatting
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[SIMULATION_COMPLETE\]/g, '<span class="badge model-badge">✓ SIMULATION COMPLETE</span>');
  return formatted;
}

function updateKPIBars(kpis, deltas) {
  // Morale
  const moraleValEl = document.getElementById('morale-val');
  const moraleBarEl = document.getElementById('morale-bar');
  moraleValEl.innerText = `${Math.round(kpis.morale)}%`;
  moraleBarEl.style.width = `${kpis.morale}%`;

  // Productivity
  const prodValEl = document.getElementById('productivity-val');
  const prodBarEl = document.getElementById('productivity-bar');
  prodValEl.innerText = `${Math.round(kpis.productivity)}%`;
  prodBarEl.style.width = `${kpis.productivity}%`;

  // Burnout
  const burnoutValEl = document.getElementById('burnout-val');
  const burnoutBarEl = document.getElementById('burnout-bar');
  burnoutValEl.innerText = `${Math.round(kpis.burnout_risk)}%`;
  burnoutBarEl.style.width = `${kpis.burnout_risk}%`;

  // Display floating delta popups if non-zero
  if (deltas.morale !== 0 || deltas.productivity !== 0 || deltas.burnout_risk !== 0) {
    showDeltasNotification(deltas);
  }
}

function showDeltasNotification(deltas) {
  const container = document.getElementById('deltas-container');
  container.innerHTML = '';

  const createPill = (label, val, positiveGood = true) => {
    if (val === 0) return;
    const isGood = positiveGood ? val > 0 : val < 0;
    const sign = val > 0 ? '+' : '';
    const pill = document.createElement('div');
    pill.className = `pill ${isGood ? 'positive' : 'negative'}`;
    pill.style.cssText = `
      background: ${isGood ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'};
      color: ${isGood ? '#34D399' : '#F87171'};
      border: 1px solid ${isGood ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'};
      padding: 4px 10px;
      font-weight: 700;
      font-size: 0.75rem;
      border-radius: 12px;
      animation: fadeIn 0.4s ease-out;
    `;
    pill.innerText = `${label}: ${sign}${val}%`;
    container.appendChild(pill);
  };

  createPill('Morale', deltas.morale, true);
  createPill('Productivity', deltas.productivity, true);
  createPill('Burnout Risk', deltas.burnout_risk, false);

  setTimeout(() => { container.innerHTML = ''; }, 4000);
}

function updatePhaseStepper(phase) {
  for (let i = 1; i <= 3; i++) {
    const stepEl = document.getElementById(`step-${i}`);
    if (i <= phase) {
      stepEl.classList.add('active');
    } else {
      stepEl.classList.remove('active');
    }
  }

  const phaseSubtitles = {
    1: 'Phase 1: Conflict Mediation (Alex vs Morgan)',
    2: 'Phase 2: Crunch Time Dilemma (48h Launch)',
    3: 'Phase 3: Feedback Session (Jordan Review)'
  };
  document.getElementById('current-phase-subtitle').innerText = phaseSubtitles[phase] || `Phase ${phase}`;
}

function renderMemosList(memos) {
  const container = document.getElementById('memo-list');
  container.innerHTML = '';

  memos.forEach(m => {
    const card = document.createElement('div');
    card.className = `memo-card ${m.read ? '' : 'unread'}`;
    
    card.innerHTML = `
      <div class="memo-header-row">
        <span class="priority-tag ${m.priority.toLowerCase()}">${m.priority}</span>
        <span class="memo-time">${m.date}</span>
      </div>
      <div class="memo-title">${m.title}</div>
      <div class="memo-sender">From: ${m.sender}</div>
    `;

    card.addEventListener('click', () => openMemoModal(m));
    container.appendChild(card);
  });
}

function openMemoModal(memo) {
  memo.read = true;
  document.getElementById('modal-memo-priority').innerText = memo.priority;
  document.getElementById('modal-memo-priority').className = `priority-tag ${memo.priority.toLowerCase()}`;
  document.getElementById('modal-memo-subject').innerText = memo.subject;
  document.getElementById('modal-memo-sender').innerText = memo.sender;
  document.getElementById('modal-memo-date').innerText = memo.date;
  document.getElementById('modal-memo-phase').innerText = `Phase ${memo.phase}`;
  document.getElementById('modal-memo-content').innerText = memo.content;

  document.getElementById('memo-modal-backdrop').classList.remove('hidden');
  renderMemosList(activeMemos);
}

function closeMemoModal() {
  document.getElementById('memo-modal-backdrop').classList.add('hidden');
}

function renderScorecardModal(data) {
  const bodyEl = document.getElementById('scorecard-content');
  
  const ratingClass = (data.candidate_rating || 'Developing').toLowerCase().replace(/\s+/g, '-');

  bodyEl.innerHTML = `
    <div class="scorecard-banner">
      <div>
        <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">Leadership Rating</div>
        <div class="rating-badge ${ratingClass}">${data.candidate_rating}</div>
      </div>
      <div class="overall-score-circle">
        <span class="score-num">${data.overall_score}</span>
        <span class="score-caption">OVERALL SCORE / 100</span>
      </div>
    </div>

    <div class="scorecard-section-title">Rubric Category Analysis</div>
    <div class="metric-grid">
      <div class="metric-item">
        <div class="metric-item-header">
          <span>😊 Empathy & Active Listening</span>
          <span style="color: var(--primary-accent);">${data.metrics.empathy.score}%</span>
        </div>
        <p>${data.metrics.empathy.analysis}</p>
      </div>

      <div class="metric-item">
        <div class="metric-item-header">
          <span>📈 Decision-Making & Trade-offs</span>
          <span style="color: var(--primary-accent);">${data.metrics.decision_making.score}%</span>
        </div>
        <p>${data.metrics.decision_making.analysis}</p>
      </div>

      <div class="metric-item">
        <div class="metric-item-header">
          <span>💬 Communication & Tone</span>
          <span style="color: var(--primary-accent);">${data.metrics.communication.score}%</span>
        </div>
        <p>${data.metrics.communication.analysis}</p>
      </div>

      <div class="metric-item">
        <div class="metric-item-header">
          <span>🔥 Team Health & Crisis Control</span>
          <span style="color: var(--primary-accent);">${data.metrics.team_sustainability.score}%</span>
        </div>
        <p>${data.metrics.team_sustainability.analysis}</p>
      </div>
    </div>

    <div class="lists-row">
      <div class="card-list-box strengths">
        <h4>✓ Key Leadership Strengths</h4>
        <ul>
          ${(data.key_strengths || []).map(s => `<li>• ${s}</li>`).join('')}
        </ul>
      </div>

      <div class="card-list-box growth">
        <h4>▲ Growth Areas & Blind Spots</h4>
        <ul>
          ${(data.areas_for_growth || []).map(g => `<li>• ${s = g}</li>`).join('')}
        </ul>
      </div>
    </div>

    <div class="scorecard-section-title">Executive Evaluation Summary</div>
    <div class="exec-summary-box">
      ${data.executive_summary}
    </div>
  `;

  document.getElementById('scorecard-modal-backdrop').classList.remove('hidden');
}

function closeScorecardModal() {
  document.getElementById('scorecard-modal-backdrop').classList.add('hidden');
}

function showTypingIndicator(show) {
  const el = document.getElementById('typing-indicator');
  if (show) el.classList.remove('hidden');
  else el.classList.add('hidden');
}

function insertSuggestion(text) {
  const inputEl = document.getElementById('message-input');
  inputEl.value = text;
  inputEl.focus();
}

async function resetSimulation() {
  if (!sessionId) return;
  try {
    const res = await fetch(`${API_BASE}/reset/${sessionId}`, { method: 'POST' });
    const data = await res.json();

    sessionId = data.new_session_id;
    currentPhase = data.current_phase;
    currentKPIs = data.kpis;
    activeMemos = data.memos;
    isSimulationComplete = false;
    scorecardData = null;

    document.getElementById('session-id-display').innerText = `Session: ${sessionId.substring(0, 8)}...`;
    document.getElementById('eval-trigger-box').classList.add('hidden');

    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = '';
    appendChatMessage('agent', data.initial_message, 1);

    updateKPIBars(currentKPIs, { morale: 0, productivity: 0, burnout_risk: 0 });
    updatePhaseStepper(currentPhase);
    renderMemosList(activeMemos);
    closeScorecardModal();
  } catch (err) {
    console.error('Error resetting simulation:', err);
  }
}

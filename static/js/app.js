const API_BASE = window.location.origin;
let isListening = false;
let statusInterval = null;
let allKeywords = [];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch(`${API_BASE}/info`);
    const data = await response.json();
    allKeywords = data.keywords || [];
    renderKeywords([]);
  } catch (err) {
    console.error('Failed to load keywords:', err);
    allKeywords = ['yes', 'no', 'left', 'right', 'up', 'down', 'next', 'cancel', 'back', 'start', 'stop', 'exit'];
    renderKeywords([]);
  }
});

function renderKeywords(detected) {
  const grid = document.getElementById('keywordsGrid');
  grid.innerHTML = allKeywords.map(kw => `
    <span class="keyword-chip ${detected.includes(kw) ? 'detected' : 'available'}">${kw}</span>
  `).join('');
}

async function toggleListening() {
  if (isListening) {
    await stopListening();
  } else {
    await startListening();
  }
}

async function startListening() {
  try {
    const response = await fetch(`${API_BASE}/start`);
    const data = await response.json();
    
    if (data.status === 'listening' || data.status === 'already_listening') {
      isListening = true;
      updateUI(true);
      startPolling();
    }
  } catch (err) {
    console.error('Failed to start:', err);
    alert('Failed to start listening. Is the server running?');
  }
}

async function stopListening() {
  try {
    stopPolling();
    const response = await fetch(`${API_BASE}/stop`);
    const data = await response.json();
    
    isListening = false;
    updateUI(false);
    
    // Show final results
    if (data.keywords && data.keywords.length > 0) {
      renderKeywords(data.keywords);
    }
  } catch (err) {
    console.error('Failed to stop:', err);
  }
}

function updateUI(listening) {
  const btn = document.getElementById('mainBtn');
  const btnIcon = document.getElementById('btnIcon');
  const btnText = document.getElementById('btnText');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  if (listening) {
    btn.className = 'btn-main btn-stop';
    btnIcon.textContent = '⏹️';
    btnText.textContent = 'Stop Listening';
    statusDot.className = 'status-dot listening';
    statusText.textContent = 'Listening...';
  } else {
    btn.className = 'btn-main btn-start';
    btnIcon.textContent = '▶️';
    btnText.textContent = 'Start Listening';
    statusDot.className = 'status-dot';
    statusText.textContent = 'Ready to listen';
  }
}

function startPolling() {
  statusInterval = setInterval(pollStatus, 300);
}

function stopPolling() {
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }
}

async function pollStatus() {
  try {
    const response = await fetch(`${API_BASE}/status`);
    const data = await response.json();

    // Update listening state
    if (!data.listening && isListening) {
      isListening = false;
      updateUI(false);
      stopPolling();
    }

    // Update partial text
    const partialEl = document.getElementById('partialText');
    if (data.partial) {
      partialEl.textContent = `"${data.partial}..."`;
      partialEl.style.color = '';
    } else if (data.transcript && data.transcript.length > 0) {
      partialEl.textContent = `Last: "${data.transcript[data.transcript.length - 1]}"`;
    } else {
      partialEl.textContent = 'Listening for speech...';
    }

    // Update transcript list
    const transcriptList = document.getElementById('transcriptList');
    if (data.transcript && data.transcript.length > 0) {
      transcriptList.innerHTML = data.transcript.map(t => 
        `<div class="transcript-item">"${t}"</div>`
      ).join('');
      transcriptList.scrollTop = transcriptList.scrollHeight;
    }

    // Update speaker verification
    const similarity = data.speaker_similarity || 0;
    const percentage = Math.round(similarity * 100);
    document.getElementById('verificationFill').style.width = `${percentage}%`;
    document.getElementById('similarityValue').textContent = `${percentage}%`;
    
    const statusDot = document.getElementById('statusDot');
    const verificationStatus = document.getElementById('verificationStatus');
    
    if (data.is_verified) {
      verificationStatus.textContent = '✅ Verified';
      verificationStatus.style.color = 'var(--accent-success)';
      statusDot.classList.add('verified');
      statusDot.classList.remove('unverified');
    } else if (similarity > 0) {
      verificationStatus.textContent = '⚠️ Not verified';
      verificationStatus.style.color = 'var(--accent-warning)';
      statusDot.classList.add('unverified');
      statusDot.classList.remove('verified');
    } else {
      verificationStatus.textContent = 'Waiting...';
      verificationStatus.style.color = '';
    }

    // Update keywords
    if (data.keywords) {
      renderKeywords(data.keywords);
    }

    // Update last keyword
    const lastKeywordSection = document.getElementById('lastKeywordSection');
    const lastKeywordValue = document.getElementById('lastKeywordValue');
    if (data.last_keyword) {
      lastKeywordSection.style.display = 'block';
      lastKeywordValue.textContent = data.last_keyword.toUpperCase();
    }

  } catch (err) {
    console.error('Polling error:', err);
  }
}

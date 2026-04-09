// ── Backend URL ─────────────────────────────────────────────
// Uses the same origin — works both locally and on Render
const API_URL = window.location.origin;

// ── State ────────────────────────────────────────────────────
let sessions  = [];
let activeId  = null;
let isLoading = false;

// ── Helpers ──────────────────────────────────────────────────
function esc(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function makeSession() {
  return { id: Date.now().toString(), title: 'New Chat', messages: [] };
}

function getSession(id) {
  return sessions.find(s => s.id === id);
}

// ── Session management ────────────────────────────────────────
function createSession() {
  const s = makeSession();
  sessions.unshift(s);
  switchSession(s.id);
}

function switchSession(id) {
  activeId = id;
  renderSidebar();
  renderMessages();
  updateTopbar();
}

function updateSessionTitle(id) {
  const s = getSession(id);
  if (!s) return;
  const first = s.messages.find(m => m.role === 'user');
  if (first) s.title = first.text.slice(0, 45) + (first.text.length > 45 ? '…' : '');
}

// ── Sidebar ───────────────────────────────────────────────────
function renderSidebar() {
  const list = document.getElementById('sessions-list');
  list.innerHTML = sessions.map(s => `
    <button class="session-item ${s.id === activeId ? 'active' : ''}"
            onclick="switchSession('${s.id}')">
      <svg class="session-icon" width="14" height="14" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
      <span class="session-title">${esc(s.title)}</span>
    </button>
  `).join('');
}

function updateTopbar() {
  const s = getSession(activeId);
  document.getElementById('topbar-title').textContent = s ? s.title : 'New Chat';
}

// ── Message rendering ─────────────────────────────────────────
const BOT_AVATAR_SVG = `
  <svg width="16" height="16" viewBox="0 0 28 28" fill="none">
    <path d="M14 2L26 8V20L14 26L2 20V8L14 2Z" fill="#D97706"/>
    <path d="M14 7L21 11V17L14 21L7 17V11L14 7Z" fill="#FDE68A"/>
  </svg>`;

const WELCOME_HTML = `
  <div class="chat-welcome">
    <div class="welcome-icon">
      <svg width="40" height="40" viewBox="0 0 28 28" fill="none">
        <path d="M14 2L26 8V20L14 26L2 20V8L14 2Z" fill="#D97706" fill-opacity="0.9"/>
        <path d="M14 7L21 11V17L14 21L7 17V11L14 7Z" fill="#FDE68A"/>
      </svg>
    </div>
    <h2>How can I help you today?</h2>
    <p>Ask me anything about the knowledge base. I'll find the relevant steps and screenshots for you.</p>
    <div class="welcome-chips">
      <button class="chip" onclick="useChip('How do I configure WLAN?')">How do I configure WLAN?</button>
      <button class="chip" onclick="useChip('Walk me through the proxy process')">Walk me through the proxy process</button>
      <button class="chip" onclick="useChip('Show me the pivot process steps')">Show me the pivot process steps</button>
    </div>
  </div>`;

function parseResponse(text) {
  if (!text) return '';

  // 1. Extract all Image: <url> occurrences (anywhere in text) and replace with placeholders
  const images = [];
  const withPlaceholders = text.replace(/Image:\s*(https?:\/\/[^\s\n]+)/g, (_, url) => {
    const idx = images.length;
    images.push(url.trim());
    return `\n%%IMG_${idx}%%\n`;
  });

  // 2. Render markdown (handles **bold**, numbered lists, paragraphs, etc.)
  const html = typeof marked !== 'undefined'
    ? marked.parse(withPlaceholders)
    : withPlaceholders.split('\n').map(l => l.trim() ? `<p>${esc(l)}</p>` : '').join('');

  // 3. Replace placeholders back with <img> tags
  return html.replace(/%%IMG_(\d+)%%/g, (_, idx) => {
    const url = images[parseInt(idx)];
    return url
      ? `<img class="step-image" src="${API_URL}/image-proxy?url=${encodeURIComponent(url)}" alt="step screenshot"/>`
      : '';
  });
}

function msgHTML(msg) {
  if (msg.role === 'user') {
    return `
      <div class="msg msg-user">
        <div class="msg-bubble">${esc(msg.text)}</div>
        <div class="avatar user-avatar">You</div>
      </div>`;
  }
  return `
    <div class="msg msg-bot">
      <div class="avatar bot-avatar">${BOT_AVATAR_SVG}</div>
      <div class="msg-body">${parseResponse(msg.text)}</div>
    </div>`;
}

function renderMessages() {
  const container = document.getElementById('chat-messages');
  const s = getSession(activeId);
  if (!s || s.messages.length === 0) {
    container.innerHTML = WELCOME_HTML;
    return;
  }
  container.innerHTML = s.messages.map(msgHTML).join('');
  container.scrollTop = container.scrollHeight;
}

// ── Typing indicator ──────────────────────────────────────────
function showTyping() {
  const container = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.id = 'typing-indicator';
  el.className = 'msg msg-bot';
  el.innerHTML = `
    <div class="avatar bot-avatar">${BOT_AVATAR_SVG}</div>
    <div class="msg-body">
      <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

// ── Send message ──────────────────────────────────────────────
async function send() {
  if (isLoading) return;
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text) return;

  const s = getSession(activeId);
  if (!s) return;

  s.messages.push({ role: 'user', text });
  updateSessionTitle(activeId);
  input.value = '';
  input.style.height = 'auto';
  renderMessages();
  updateTopbar();
  renderSidebar();

  isLoading = true;
  updateSendBtn();
  showTyping();

  try {
    // Send last 10 messages as history (excluding the current message just added)
    const history = s.messages.slice(0, -1).slice(-10).map(m => ({
      role: m.role === 'user' ? 'user' : 'assistant',
      content: m.text,
    }));

    const res = await fetch(`${API_URL}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ query: text, history }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(`[${res.status}] ${err.detail || res.statusText}`);
    }
    const data = await res.json();
    s.messages.push({ role: 'bot', text: data.response });
  } catch (err) {
    s.messages.push({ role: 'bot', text: `⚠ Error: ${err.message}` });
    console.error('Chat error:', err);
  } finally {
    hideTyping();
    isLoading = false;
    updateSendBtn();
    renderMessages();
  }
}

// ── Chip shortcut ─────────────────────────────────────────────
function useChip(text) {
  const input = document.getElementById('chat-input');
  input.value = text;
  updateSendBtn();
  send();
}

// ── Send button state ─────────────────────────────────────────
function updateSendBtn() {
  const btn   = document.getElementById('send-btn');
  const input = document.getElementById('chat-input');
  const ready = !!input.value.trim() && !isLoading;
  btn.classList.toggle('active', ready);
  btn.disabled = !ready;
}

// ── Boot ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Create initial session
  const first = makeSession();
  sessions.push(first);
  activeId = first.id;
  renderSidebar();
  renderMessages();

  const input  = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 180) + 'px';
    updateSendBtn();
  });

  sendBtn.addEventListener('click', send);
  document.getElementById('new-chat-btn').addEventListener('click', createSession);
});

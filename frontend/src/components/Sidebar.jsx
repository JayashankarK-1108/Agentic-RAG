export default function Sidebar({ sessions, activeId, onSelect, onNew }) {
  return (
    <div className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <path d="M14 2L26 8V20L14 26L2 20V8L14 2Z" fill="#D97706" fillOpacity="0.9"/>
            <path d="M14 7L21 11V17L14 21L7 17V11L14 7Z" fill="#FDE68A"/>
          </svg>
        </div>
        <span className="brand-name">KB Assistant</span>
      </div>

      <button className="new-chat-btn" onClick={onNew}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        New Chat
      </button>

      <div className="sessions-section">
        <div className="sessions-label">Recent</div>
        <div className="sessions-list">
          {sessions.map(s => (
            <button
              key={s.id}
              className={`session-item ${s.id === activeId ? "active" : ""}`}
              onClick={() => onSelect(s.id)}
            >
              <svg className="session-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span className="session-title">{s.title}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

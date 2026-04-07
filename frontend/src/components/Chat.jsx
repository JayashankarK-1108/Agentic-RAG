import { useState, useRef, useEffect } from "react";
import { sendMessage } from "../services/api";
import Message from "./Message";

export default function Chat({ session, onUpdate }) {
  const [messages, setMessages] = useState(session.messages);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [text]);

  const send = async () => {
    if (!text.trim() || loading) return;
    const userMsg = { role: "user", text: text.trim() };
    const updated = [...messages, userMsg];
    setMessages(updated);
    onUpdate(updated);
    setText("");
    setLoading(true);

    try {
      const res = await sendMessage(userMsg.text);
      const done = [...updated, { role: "bot", text: res.response }];
      setMessages(done);
      onUpdate(done);
    } catch {
      const done = [...updated, { role: "bot", text: "Sorry, I couldn't get a response. Please try again." }];
      setMessages(done);
      onUpdate(done);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chat-pane">
      <div className="chat-topbar">
        <span className="topbar-title">{session.title}</span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && !loading && (
          <div className="chat-welcome">
            <div className="welcome-icon">
              <svg width="40" height="40" viewBox="0 0 28 28" fill="none">
                <path d="M14 2L26 8V20L14 26L2 20V8L14 2Z" fill="#D97706" fillOpacity="0.9"/>
                <path d="M14 7L21 11V17L14 21L7 17V11L14 7Z" fill="#FDE68A"/>
              </svg>
            </div>
            <h2>How can I help you today?</h2>
            <p>Ask me anything about the knowledge base. I'll find the relevant steps and screenshots for you.</p>
            <div className="welcome-chips">
              {["How do I configure WLAN?", "Walk me through the proxy process", "Show me the pivot process steps"].map(q => (
                <button key={q} className="chip" onClick={() => { setText(q); textareaRef.current?.focus(); }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && <Message msg={{ role: "bot", text: "" }} loading />}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="input-box">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Message KB Assistant…"
            rows={1}
          />
          <button
            className={`send-btn ${text.trim() && !loading ? "active" : ""}`}
            onClick={send}
            disabled={loading || !text.trim()}
            title="Send message"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="19" x2="12" y2="5"/>
              <polyline points="5 12 12 5 19 12"/>
            </svg>
          </button>
        </div>
        <p className="input-hint">Enter to send &nbsp;·&nbsp; Shift+Enter for new line</p>
      </div>
    </div>
  );
}

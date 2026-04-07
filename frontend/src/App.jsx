import { useState } from "react";
import Sidebar from "./components/Sidebar";
import Chat from "./components/Chat";

const makeSession = () => ({ id: Date.now().toString(), title: "New Chat", messages: [] });

export default function App() {
  const [sessions, setSessions] = useState([makeSession()]);
  const [activeId, setActiveId] = useState(sessions[0].id);

  const activeSession = sessions.find(s => s.id === activeId) || sessions[0];

  const createSession = () => {
    const s = makeSession();
    setSessions(prev => [s, ...prev]);
    setActiveId(s.id);
  };

  const updateSession = (id, messages) => {
    setSessions(prev => prev.map(s => {
      if (s.id !== id) return s;
      const title = messages.find(m => m.role === "user")?.text.slice(0, 42) || "New Chat";
      return { ...s, title, messages };
    }));
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={createSession}
      />
      <Chat
        key={activeId}
        session={activeSession}
        onUpdate={(msgs) => updateSession(activeId, msgs)}
      />
    </div>
  );
}

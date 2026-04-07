function BotAvatar() {
  return (
    <div className="avatar bot-avatar">
      <svg width="16" height="16" viewBox="0 0 28 28" fill="none">
        <path d="M14 2L26 8V20L14 26L2 20V8L14 2Z" fill="#D97706"/>
        <path d="M14 7L21 11V17L14 21L7 17V11L14 7Z" fill="#FDE68A"/>
      </svg>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="typing-dots">
      <span /><span /><span />
    </div>
  );
}

export default function Message({ msg, loading }) {
  if (msg.role === "user") {
    return (
      <div className="msg msg-user">
        <div className="msg-bubble">{msg.text}</div>
        <div className="avatar user-avatar">You</div>
      </div>
    );
  }

  return (
    <div className="msg msg-bot">
      <BotAvatar />
      <div className="msg-body">
        {loading ? <TypingDots /> : (
          msg.text?.split("\n").map((line, i) => {
            if (line.startsWith("Image:")) {
              const url = line.replace("Image:", "").trim();
              return url
                ? <img key={i} className="step-image" src={url} alt="step screenshot" />
                : null;
            }
            return line.trim()
              ? <p key={i}>{line}</p>
              : null;
          })
        )}
      </div>
    </div>
  );
}

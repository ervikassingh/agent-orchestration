import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

interface AgentInfo {
  name: string;
  description: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const API_BASE = "/api";

async function apiError(response: Response): Promise<Error> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return new Error(data.detail);
  } catch {
    // Fall back to the HTTP status when the response is not JSON.
  }
  return new Error(`API returned ${response.status}`);
}

export default function App() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${API_BASE}/agents`)
      .then((res) => {
        if (!res.ok) return apiError(res).then((error) => { throw error; });
        return res.json();
      })
      .then((data) => setAgents(data.agents ?? []))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || isSending) return;

    const userMessage: ChatMessage = { role: "user", content };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setDraft("");
    setError(null);
    setIsSending(true);

    try {
      const response = await fetch(`${API_BASE}/agents/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });
      if (!response.ok) throw await apiError(response);
      if (!response.body) throw new Error("The agent returned no stream.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let reply = "";

      const appendToken = (token: string) => {
        reply += token;
        setMessages([...nextMessages, { role: "assistant", content: reply }]);
      };

      while (true) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value, { stream: !done });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const event of events) {
          const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
          if (!dataLine) continue;

          const data = JSON.parse(dataLine.slice(6)) as { token?: string; error?: string };
          if (data.error) throw new Error(data.error);
          if (data.token) appendToken(data.token);
        }

        if (done) break;
      }

      if (!reply) {
        setMessages([...nextMessages, { role: "assistant", content: "The agent returned an empty response." }]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reach the agent");
    } finally {
      setIsSending(false);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  const activeAgent = agents[0];

  return (
    <main className="app">
      <header className="app-header">
        <div>
          <p className="eyebrow">Agent workspace</p>
          <h1>Talk to your agent.</h1>
          <p className="subtitle">Ask questions, explore ideas, and run tasks through the orchestration service.</p>
        </div>
        <div className={`status-chip ${isSending ? "thinking" : ""}`} aria-label={isSending ? "Agent is thinking" : "Agent is ready"}>
          <span className="status-bot" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          {activeAgent?.name ?? "Connecting"}
        </div>
      </header>

      <section className="chat-panel" aria-label="Agent conversation">
        <div className="conversation">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark">✦</div>
              <h2>Where should we begin?</h2>
              <p>Send a message to start a conversation with the orchestrator.</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <span className="message-label">{message.role === "user" ? "You" : "Agent"}</span>
                <p>{message.content}</p>
              </article>
            ))
          )}
          {isSending && (
            <article className="message assistant typing" aria-label="Agent is thinking">
              <span className="message-label">Agent</span>
              <p><span /> <span /> <span /></p>
            </article>
          )}
          <div ref={messagesEndRef} />
        </div>

        {error && <div className="error" role="alert">{error}</div>}

        <form className="composer" onSubmit={sendMessage}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleComposerKeyDown}
            placeholder="Ask the agent anything..."
            aria-label="Message the agent"
            rows={1}
            disabled={isSending}
          />
          <button type="submit" disabled={isSending || !draft.trim()} aria-label="Send message">
            Send
          </button>
        </form>
      </section>
    </main>
  );
}

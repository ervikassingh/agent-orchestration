import { useEffect, useState } from "react";

interface AgentInfo {
  name: string;
  description: string;
}

const API_BASE = "/api";

export default function App() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/agents`)
      .then((res) => {
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        return res.json();
      })
      .then((data) => setAgents(data.agents ?? []))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <main className="app">
      <header>
        <h1>Agent Orchestration</h1>
        <p className="subtitle">
          LangChain + LangGraph powered agent service
        </p>
      </header>

      {error && <div className="error">⚠ {error}</div>}

      <section>
        <h2>Registered Agents</h2>
        {agents.length === 0 ? (
          <p className="empty">No agents registered yet.</p>
        ) : (
          <ul className="agent-list">
            {agents.map((agent) => (
              <li key={agent.name}>
                <strong>{agent.name}</strong>
                {agent.description && <span> — {agent.description}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}

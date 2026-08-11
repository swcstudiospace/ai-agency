import { useEffect, useRef } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import type { ChatMessage, HitlRequest } from "../data/demo";
import { AGENTS, agentColor, TEAMS } from "../data/agents";
import type { AgentRuntime } from "../data/demo";
import { GenUIRenderer } from "./GenUI";

function fmt(ts: number) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

const HINTS = [
  "Rank desk mobility kits under $50",
  "Open returns RMA for order #1042",
  "Draft creative factory for Mobility Kit",
  "Show fraud holds last 24h",
  "Run experimentation cycle on PDP CVR",
];

export function ChatStage({
  messages,
  onHitl,
  draft,
  setDraft,
  onSend,
  typing,
}: {
  messages: ChatMessage[];
  onHitl: (id: string, d: "approved" | "rejected") => void;
  draft: string;
  setDraft: (v: string) => void;
  onSend: () => void;
  typing?: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  return (
    <main className="panel chat">
      <div className="panel-hd" style={{ paddingInline: 22 }}>
        <h2>Mission control</h2>
        <span className="muted" style={{ fontSize: 12, display: "inline-flex", alignItems: "center", gap: 6 }}>
          <Sparkles size={12} /> Generative UI · CopilotKit-ready
        </span>
      </div>
      <div className="chat-stream">
        {messages.map((m) => {
          const agent = m.agentId ? AGENTS.find((a) => a.id === m.agentId) : undefined;
          return (
            <article key={m.id} className={`msg ${m.role}`}>
              <div className="msg-bubble">
                {m.role !== "user" && m.role !== "system" ? (
                  <div className="msg-hd">
                    <span
                      className="avatar"
                      style={{ background: agent ? agentColor(agent.hue) : "var(--accent2)" }}
                    >
                      {(agent?.name ?? "SW").slice(0, 2).toUpperCase()}
                    </span>
                    <strong>{agent?.name ?? (m.role === "swarm" ? "Swarm bus" : "System")}</strong>
                    <span className="muted" style={{ fontSize: 11 }}>
                      {agent?.role ?? "coordination"}
                    </span>
                    <time>{fmt(m.ts)}</time>
                  </div>
                ) : null}
                <div>{m.content}</div>
                {m.genui?.length ? <GenUIRenderer blocks={m.genui} onHitl={onHitl} /> : null}
              </div>
            </article>
          );
        })}
        {typing ? (
          <article className="msg agent">
            <div className="msg-bubble">
              <div className="msg-hd">
                <span className="avatar" style={{ background: "var(--accent)" }}>HO</span>
                <strong>Hermes Ops</strong>
                <span className="muted" style={{ fontSize: 11 }}>orchestrating</span>
              </div>
              <span className="typing" aria-label="Agent typing"><i /><i /><i /></span>
            </div>
          </article>
        ) : null}
        <div ref={endRef} />
      </div>
      <div className="composer">
        <div className="composer-box">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Command the agency… product rank, RMA, creative factory, fraud holds, lifecycle…"
            rows={2}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
          <button type="button" className="btn primary" onClick={onSend} disabled={!draft.trim()}>
            <ArrowUp size={16} /> Dispatch
          </button>
        </div>
        <div className="composer-hints">
          {HINTS.map((h) => (
            <button type="button" className="hint" key={h} onClick={() => setDraft(h)}>
              {h}
            </button>
          ))}
        </div>
      </div>
    </main>
  );
}

export function RightRail({
  hitl,
  onHitl,
  feed,
  selected,
  runtime,
}: {
  hitl: HitlRequest[];
  onHitl: (id: string, d: "approved" | "rejected") => void;
  feed: { id: string; text: string; color: string }[];
  selected?: string;
  runtime: AgentRuntime[];
}) {
  const agent = selected ? AGENTS.find((a) => a.id === selected) : undefined;
  const rt = selected ? runtime.find((r) => r.agent.id === selected) : undefined;
  const pending = hitl.filter((h) => h.status === "pending");

  return (
    <aside className="panel rail">
      <div className="panel-hd">
        <h2>Inspector</h2>
        <span className="muted" style={{ fontFamily: "var(--mono)", fontSize: 11 }}>
          {pending.length} HITL
        </span>
      </div>
      <div className="panel-body">
        {agent && rt ? (
          <div className="inspector">
            <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
              <span className="avatar" style={{ background: agentColor(agent.hue), width: 32, height: 32, fontSize: 11 }}>
                {agent.name.slice(0, 2).toUpperCase()}
              </span>
              <div>
                <h3 style={{ margin: 0 }}>{agent.name}</h3>
                <p style={{ margin: 0 }}>{agent.role}</p>
              </div>
            </div>
            <p>
              Team · <strong style={{ color: TEAMS[agent.team].accent }}>{TEAMS[agent.team].name}</strong>
              {" · "}
              <span className={`badge ${rt.status === "awaiting_hitl" ? "pending" : rt.status === "done" ? "PASS" : "TEST"}`}>
                {rt.status}
              </span>
            </p>
            <p style={{ marginTop: 6 }}>{rt.lastAction} · load {Math.round(rt.load)}%</p>
            <div className="tool-pills">
              {agent.tools.map((t) => (
                <span className="chip" key={t}>{t}</span>
              ))}
            </div>
          </div>
        ) : (
          <p className="muted" style={{ padding: "4px 4px 10px" }}>Select an agent to inspect tools & status.</p>
        )}

        <div className="panel-hd" style={{ paddingInline: 0 }}>
          <h2>HITL queue</h2>
        </div>
        {hitl.length === 0 ? <p className="muted">No approvals waiting.</p> : null}
        {hitl.map((h) => (
          <div className={`hitl-item ${h.status}`} key={h.id}>
            <h3>{h.title}</h3>
            <p>{h.detail}</p>
            {h.amountUsd != null ? (
              <p style={{ marginTop: 6, fontFamily: "var(--mono)", color: "var(--text)" }}>
                ${h.amountUsd.toLocaleString()} · {h.kind}
              </p>
            ) : null}
            <div style={{ marginTop: 8 }}>
              <span className={`badge ${h.status}`}>{h.status}</span>
            </div>
            {h.status === "pending" ? (
              <div className="hitl-actions" style={{ marginTop: 10 }}>
                <button type="button" className="btn approve sm" onClick={() => onHitl(h.id, "approved")}>Approve</button>
                <button type="button" className="btn reject sm" onClick={() => onHitl(h.id, "rejected")}>Reject</button>
              </div>
            ) : null}
          </div>
        ))}

        <div className="section-gap" />
        <div className="panel-hd" style={{ paddingInline: 0 }}>
          <h2>Live feed</h2>
        </div>
        {feed.map((f) => (
          <div className="feed-item" key={f.id}>
            <span className="tick" style={{ background: f.color, color: f.color }} />
            <p>{f.text}</p>
          </div>
        ))}

        <div className="section-gap" />
        <div className="hitl-item">
          <h3>Stack path</h3>
          <p>
            Mock GenUI cockpit → next: CopilotKit runtime → AgentOS :7777 MCP · Drop :7788 · Bridge :7790 · HITL vault.
          </p>
        </div>
      </div>
    </aside>
  );
}

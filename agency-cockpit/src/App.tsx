import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Bot, Command, LayoutGrid, Radio, Shield, Sparkles, Workflow } from "lucide-react";
import { AgentRail } from "./components/AgentRail";
import { AgentConstellation } from "./components/AgentConstellation";
import { ChatStage, RightRail } from "./components/ChatStage";
import { PlatformBadge } from "./components/PlatformBadge";
import {
  buildDemoTranscript,
  seedRuntime,
  simulateUserPrompt,
  type AgentRuntime,
  type ChatMessage,
  type HitlRequest,
} from "./data/demo";
import { AGENTS, WORKFLOWS, agentColor } from "./data/agents";
import "./styles/app.css";

type ViewMode = "mission" | "swarm" | "hitl";
type Toast = { id: string; text: string; kind: "ok" | "bad" | "info" };

const COMMANDS = [
  { id: "lifecycle", label: "Launch full product lifecycle", run: "Run full product lifecycle for desk mobility" },
  { id: "rank", label: "Rank desk mobility products", run: "Rank desk mobility kits under $50" },
  { id: "rma", label: "Open returns RMA pipeline", run: "Open returns RMA for order #1042" },
  { id: "creative", label: "Creative factory for Mobility Kit", run: "Draft creative factory for Mobility Kit" },
  { id: "fraud", label: "Show fraud holds", run: "Show fraud holds last 24h" },
  { id: "exp", label: "Experimentation cycle", run: "Run experimentation cycle on PDP CVR" },
  { id: "replay", label: "Replay demo transcript", run: "__replay__" },
];

export default function App() {
  const [runtime, setRuntime] = useState<AgentRuntime[]>(() => seedRuntime());
  const [messages, setMessages] = useState<ChatMessage[]>(() => buildDemoTranscript());
  const [hitl, setHitl] = useState<HitlRequest[]>([
    {
      id: "hitl_demo_1",
      kind: "ad_spend",
      title: "Meta TEST · Mobility Kit",
      detail: "$150/day × 5 days · draft only until approved",
      amountUsd: 750,
      agentId: "growth_media_buyer",
      status: "pending",
    },
    {
      id: "hitl_demo_2",
      kind: "refund",
      title: "Refund above policy",
      detail: "CX Escalations · influencer delay goodwill $60",
      amountUsd: 60,
      agentId: "cx_escalations",
      status: "pending",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [selected, setSelected] = useState<string | undefined>("hermes_ops");
  const [mode, setMode] = useState<ViewMode>("mission");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteQ, setPaletteQ] = useState("");
  const [typing, setTyping] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [feed, setFeed] = useState(() =>
    AGENTS.slice(0, 8).map((a, i) => ({
      id: `f${i}`,
      text: `${a.name} registered toolbelt · ready`,
      color: agentColor(a.hue),
    })),
  );

  const toast = useCallback((text: string, kind: Toast["kind"] = "info") => {
    const id = `${Date.now()}_${Math.random()}`;
    setToasts((t) => [...t, { id, text, kind }]);
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200);
  }, []);

  // ambient swarm
  useEffect(() => {
    const t = window.setInterval(() => {
      setRuntime((prev) => {
        const next = prev.map((r) => ({ ...r }));
        const i = Math.floor(Math.random() * next.length);
        const statuses: AgentRuntime["status"][] = ["idle", "thinking", "tooling", "done"];
        const st = statuses[Math.floor(Math.random() * statuses.length)];
        if (next[i].status === "awaiting_hitl") return prev;
        next[i] = {
          ...next[i],
          status: st,
          load: Math.min(100, Math.max(0, next[i].load + (Math.random() * 20 - 8))),
          lastAction:
            st === "tooling" ? "Calling tools…" :
            st === "thinking" ? "Reasoning…" :
            st === "done" ? "Handed off" : "Standing by",
        };
        return next;
      });
      const a = AGENTS[Math.floor(Math.random() * AGENTS.length)];
      setFeed((f) =>
        [{
          id: `${Date.now()}`,
          text: `${a.name} · ${["KIP recall", "Linear dual-write", "Parallel search", "Shopify read", "QA checklist", "GenUI card"][Math.floor(Math.random() * 6)]}`,
          color: agentColor(a.hue),
        }, ...f].slice(0, 16),
      );
    }, 2600);
    return () => window.clearInterval(t);
  }, []);

  // ⌘K / Ctrl+K
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((o) => !o);
        setPaletteQ("");
      }
      if (e.key === "Escape") setPaletteOpen(false);
      if ((e.metaKey || e.ctrlKey) && e.key === "1") setMode("mission");
      if ((e.metaKey || e.ctrlKey) && e.key === "2") setMode("swarm");
      if ((e.metaKey || e.ctrlKey) && e.key === "3") setMode("hitl");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // mark growth buyer awaiting hitl while pending spend exists
  useEffect(() => {
    const pendingSpend = hitl.some((h) => h.status === "pending" && h.kind === "ad_spend");
    setRuntime((prev) =>
      prev.map((r) =>
        r.agent.id === "growth_media_buyer" && pendingSpend
          ? { ...r, status: "awaiting_hitl", lastAction: "Awaiting spend HITL" }
          : r,
      ),
    );
  }, [hitl]);

  const pendingHitl = useMemo(() => hitl.filter((h) => h.status === "pending").length, [hitl]);
  const liveCount = useMemo(() => runtime.filter((r) => r.status !== "idle").length, [runtime]);

  const applyHitl = useCallback((id: string, decision: "approved" | "rejected") => {
    setHitl((prev) => prev.map((h) => (h.id === id ? { ...h, status: decision } : h)));
    setMessages((prev) =>
      prev.map((m) => {
        if (!m.genui) return m;
        return {
          ...m,
          genui: m.genui.map((g) => {
            if (g.kind !== "hitl_spend") return g;
            if ((g.data as { hitlId?: string }).hitlId !== id) return g;
            return { ...g, data: { ...g.data, status: decision } };
          }),
        };
      }),
    );
    setMessages((prev) => [
      ...prev,
      {
        id: `hitl_res_${id}_${Date.now()}`,
        role: "system",
        content: `HITL ${decision.toUpperCase()} · ${id} · Finance vault notified (mock)`,
        ts: Date.now(),
      },
    ]);
    setRuntime((prev) =>
      prev.map((r) =>
        r.agent.id === "growth_media_buyer" || r.agent.id === "finance_controller"
          ? { ...r, status: decision === "approved" ? "tooling" : "idle", lastAction: `HITL ${decision}` }
          : r,
      ),
    );
    toast(decision === "approved" ? "HITL approved — agents unblocked" : "HITL rejected — draft discarded", decision === "approved" ? "ok" : "bad");
  }, [toast]);

  const onSend = () => {
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    setTyping(true);
    const sim = simulateUserPrompt(text);
    // staggered feel
    setMessages((m) => [...m, sim.messages[0]]);
    window.setTimeout(() => {
      setMessages((m) => [...m, ...sim.messages.slice(1)]);
      if (sim.hitl) setHitl((h) => [sim.hitl!, ...h]);
      setRuntime((prev) =>
        prev.map((r) =>
          sim.touch.includes(r.agent.id)
            ? { ...r, status: "thinking", lastAction: "Activated by dispatch", load: Math.min(100, r.load + 25) }
            : r.agent.id === "hermes_ops"
              ? { ...r, status: "tooling", lastAction: "Orchestrating swarm" }
              : r,
        ),
      );
      setTyping(false);
      toast("Swarm dispatched", "ok");
    }, 700);
  };

  const runCommand = (cmd: string) => {
    setPaletteOpen(false);
    if (cmd === "__replay__") {
      setMessages(buildDemoTranscript());
      setRuntime(seedRuntime());
      toast("Demo transcript replayed", "info");
      return;
    }
    setDraft(cmd);
    setMode("mission");
    // auto-send shortly so palette feels instant
    window.setTimeout(() => {
      const sim = simulateUserPrompt(cmd);
      setMessages((m) => [...m, ...sim.messages]);
      if (sim.hitl) setHitl((h) => [sim.hitl!, ...h]);
      setDraft("");
      toast("Command dispatched", "ok");
    }, 80);
  };

  const paletteItems = COMMANDS.filter((c) =>
    !paletteQ || c.label.toLowerCase().includes(paletteQ.toLowerCase()),
  );

  const wfProgress = [
    { name: "Full Product Lifecycle", pct: 62 },
    { name: "Creative Production Ops", pct: 40 },
    { name: "Returns RMA Pipeline", pct: 18 },
  ];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark" />
          <div>
            <h1>Agency Cockpit</h1>
            <span>Hermes × Agno · GenUI</span>
          </div>
        </div>

        <div className="view-tabs" role="tablist">
          {(
            [
              ["mission", "Mission", LayoutGrid],
              ["swarm", "Swarm", Activity],
              ["hitl", "HITL", Shield],
            ] as const
          ).map(([id, label, Icon]) => (
            <button
              key={id}
              type="button"
              role="tab"
              className={mode === id ? "on" : ""}
              onClick={() => setMode(id)}
            >
              <Icon size={12} style={{ marginRight: 4, verticalAlign: -1 }} />
              {label}
            </button>
          ))}
        </div>

        <div className="pill-row">
          <span className="pill"><span className="dot" /><strong>{liveCount}</strong> live / 30</span>
          <span className="pill"><strong>12</strong> teams</span>
          <span className="pill"><Workflow size={11} /><strong>10</strong> wf</span>
          <span className="pill"><Bot size={11} /> :7777</span>
          <span className="pill"><Radio size={11} /> :7790</span>
          <PlatformBadge />
          <span className="pill">
            <span className={pendingHitl ? "dot warn" : "dot"} />
            <Shield size={11} /> HITL {pendingHitl}
          </span>
        </div>

        <div className="top-actions">
          <button type="button" className="btn sm" onClick={() => setPaletteOpen(true)} title="Command palette">
            <Command size={13} /> <span className="kbd">⌘K</span>
          </button>
          <button
            type="button"
            className="btn sm"
            onClick={() => {
              setMessages(buildDemoTranscript());
              setRuntime(seedRuntime());
              toast("Demo replayed", "info");
            }}
          >
            <Activity size={13} /> Replay
          </button>
          <button
            type="button"
            className="btn primary sm"
            onClick={() => runCommand("Run full product lifecycle for desk mobility")}
          >
            <Sparkles size={13} /> Lifecycle
          </button>
        </div>
      </header>

      <div className="wf-strip" aria-label="Workflow progress">
        {wfProgress.map((w) => (
          <span className="wf-chip active" key={w.name}>
            {w.name}
            <span className="mini-bar"><i style={{ width: `${w.pct}%` }} /></span>
            <strong style={{ color: "var(--text)" }}>{w.pct}%</strong>
          </span>
        ))}
        {WORKFLOWS.slice(5, 8).map((w) => (
          <span className="wf-chip" key={w.id}>{w.name}</span>
        ))}
      </div>

      <div className={`shell mode-${mode}`}>
        {mode !== "hitl" ? (
          <AgentRail runtime={runtime} selected={selected} onSelect={setSelected} />
        ) : null}

        {mode === "swarm" ? (
          <div className="swarm-stage">
            <AgentConstellation runtime={runtime} large onSelect={setSelected} />
          </div>
        ) : (
          <ChatStage
            messages={messages}
            onHitl={applyHitl}
            draft={draft}
            setDraft={setDraft}
            onSend={onSend}
            typing={typing}
          />
        )}

        {mode !== "swarm" ? (
          <RightRail
            hitl={hitl}
            onHitl={applyHitl}
            feed={feed}
            selected={selected}
            runtime={runtime}
          />
        ) : null}
      </div>

      {paletteOpen ? (
        <div className="overlay" onClick={() => setPaletteOpen(false)}>
          <div className="palette" onClick={(e) => e.stopPropagation()}>
            <input
              autoFocus
              placeholder="Type a command or mission…"
              value={paletteQ}
              onChange={(e) => setPaletteQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && paletteItems[0]) runCommand(paletteItems[0].run);
              }}
            />
            <div className="palette-list">
              {paletteItems.map((c, i) => (
                <button
                  type="button"
                  key={c.id}
                  className={`palette-item${i === 0 ? " active" : ""}`}
                  onClick={() => runCommand(c.run)}
                >
                  <Sparkles size={14} color="var(--accent)" />
                  {c.label}
                  <small>↵</small>
                </button>
              ))}
              {!paletteItems.length ? (
                <p className="muted" style={{ padding: 16 }}>No matches — try “rank” or “lifecycle”.</p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}

      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind === "info" ? "" : t.kind}`}>{t.text}</div>
        ))}
      </div>
    </div>
  );
}

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { TEAMS, type TeamId } from "../data/agents";
import type { AgentRuntime } from "../data/demo";
import { AgentConstellation } from "./AgentConstellation";

const TEAM_ORDER: TeamId[] = [
  "director", "research", "supply", "creative", "store", "growth",
  "growth_ops", "retention", "cx_ops", "logistics_ops", "risk_finance", "merch",
];

type Filter = "all" | "live" | "hitl";

export function AgentRail({
  runtime,
  selected,
  onSelect,
}: {
  runtime: AgentRuntime[];
  selected?: string;
  onSelect: (id: string) => void;
}) {
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = useMemo(() => {
    const qq = q.trim().toLowerCase();
    return runtime.filter((rt) => {
      if (filter === "live" && rt.status === "idle") return false;
      if (filter === "hitl" && rt.status !== "awaiting_hitl") return false;
      if (!qq) return true;
      return (
        rt.agent.name.toLowerCase().includes(qq) ||
        rt.agent.role.toLowerCase().includes(qq) ||
        rt.agent.team.includes(qq)
      );
    });
  }, [runtime, q, filter]);

  const live = runtime.filter((r) => r.status !== "idle").length;

  return (
    <aside className="panel agents">
      <div className="panel-hd">
        <h2>Swarm · 30</h2>
        <span className="muted" style={{ fontFamily: "var(--mono)", fontSize: 11 }}>{live} live</span>
      </div>
      <AgentConstellation runtime={runtime} onSelect={onSelect} />
      <div className="search-box">
        <Search size={14} color="var(--dim)" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter agents…"
          aria-label="Filter agents"
        />
      </div>
      <div className="filter-row">
        {([
          ["all", "All"],
          ["live", "Live"],
          ["hitl", "HITL"],
        ] as const).map(([k, label]) => (
          <button
            key={k}
            type="button"
            className={`filter-chip${filter === k ? " on" : ""}`}
            onClick={() => setFilter(k)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="panel-body">
        {TEAM_ORDER.map((tid) => {
          const members = filtered.filter((r) => r.agent.team === tid);
          if (!members.length) return null;
          const meta = TEAMS[tid];
          return (
            <div className="team-group" key={tid}>
              <div className="team-label">
                <span className="team-swatch" style={{ background: meta.accent, color: meta.accent }} />
                {meta.name}
                <span style={{ marginLeft: "auto" }}>{members.length}</span>
              </div>
              {members.map((rt) => (
                <button
                  type="button"
                  key={rt.agent.id}
                  className={`agent-row${selected === rt.agent.id ? " active" : ""}`}
                  onClick={() => onSelect(rt.agent.id)}
                >
                  <span className={`pulse ${rt.status}`} />
                  <span className="agent-meta">
                    <strong>{rt.agent.name}</strong>
                    <small>{rt.status === "idle" ? rt.agent.role : rt.lastAction}</small>
                  </span>
                  <span className="agent-load">{Math.round(rt.load)}%</span>
                </button>
              ))}
            </div>
          );
        })}
        {!filtered.length ? (
          <p className="muted" style={{ padding: 12, textAlign: "center" }}>No agents match.</p>
        ) : null}
      </div>
    </aside>
  );
}

import clsx from "clsx";
import type { GenUIBlock } from "../data/demo";
import { AGENTS, agentColor } from "../data/agents";

function agentById(id?: string) {
  return AGENTS.find((a) => a.id === id);
}

export function GenUIRenderer({
  blocks,
  onHitl,
}: {
  blocks: GenUIBlock[];
  onHitl?: (id: string, decision: "approved" | "rejected") => void;
}) {
  return (
    <div className="genui-stack">
      {blocks.map((b, i) => (
        <div className="gcard" key={`${b.kind}-${i}`}>
          {b.title ? (
            <div className="gcard-hd">
              {b.title}
              <span className="tag">GenUI</span>
            </div>
          ) : null}
          <div className="gcard-bd">{renderBlock(b, onHitl)}</div>
        </div>
      ))}
    </div>
  );
}

function renderBlock(
  b: GenUIBlock,
  onHitl?: (id: string, decision: "approved" | "rejected") => void,
) {
  switch (b.kind) {
    case "kpi_strip": {
      const d = b.data as { agents: number; teams: number; workflows: number; hitlOpen: number };
      return (
        <div className="kpi-row">
          <div className="kpi"><b>{d.agents}</b><span>Agents</span></div>
          <div className="kpi"><b>{d.teams}</b><span>Teams</span></div>
          <div className="kpi"><b>{d.workflows}</b><span>Workflows</span></div>
          <div className="kpi"><b>{d.hitlOpen}</b><span>HITL open</span></div>
        </div>
      );
    }
    case "product_rank": {
      const d = b.data as {
        niche: string;
        winners: { name: string; score: number; price: number; cm: number; decision: string }[];
      };
      return (
        <>
          <p className="muted" style={{ marginTop: 0, marginBottom: 10 }}>
            Niche · <span style={{ color: "var(--text)", fontWeight: 600 }}>{d.niche}</span>
          </p>
          <table className="product-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Score</th>
                <th>Price</th>
                <th>CM%</th>
                <th>Gate</th>
              </tr>
            </thead>
            <tbody>
              {d.winners.map((w) => (
                <tr key={w.name}>
                  <td style={{ fontWeight: 600 }}>{w.name}</td>
                  <td>
                    <div className="score-cell">
                      {w.score}
                      <span className="score-bar"><i style={{ width: `${Math.min(100, w.score)}%` }} /></span>
                    </div>
                  </td>
                  <td style={{ fontFamily: "var(--mono)" }}>${w.price}</td>
                  <td style={{ fontFamily: "var(--mono)", color: w.cm >= 20 ? "var(--good)" : "var(--warn)" }}>
                    {w.cm}%
                  </td>
                  <td><span className={clsx("badge", w.decision)}>{w.decision}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      );
    }
    case "hitl_spend": {
      const d = b.data as {
        hitlId: string;
        channel: string;
        dailyUsd: number;
        durationDays: number;
        objective: string;
        status: string;
      };
      const total = d.dailyUsd * d.durationDays;
      return (
        <div className="hitl-card">
          <div>
            <div className="muted" style={{ fontSize: 12 }}>
              {d.channel} · {d.durationDays}d · {d.objective}
            </div>
            <div className="amount">${total.toLocaleString()}</div>
            <div className="muted" style={{ fontSize: 12 }}>
              ${d.dailyUsd}/day draft · <span className={clsx("badge", d.status)}>{d.status}</span>
            </div>
          </div>
          {d.status === "pending" ? (
            <div className="hitl-actions">
              <button type="button" className="btn approve" onClick={() => onHitl?.(d.hitlId, "approved")}>
                Approve HITL
              </button>
              <button type="button" className="btn reject" onClick={() => onHitl?.(d.hitlId, "rejected")}>
                Reject
              </button>
            </div>
          ) : null}
        </div>
      );
    }
    case "qa_gate": {
      const d = b.data as { sku: string; verdict: string; defects: string[]; shipHold: boolean };
      return (
        <div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10, flexWrap: "wrap" }}>
            <strong>{d.sku}</strong>
            <span className={clsx("badge", d.verdict)}>{d.verdict}</span>
            {d.shipHold ? <span className="badge FAIL">SHIP HOLD</span> : null}
          </div>
          <div className="chips">
            {d.defects.map((x) => (
              <span className="chip" key={x}>{x}</span>
            ))}
          </div>
        </div>
      );
    }
    case "swarm_status": {
      const d = b.data as { active: string[]; workflow: string };
      return (
        <div>
          <p className="muted" style={{ marginTop: 0 }}>Workflow · <strong style={{ color: "var(--text)" }}>{d.workflow}</strong></p>
          <div className="chips">
            {d.active.map((id) => {
              const a = agentById(id);
              return (
                <span className="chip" key={id} style={{ borderColor: a ? agentColor(a.hue, 0.5) : undefined, color: a ? agentColor(a.hue) : undefined }}>
                  {a?.name ?? id}
                </span>
              );
            })}
          </div>
        </div>
      );
    }
    case "workflow_progress": {
      const d = b.data as { items: { name: string; pct: number }[] };
      return (
        <div className="progress-list">
          {d.items.map((it) => (
            <div className="progress-row" key={it.name}>
              <label>
                <span>{it.name}</span>
                <span style={{ fontFamily: "var(--mono)" }}>{it.pct}%</span>
              </label>
              <div className="bar"><i style={{ width: `${it.pct}%` }} /></div>
            </div>
          ))}
        </div>
      );
    }
    case "linear_issue": {
      const d = b.data as { key: string; title: string; state: string };
      return (
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span className="chip" style={{ color: "var(--accent2)", borderColor: "rgba(34,211,238,0.35)" }}>{d.key}</span>
          <span style={{ fontWeight: 600 }}>{d.title}</span>
          <span className="badge TEST" style={{ marginLeft: "auto" }}>{d.state}</span>
        </div>
      );
    }
    case "experiment": {
      const d = b.data as { hypothesis: string; metric: string; days: number; ice: number };
      return (
        <div>
          <p style={{ marginTop: 0, fontWeight: 500 }}>{d.hypothesis}</p>
          <div className="chips">
            <span className="chip">metric:{d.metric}</span>
            <span className="chip">{d.days}d</span>
            <span className="chip" style={{ color: "var(--good)" }}>ICE {d.ice}</span>
          </div>
        </div>
      );
    }
    case "fraud_hold": {
      const d = b.data as { orderId: string; score: number; action: string };
      return (
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span className="chip">{d.orderId}</span>
          <div className="score-cell">risk {d.score}<span className="score-bar"><i style={{ width: `${d.score}%`, background: "linear-gradient(90deg,var(--warn),var(--bad))" }} /></span></div>
          <span className="badge CONDITIONAL">{d.action}</span>
        </div>
      );
    }
    default:
      return <pre style={{ margin: 0, fontSize: 11 }}>{JSON.stringify(b.data, null, 2)}</pre>;
  }
}

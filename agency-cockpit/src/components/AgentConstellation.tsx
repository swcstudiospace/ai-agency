import { useMemo } from "react";
import type { AgentRuntime } from "../data/demo";
import { agentColor } from "../data/agents";

/** Radial constellation of all agents — active ones glow + link to Hermes. */
export function AgentConstellation({
  runtime,
  large = false,
  onSelect,
}: {
  runtime: AgentRuntime[];
  large?: boolean;
  onSelect?: (id: string) => void;
}) {
  const layout = useMemo(() => {
    const cx = large ? 400 : 200;
    const cy = large ? 260 : 105;
    const rOuter = large ? 200 : 88;
    const rInner = large ? 120 : 52;
    return runtime.map((rt, i) => {
      const ring = i % 2 === 0 ? rOuter : rInner;
      const angle = (i / runtime.length) * Math.PI * 2 - Math.PI / 2;
      return {
        ...rt,
        x: cx + Math.cos(angle) * ring,
        y: cy + Math.sin(angle) * ring,
      };
    });
  }, [runtime, large]);

  const hermes = layout.find((n) => n.agent.id === "hermes_ops");
  const active = layout.filter((n) => n.status !== "idle");
  const vb = large ? "0 0 800 520" : "0 0 400 210";

  return (
    <div className="constellation-wrap" aria-label="Agent constellation">
      <div className="constellation-legend">
        <span>{active.length} active</span>
        <span>{runtime.length} total</span>
      </div>
      <svg viewBox={vb}>
        <defs>
          <radialGradient id="glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(139,92,246,0.4)" />
            <stop offset="100%" stopColor="rgba(139,92,246,0)" />
          </radialGradient>
          <filter id="soft">
            <feGaussianBlur stdDeviation="1.2" />
          </filter>
        </defs>
        <circle cx={large ? 400 : 200} cy={large ? 260 : 105} r={large ? 140 : 70} fill="url(#glow)" />
        {hermes
          ? active.map((n) => (
              <line
                key={`l-${n.agent.id}`}
                x1={hermes.x}
                y1={hermes.y}
                x2={n.x}
                y2={n.y}
                stroke={agentColor(n.agent.hue, 0.4)}
                strokeWidth={n.status === "tooling" ? 1.6 : 1}
                strokeLinecap="round"
              />
            ))
          : null}
        {layout.map((n) => {
          const busy = n.status !== "idle";
          const r = n.agent.id === "hermes_ops" ? (large ? 10 : 7) : busy ? (large ? 7 : 5) : large ? 4.5 : 3.2;
          return (
            <g
              key={n.agent.id}
              style={{ cursor: onSelect ? "pointer" : "default" }}
              onClick={() => onSelect?.(n.agent.id)}
            >
              {busy ? (
                <circle cx={n.x} cy={n.y} r={r + 4} fill={agentColor(n.agent.hue, 0.15)} filter="url(#soft)" />
              ) : null}
              <circle
                cx={n.x}
                cy={n.y}
                r={r}
                fill={agentColor(n.agent.hue, busy ? 0.95 : 0.4)}
                stroke={busy ? "rgba(255,255,255,0.55)" : "transparent"}
                strokeWidth={1.2}
              >
                <title>{n.agent.name} · {n.status}</title>
              </circle>
              {large ? (
                <text
                  x={n.x}
                  y={n.y + r + 12}
                  textAnchor="middle"
                  fill="rgba(255,255,255,0.45)"
                  fontSize="9"
                  fontFamily="IBM Plex Mono, monospace"
                >
                  {n.agent.name.split(" ")[0]}
                </text>
              ) : null}
            </g>
          );
        })}
        <text
          x={large ? 400 : 200}
          y={large ? 264 : 109}
          textAnchor="middle"
          fill="rgba(255,255,255,0.6)"
          fontSize={large ? 12 : 9}
          fontFamily="IBM Plex Mono, monospace"
          fontWeight="600"
        >
          HERMES
        </text>
      </svg>
      <div className="constellation-caption">{runtime.length} agents · {active.length} live edges · click node to inspect</div>
    </div>
  );
}

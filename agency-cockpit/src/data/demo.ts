import type { AgentDef } from "./agents";
import { AGENTS } from "./agents";

export type GenUIKind =
  | "text"
  | "product_rank"
  | "hitl_spend"
  | "linear_issue"
  | "qa_gate"
  | "swarm_status"
  | "workflow_progress"
  | "kpi_strip"
  | "fraud_hold"
  | "experiment";

export interface ChatMessage {
  id: string;
  role: "user" | "system" | "agent" | "swarm";
  agentId?: string;
  content: string;
  ts: number;
  genui?: GenUIBlock[];
}

export interface GenUIBlock {
  kind: GenUIKind;
  title?: string;
  data: Record<string, unknown>;
}

export interface AgentRuntime {
  agent: AgentDef;
  status: "idle" | "thinking" | "tooling" | "awaiting_hitl" | "done" | "error";
  lastAction: string;
  load: number; // 0-100
}

export interface HitlRequest {
  id: string;
  kind: "ad_spend" | "refund" | "publish" | "po";
  title: string;
  detail: string;
  amountUsd?: number;
  agentId: string;
  status: "pending" | "approved" | "rejected";
}

const pick = <T,>(arr: T[], n: number) => {
  const copy = [...arr];
  const out: T[] = [];
  while (out.length < n && copy.length) {
    const i = Math.floor(Math.random() * copy.length);
    out.push(copy.splice(i, 1)[0]);
  }
  return out;
};

export function seedRuntime(): AgentRuntime[] {
  return AGENTS.map((agent, i) => ({
    agent,
    status: i % 7 === 0 ? "thinking" : i % 11 === 0 ? "tooling" : "idle",
    lastAction: i % 7 === 0 ? "Planning next step…" : "Standing by",
    load: Math.floor(Math.random() * 40),
  }));
}

export function buildDemoTranscript(): ChatMessage[] {
  const now = Date.now();
  return [
    {
      id: "m0",
      role: "system",
      content: "Agency Cockpit connected · AgentOS :7777 · Drop :7788 · Bridge :7790 · Anda Nexus :8091",
      ts: now - 120000,
      genui: [{ kind: "kpi_strip", data: { agents: 30, teams: 12, workflows: 10, hitlOpen: 2 } }],
    },
    {
      id: "m1",
      role: "user",
      content: "Run product rank for desk mobility kits under $50. Prefer high CM, low return risk. Draft Meta test only — no live spend.",
      ts: now - 110000,
    },
    {
      id: "m2",
      role: "agent",
      agentId: "hermes_ops",
      content: "Routing Research → Supply → Creative. Holding Growth at L2 (draft only). Opening Linear dual-write for the test track.",
      ts: now - 105000,
      genui: [
        {
          kind: "swarm_status",
          title: "Swarm activation",
          data: {
            active: ["product_scout", "supplier_sourcer", "pricing_strategist", "compliance_officer"],
            workflow: "full_product_lifecycle",
          },
        },
      ],
    },
    {
      id: "m3",
      role: "agent",
      agentId: "product_scout",
      content: "Parallel advanced search + unit economics complete. Top candidate clears TEST gate.",
      ts: now - 90000,
      genui: [
        {
          kind: "product_rank",
          title: "Product rank · Desk mobility",
          data: {
            niche: "desk mobility",
            winners: [
              { name: "Desk Reset Mobility Kit", score: 75.7, price: 49.99, cm: 23.5, decision: "TEST" },
              { name: "Under-Desk Pedal Mini", score: 68.2, price: 39.0, cm: 21.1, decision: "TEST" },
              { name: "Laptop Lift Stand Pro", score: 54.0, price: 44.0, cm: 14.2, decision: "NO-GO" },
            ],
          },
        },
      ],
    },
    {
      id: "m4",
      role: "agent",
      agentId: "qa_inspector",
      content: "Sample zipper snag on Mobility Kit — CONDITIONAL gate. Holding bulk PO until CAPA.",
      ts: now - 70000,
      genui: [
        {
          kind: "qa_gate",
          title: "QA gate",
          data: { sku: "Desk Reset Mobility Kit", verdict: "CONDITIONAL", defects: ["ZIPPER_FAIL"], shipHold: true },
        },
      ],
    },
    {
      id: "m5",
      role: "agent",
      agentId: "growth_media_buyer",
      content: "Meta draft campaign ready for $150/day TEST. Requires HITL before any live spend.",
      ts: now - 50000,
      genui: [
        {
          kind: "hitl_spend",
          title: "HITL · Ad spend",
          data: {
            hitlId: "hitl_demo_1",
            channel: "Meta",
            dailyUsd: 150,
            durationDays: 5,
            objective: "Purchase · Desk Reset Mobility Kit",
            status: "pending",
          },
        },
      ],
    },
    {
      id: "m6",
      role: "agent",
      agentId: "experimentation_lead",
      content: "CRO backlog ranked. Primary: social-proof block on PDP.",
      ts: now - 30000,
      genui: [
        {
          kind: "experiment",
          title: "Experiment design",
          data: {
            hypothesis: "Social proof above fold lifts CVR ≥15% relative",
            metric: "cvr",
            days: 14,
            ice: 7.0,
          },
        },
      ],
    },
    {
      id: "m7",
      role: "swarm",
      content: "12 teams online · 4 agents tooling · 2 HITL pending · KIP dual-write healthy",
      ts: now - 10000,
      genui: [
        {
          kind: "workflow_progress",
          title: "Active workflows",
          data: {
            items: [
              { name: "Full Product Lifecycle", pct: 62 },
              { name: "Creative Production Ops", pct: 40 },
              { name: "Returns RMA Pipeline", pct: 18 },
            ],
          },
        },
        {
          kind: "linear_issue",
          title: "Linear dual-write",
          data: { key: "SPE-42", title: "TEST: Desk Reset Mobility Kit", state: "started" },
        },
      ],
    },
  ];
}

export function simulateUserPrompt(prompt: string): {
  messages: ChatMessage[];
  hitl?: HitlRequest;
  touch: string[];
} {
  const ts = Date.now();
  const active = pick(AGENTS, 5).map((a) => a.id);
  const hermes = AGENTS.find((a) => a.id === "hermes_ops")!;
  const scout = AGENTS.find((a) => a.id === "product_scout")!;

  const messages: ChatMessage[] = [
    { id: `u_${ts}`, role: "user", content: prompt, ts },
    {
      id: `h_${ts}`,
      role: "agent",
      agentId: hermes.id,
      content: `Acknowledged. Coordinating swarm for: “${prompt.slice(0, 120)}${prompt.length > 120 ? "…" : ""}”`,
      ts: ts + 1,
      genui: [
        {
          kind: "swarm_status",
          title: "Swarm activation",
          data: { active, workflow: "full_product_lifecycle" },
        },
      ],
    },
    {
      id: `s_${ts}`,
      role: "agent",
      agentId: scout.id,
      content: "Generative UI preview — live AgentOS wiring hooks in next iteration.",
      ts: ts + 2,
      genui: [
        {
          kind: "product_rank",
          title: "Live rank snapshot",
          data: {
            niche: prompt.slice(0, 40) || "general",
            winners: [
              { name: "Signal Kit Alpha", score: 72, price: 47, cm: 22, decision: "TEST" },
              { name: "Signal Kit Beta", score: 61, price: 42, cm: 18, decision: "TEST" },
            ],
          },
        },
        {
          kind: "hitl_spend",
          title: "HITL · Draft spend",
          data: {
            hitlId: `hitl_${ts}`,
            channel: "Meta",
            dailyUsd: 100,
            durationDays: 3,
            objective: "TEST · from cockpit prompt",
            status: "pending",
          },
        },
      ],
    },
  ];

  const hitl: HitlRequest = {
    id: `hitl_${ts}`,
    kind: "ad_spend",
    title: "Approve Meta TEST budget",
    detail: prompt.slice(0, 160),
    amountUsd: 300,
    agentId: "growth_media_buyer",
    status: "pending",
  };

  return { messages, hitl, touch: active };
}

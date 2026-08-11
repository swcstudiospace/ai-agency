# Architecture overview

```text
Humans (Telegram / TUI / Cockpit / Linear)
                 |
          Hermes Agent (orchestrator)
                 | MCP
     +-----------+-----------+
     v           v           v
AgentOS :7777  Drop :7788  Bridge :7790
30 agents      CoT x GoT   browser/skills
12 teams       Linear      KIP dual-write
11 workflows   lifecycle   CUA jobs
     \           |           /
      \          v          /
       Anda Nexus :8091 (KIP)
                 |
 Parallel | SuperGrok | Shopify | Meta/TikTok | PromptWise/Fal
```

## Design principles

1. Hermes is boss — agents never unsupervised-pay
2. Thin agent modules — thick prompts/ personas + skills
3. Dual-write work — Linear SWC + GitHub ai-agency
4. Draft by default — Shopify drafts, ad drafts, HITL spend
5. Shared memory — KIP/Anda, not only chat history

# Linear ↔ GitHub linking

## Canonical repo
**`swcstudiospace/ai-agency`** — dropshipping agency codebase.

Not: `agent_runtime` / `Agent Runtime` (wrong product).

## What we fixed
Agency issues **SWC-60 … SWC-66** had Linear GitHub attachments pointing at
`swcstudiospace/agent_runtime` (and some historical `swcstudio/agent_runtime`).

Those attachments were deleted and replaced with issues on **ai-agency**:

| Linear | GitHub |
|--------|--------|
| SWC-66 | https://github.com/swcstudiospace/ai-agency/issues/1 |
| SWC-65 | https://github.com/swcstudiospace/ai-agency/issues/2 |
| SWC-64 | https://github.com/swcstudiospace/ai-agency/issues/3 |
| SWC-63 | https://github.com/swcstudiospace/ai-agency/issues/4 |
| SWC-62 | https://github.com/swcstudiospace/ai-agency/issues/5 |
| SWC-61 | https://github.com/swcstudiospace/ai-agency/issues/6 |
| SWC-60 | https://github.com/swcstudiospace/ai-agency/issues/7 |

## Ongoing behavior
`create_linear_issue()` now best-effort:
1. Creates a GitHub issue on `LINEAR_GITHUB_REPO` (default `swcstudiospace/ai-agency`)
2. Removes any stray `agent_runtime` attachments
3. Links via `attachmentLinkGitHubIssue`

Env:
```bash
LINEAR_GITHUB_REPO=swcstudiospace/ai-agency
LINEAR_GITHUB_LINK=1   # set 0 to disable auto GH issues
```

## One-time Linear UI setting (recommended)
In Linear → **Settings → Integrations → GitHub** for workspace **spectrumwebco**:
1. Connect / prefer repository **`swcstudiospace/ai-agency`**
2. Disconnect or uncheck **agent_runtime** as the default for team **SWC**
3. Ensure project **AI Dropshipping Agency** maps to **ai-agency**

Until the workspace default is changed, Linear’s *automatic* two-way sync may still
prefer agent_runtime for some branch actions — our dual-write path forces ai-agency.

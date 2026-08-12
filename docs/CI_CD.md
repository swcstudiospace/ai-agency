# CI/CD (SOTA)

## Philosophy

We do **not** treat “ad-hoc smoke” as CI. GitHub Actions is the source of truth.

| Layer | What | Fail closed? |
|-------|------|--------------|
| **Lint** | Ruff on Python packages | Yes |
| **Unit tests** | Pytest + coverage XML | Yes (`fail_under` in pyproject) |
| **Agent evals** | Personas, skills, toolbelts, AgentOS 30/12/12 | Yes |
| **README gate** | Living doc — paths + scale numbers | Yes |
| **Cockpit** | Vite PWA production build | Yes |
| **Docs** | Docusaurus production build | Yes |
| **Storefront** | Oxygen/ego.engineer Vite build | Yes |
| **Security** | Gitleaks + pip-audit + npm audit | Job must pass; audits may warn |
| **CD Docs** | GitHub Pages from `docs-site/build` | On main path push |

## Workflows

```text
.github/workflows/
  ci.yml                 # umbrella + ci-success aggregate
  ci-backend.yml         # ruff · pytest+cov · evals · README
  ci-cockpit.yml         # agency-cockpit PWA (+ optional Tauri)
  ci-docs.yml            # Docusaurus
  ci-storefront.yml      # storefront-oxygen
  ci-security.yml        # gitleaks · audits
  cd-docs.yml            # GitHub Pages deploy
  agency-cockpit-package.yml  # heavier desktop packages
```

## Local parity

```bash
cd /root/src/repos/ai-agency
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export PYTHONPATH=. AGENCY_DISABLE_HERMES_BRIDGE=1 AGENCY_DISABLE_ANDA_BRAIN=1
export XAI_API_KEY=missing-ci-placeholder LINEAR_GITHUB_LINK=0

ruff check agents app tools teams workflows scripts tests evals
pytest tests/ --cov=tools --cov-report=term-missing
python -m evals.run_agent_evals
python -m scripts.check_readme_freshness
```

## Branch protection (recommended)

Require status check: **All CI gates green** (`ci-success` job).

## Living README policy

Every feature PR must update `README.md` when it changes:

- ports, counts (agents/teams/workflows)
- scripts / pipelines
- env vars operators need
- CI/CD surface

Enforced by `scripts/check_readme_freshness.py` in CI.

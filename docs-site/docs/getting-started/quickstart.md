# Quick start

## Prerequisites

- Python 3.12+
- Node 18+ (cockpit + docs)
- Parallel API key
- SuperGrok OAuth (or XAI_API_KEY)
- Optional: Shopify shop + Dev Dashboard app, Linear key

## Install and run AgentOS

```bash
cd /path/to/ai-agency
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env
python -m tools.xai_oauth_pkce login
./scripts/start_agentos.sh
```

## First product rank

```bash
PYTHONPATH=. python -m scripts.autonomous_product_rank \
  --niche "desk mobility for remote workers" \
  --processor ultra
```

## First supplier locate

```bash
PYTHONPATH=. python -m scripts.autonomous_product_locate --top 3 --processor pro
```

## Docs site

```bash
cd docs-site && npm install && npm start
```

## Cockpit UI

```bash
cd agency-cockpit && npm install && npm run dev
```

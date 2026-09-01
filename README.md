# Mother AI — Autonomous AI Control Plane

Mother AI is a layered, governed agent platform. The FastAPI gateway is the single control plane; Streamlit is the current operator console. The system separates executive coordination from business agents and keeps high-impact actions behind explicit approval.

## Current architecture

```text
Dashboard (Streamlit / future React)
             |
             v
      FastAPI Gateway 2.2
       /healthz /readyz
       /status /agents /catalog
       /executive/* /start /stop
             |
      +------+------+
      |             |
 Supervisor     Event Bus
      |
 +----+----+----------------+
 |    |    |                |
Mother Crypto Gold       Content
 |                         |
Scheduler / Workflow      Learning
```

## Agent catalog v1.0

The product catalog contains **50 agents** across Executive, Finance, Trading, Learning, Content, Business, Intelligence, Infrastructure, Security, Development, and Communication.

`GET /catalog` exposes the complete catalog. `GET /agents` exposes only hydrated runtime agents. This distinction prevents a planned capability from being represented as a working integration.

Current runtime implementations include Mother, Scheduler, Workflow, Learning, Crypto, Gold, and Content. LinkedIn remains an existing integration that is disabled until credentials/configuration are supplied. The remaining catalog entries are safe scaffolds until their real adapters and business logic are implemented.

## Executive governance

Mother Agent creates decisions; it does not directly execute business tasks. High-impact actions require approval. Available endpoints include:

- `GET /executive/status`
- `POST /executive/decide`
- `POST /executive/approve`
- `POST /executive/dispatch/{decision_id}`

Code changes follow proposal -> tests -> human approval -> staged deployment. The Learning Engine must never directly rewrite production source code.

## Trading safety

Crypto and Gold remain `paper=true` and `mode=shadow` by default. Live execution is not enabled by the catalog and should only be introduced after independent risk controls, audit logging, canarying, and explicit approval are in place.

## Run locally

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m mother_ai.run --smoke-test
python -m mother_ai.run
```

Gateway: `http://127.0.0.1:8000`

For the Streamlit console:

```powershell
streamlit run streamlit_app.py
```

The Streamlit console starts the private gateway on `MOTHER_BACKEND_PORT` (default `8001`) and validates liveness before use.

## API contract

- `GET /healthz` — process liveness and API version.
- `GET /readyz` — database, registry, and runtime readiness.
- `GET /status` — complete runtime state.
- `GET /agents` — loaded runtime agents.
- `GET /catalog` — all 50 product capabilities.
- `GET /agents/{agent_key}` — one runtime agent.
- `POST /start` / `POST /stop` — authenticated lifecycle control.

## Google Cloud target

- Cloud Run: stateless gateway/API/console services.
- GKE: only persistent or specialized long-running agents.
- Cloud SQL PostgreSQL: production durable state.
- Pub/Sub: production event bus.
- Vertex AI: managed model training/evaluation/inference where appropriate.
- Secret Manager: credentials and API secrets.
- Artifact Registry: immutable images.
- Cloud Storage: reports, models, backups, and artifacts.
- Cloud Monitoring/Logging: observability.
- IAM: least privilege.
- Cloud Build/GitHub Actions: CI/CD.

See `docs/AGENT_CATALOG_V1.md` and `docs/ARCHITECTURE_V2.md` for the detailed design.

## Security

Never commit `.env`, exchange keys, OAuth secrets, JWT secrets, or webhook credentials. Use environment variables locally and Secret Manager in production.

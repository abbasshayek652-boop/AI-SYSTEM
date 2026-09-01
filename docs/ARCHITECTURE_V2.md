# Mother AI Architecture v2

## Control plane

Streamlit or a future React console talks to one FastAPI Gateway. The gateway owns authentication, authorization, agent lifecycle, health/readiness, catalog, executive decisions, audit hooks, and API contracts.

## Agent plane

The Supervisor owns lifecycle and periodic ticks. Agents are isolated so a status/tick failure in one agent does not take down the control plane.

## Executive plane

Mother Agent creates prioritized decisions. Scheduler Agent coordinates timing. Workflow Agent dispatches approved workflow definitions. These agents do not bypass governance.

## Event-driven evolution

The next infrastructure step is to introduce an event bus abstraction with an in-process implementation for development and Google Pub/Sub for production. Agent messages should be structured events rather than direct imports between business agents.

## Data plane

Development can continue with SQLite. Production should move durable state to PostgreSQL/Cloud SQL. Object artifacts belong in Cloud Storage. Secrets belong in Secret Manager. Redis is optional for transient coordination/caching.

## Deployment

- Cloud Run: gateway, console/API, stateless services.
- GKE: only agents that genuinely need persistent processes or specialized runtime resources.
- Artifact Registry: versioned images.
- Cloud Build/GitHub Actions: CI/CD.
- Cloud Monitoring/Logging: metrics, logs, alerts.

## Promotion pipeline

`development -> tests -> staging -> approval -> production`

No learning component should directly write production source code. Code and configuration changes pass through proposal, testing, approval, and staged deployment.

## Versioning

The API advertises `2.2` and the agent catalog advertises `1.0`. Clients should use these values for compatibility checks instead of assuming that a successful `/healthz` means every control-plane endpoint exists.

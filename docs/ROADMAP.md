# Mother AI Implementation Roadmap

## Product goal

Build a Streamlit-first personal AI operating system in which Streamlit is the operator cockpit, FastAPI is the single control plane, agents perform domain work, adapters connect external services, and a durable event stream makes the system observable.

The system should grow incrementally. A capability is not considered production-ready merely because an agent class or catalog entry exists.

## Phase 0 — Stable foundation

**Goal:** keep the existing control plane reliable.

- FastAPI gateway starts deterministically.
- Streamlit can reuse one backend process safely.
- Registry loading is deterministic and rejects duplicate keys.
- Health/readiness endpoints are explicit.
- CI compiles the project and runs tests.
- Do not expand runtime agents until this baseline is green.

**Exit gate:** startup is repeatable and the full test suite is green.

## Phase 1 — Runtime control plane

**Goal:** reliably operate the existing runtime agents.

- Registry-driven agent lifecycle.
- Start/stop controls with RBAC.
- Circuit breaker and idempotency protection.
- Agent status and catalog separation.
- Mother Executive decision endpoint.

**Exit gate:** every runtime operation is auditable and failure-isolated.

## Phase 2 — Observability + Connections foundation

**Goal:** make the system understandable before connecting real accounts.

Implemented in this phase:

- Durable `AgentEvent` event store.
- `/observability/events` with filters.
- `/observability/connections` with non-secret configuration status.
- Connection definitions for Binance, LinkedIn, Telegram, and GitHub.
- Streamlit Connections page.
- Streamlit Activity Timeline page.
- Startup/login/shutdown and agent-discovery events.
- Regression tests for secret non-disclosure and connection state.

**Important:** this phase does not make external API calls.

**Exit gate:** the operator can see system state, known connections, and a durable activity history without exposing credentials.

## Phase 3 — Adapter contract + connectivity tests

**Goal:** establish one consistent interface for external services.

Create:

- `ConnectionAdapter` interface.
- `ConnectionHealth` result model.
- credential/config validation separated from network connectivity.
- timeout, retry, and error normalization rules.
- per-connection health checks.
- adapter unit tests with mocked HTTP clients.

No publishing, trading, deleting, messaging, or other consequential side effects.

**Exit gate:** every adapter can report `configured`, `reachable`, `authenticated`, and `error` without exposing secrets.

## Phase 4 — Binance read-only adapter

**Goal:** bring exchange account visibility into the cockpit without enabling actions.

- Account connection status.
- Read-only balances.
- Read-only account metadata allowed by the API.
- Market/account timestamps.
- Sync status and last successful sync.
- Activity events for every synchronization.
- Explicit read-only capability flag.

Keep permissions minimal. Never place credentials in source code or UI logs.

**Exit gate:** Streamlit can show current account data and sync health while the adapter has no write capability.

## Phase 5 — LinkedIn draft + approval pipeline

**Goal:** connect content workflows without uncontrolled publishing.

- Account health.
- Profile identity where permitted.
- Draft generation.
- Draft storage.
- Approval queue.
- Preview.
- Publish action behind explicit operator approval.
- Publish result and audit event.

**Exit gate:** Mother can propose content, but publishing remains a deliberate operator action.

## Phase 6 — Unified account cockpit

**Goal:** make Streamlit the single operational view.

Pages:

1. Overview
2. Mother Executive
3. Connections
4. Activity
5. Approvals
6. Finance
7. Content
8. Intelligence
9. Business
10. Development
11. Alerts
12. System

Overview should answer immediately:

- Is Mother healthy?
- Which services are connected?
- Which agents are running?
- What happened recently?
- What needs approval?
- What failed?
- When was each service last synchronized?

## Phase 7 — Event-driven orchestration

**Goal:** move from isolated agents to coordinated workflows.

- Canonical event schema.
- Correlation IDs.
- Event categories: system, agent, integration, decision, approval, action, error.
- Event retention policy.
- Mother consumes events and produces decisions.
- Workflow execution records every step.
- Failed workflows can be inspected and retried safely.

## Phase 8 — Approval and policy engine

**Goal:** define what Mother may observe, recommend, or execute.

Capabilities should have explicit levels:

- `observe`
- `analyze`
- `recommend`
- `draft`
- `execute_with_approval`
- `execute_automatically`

High-impact external actions should remain approval-gated until there is a strong reason and a tested policy to automate them.

## Phase 9 — Expand agents by domain

Do not activate all 50 catalog entries at once.

Recommended order:

1. Executive
2. Observability / Infrastructure
3. Finance
4. Content
5. Intelligence
6. Development
7. Business
8. Communication
9. Advanced AI layer

Each agent must have:

- registry entry
- capability declaration
- status contract
- event emission
- tests
- failure behavior
- permission boundary
- UI representation

## Phase 10 — Production hardening

- Secrets management.
- Database backups and restore testing.
- Structured logs.
- Metrics and alerts.
- Rate-limit review.
- Dependency pinning/lock strategy.
- Database migration tooling.
- Recovery procedures.
- Security review.
- End-to-end smoke tests.

## Definition of done

A Mother AI capability is **done** only when its UI, API, agent, adapter, persistence, events, permissions, tests, and failure handling agree with each other.

The 50-agent catalog is therefore a product roadmap, not a promise that 50 independent autonomous workers are already safe or production-ready.

# Mother AI — Full System Implementation

This document defines the production path for the Streamlit-first system.

## Control flow

```text
Streamlit cockpit
  -> FastAPI control plane
  -> policy / approval boundary
  -> Mother / supervisor / agent
  -> integration adapter
  -> external service
  -> canonical event
  -> durable event store
  -> Streamlit Activity / Alerts
```

Streamlit is presentation and operator control. It must not contain service credentials or bypass FastAPI.

## Account model

Each external service is represented by a connection definition and an adapter. A connection reports:

- configured
- reachable
- authenticated
- healthy
- capabilities
- last error

Secrets are never returned from connection endpoints.

## Capability model

Every consequential capability is explicitly classified:

- `observe`
- `analyze`
- `recommend`
- `draft`
- `execute_with_approval`
- `execute_automatically`

The default policy keeps publishing, messaging, and trading behind approval.

## Binance

The first exchange adapter is intentionally read-only. Its capabilities are account/balance/market reads. It contains no order-placement method. Sandbox mode defaults to true.

The cockpit should show account data only after credentials are configured locally. Credentials belong in the runtime secret environment, never in Git, logs, Streamlit widgets, or event payloads.

## LinkedIn

The publishing workflow is approval-based:

1. create content/draft
2. request `content.publish` approval
3. operator reviews the payload
4. operator approves
5. a separate publish endpoint verifies the approval
6. the LinkedIn service performs the publish
7. the result is recorded as an event

Scheduled publishing must remain disabled unless an explicit tested automation policy is introduced.

## Events

Canonical events carry a `_meta` envelope with:

- schema version
- category
- source
- correlation ID

Categories are system, agent, integration, decision, approval, action, and error.

## Agent expansion

The 50-agent catalog is a product map. Catalog entries are not automatically runtime workers. New runtime agents must provide a registry entry, capability declaration, events, policy boundary, persistence behavior, tests, and failure handling.

A safe `ScaffoldAgent` exists for future catalog capabilities; it has no external side effects and is not automatically loaded.

## Production gates

Before calling the system production-ready:

1. CI is green.
2. Streamlit starts exactly one healthy gateway.
3. Every external adapter has mocked unit tests and timeout/error handling.
4. Database migrations and backups are tested.
5. Secrets are supplied only through the deployment environment.
6. High-impact actions are approval-gated.
7. End-to-end smoke tests cover login, connection health, agent lifecycle, event creation, approval, and failure recovery.

No Google Cloud dependency is required by this architecture.

# Mother AI — Streamlit Runtime Architecture

## Deployment target

Version 2.x is intentionally designed to run as a single Streamlit application with a local FastAPI control plane inside the same Streamlit process/container. No cloud infrastructure is required for this version.

```text
Browser
  |
  v
Streamlit UI
  |
  +--> FastAPI Gateway : local process
          |
          +--> Supervisor
          +--> Scheduler
          +--> Mother / Executive
          +--> 50 runtime agents
          +--> SQLite / local persistence
          +--> local event bus
```

## Agent model

The 50-agent catalog is the product contract. Every catalog entry is hydrated into a real `Agent` runtime instance. Existing specialized agents keep their existing implementations; other capabilities use the safe `CatalogRuntimeAgent` until a domain-specific implementation is added.

This means the dashboard can start, stop, inspect and execute every agent without pretending that an external integration exists.

## Safety boundary

- Crypto and Gold remain paper/shadow by default.
- LinkedIn publishing is disabled until explicit OAuth configuration is supplied.
- Deployment, code changes and live trading require Mother approval.
- Learning produces recommendations; it does not silently modify source code.
- Generic catalog agents have `external_side_effects=false`.

## Control-plane API

- `GET /healthz`
- `GET /readyz`
- `GET /status`
- `GET /agents`
- `GET /agents/{agent_key}`
- `POST /agents/{agent_key}/execute`
- `GET /catalog`
- `GET /catalog/{agent_key}`
- `POST /start`
- `POST /stop`
- `GET /executive/status`
- `POST /executive/decide`
- `POST /executive/approve`
- `POST /executive/dispatch/{decision_id}`

## Runtime lifecycle

```text
Catalog
  -> Registry
  -> Hydration
  -> Supervisor
  -> Start / Stop
  -> Tick loop
  -> Status / Execute
```

The Streamlit launcher validates the gateway API version before accepting a backend as healthy. This prevents an old gateway process from being mistaken for a current one.

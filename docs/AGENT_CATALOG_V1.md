# Mother AI — Complete Agent Catalog v1.0

Mother AI is organized as a layered control plane. The catalog contains 50 capabilities across Executive, Finance, Trading, Learning, Content, Business, Intelligence, Infrastructure, Security, Development, and Communication.

## Runtime status model

- **implemented** — a real agent implementation is already wired into the runtime.
- **existing** — an integration exists but is intentionally disabled until credentials/configuration are supplied.
- **scaffold** — the capability is defined and represented in the product catalog, but must not be mistaken for a production integration.

The dashboard exposes all 50 capabilities through `GET /catalog` while `GET /agents` reports only currently hydrated runtime agents.

## Executive rule

Mother Agent coordinates work; it does not directly perform business tasks. High-impact actions such as live trading, deployment, and code changes require explicit approval.

## Learning and self-improvement rule

The Learning Engine consumes telemetry and produces recommendations. It must not directly mutate source code. The intended path is:

1. telemetry and outcomes are collected;
2. learning/evaluation produces a recommendation;
3. Recommendation or Code Suggestion Agent proposes a change;
4. automated tests validate the proposal;
5. a human approves the change;
6. Deployment Agent promotes it through staged environments.

## Trading safety rule

Crypto and Gold remain paper/shadow by default. Live execution must remain behind independent risk controls and explicit approval. A catalog entry is never permission to execute a trade.

## Planned expansion

The post-v2 layer may add voice, meetings, calendar/email assistants, browser automation, customer support, RAG, multi-LLM routing, computer vision, AutoML, forecasting, and digital-twin capabilities after the core control plane is stable.

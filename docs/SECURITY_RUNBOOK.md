# Security and recovery runbook

## Secrets

Never commit API keys, JWT secrets, database passwords, OAuth tokens, or private URLs containing credentials.

If a secret ever reaches Git history, treat it as compromised even after the file is edited. Rotate the credential at its provider and then remove the historical secret from repository history using a controlled history-rewrite procedure.

## Runtime rules

- Streamlit receives no raw external credentials through widgets.
- Event payloads must not contain tokens, passwords, API secrets, or authorization headers.
- Integration health responses expose only boolean state, safe capabilities, and sanitized error classes.
- Binance remains read-only by default and sandbox mode is the default.
- Publishing, messaging, and trading actions require explicit policy/approval unless a future policy explicitly changes that state.

## Recovery

1. Stop the gateway.
2. Preserve the latest logs for diagnosis without exposing secrets.
3. Run `scripts/backup.sh`.
4. Verify the backup files exist and are readable.
5. Restore into a separate test database first.
6. Only replace the production database after validation.
7. Restart and verify `/healthz`, `/readyz`, connection health, and event history.

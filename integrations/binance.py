from __future__ import annotations

import os
import time
from typing import Any

from integrations.base import ConnectionAdapter, ConnectionHealth


class BinanceReadOnlyAdapter(ConnectionAdapter):
    key = "binance"
    capabilities = ("account.read", "balances.read", "market.read")

    def __init__(self) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.sandbox = os.getenv("BINANCE_SANDBOX", "true").lower() == "true"

    def health_check(self) -> ConnectionHealth:
        checked = time.time()
        if not self.api_key or not self.api_secret:
            return ConnectionHealth(
                key=self.key,
                configured=False,
                checked_at=checked,
                capabilities=self.capabilities,
                error="BINANCE_API_KEY and BINANCE_API_SECRET are not configured",
            )
        try:
            import ccxt

            exchange = ccxt.binance({
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            })
            if self.sandbox:
                exchange.set_sandbox_mode(True)
            exchange.check_required_credentials()
            exchange.fetch_balance()
            return ConnectionHealth(
                key=self.key,
                configured=True,
                reachable=True,
                authenticated=True,
                checked_at=checked,
                capabilities=self.capabilities,
            )
        except Exception as exc:  # noqa: BLE001
            return ConnectionHealth(
                key=self.key,
                configured=True,
                reachable=False,
                authenticated=False,
                checked_at=checked,
                capabilities=self.capabilities,
                error=type(exc).__name__,
            )

    def fetch_balances(self) -> dict[str, Any]:
        """Fetch balances only; this adapter intentionally has no order methods."""
        if not self.api_key or not self.api_secret:
            raise RuntimeError("Binance credentials are not configured")
        import ccxt

        exchange = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
        if self.sandbox:
            exchange.set_sandbox_mode(True)
        return exchange.fetch_balance()

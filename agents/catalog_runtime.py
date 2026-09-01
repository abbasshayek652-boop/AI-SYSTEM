from __future__ import annotations

import datetime as dt
import statistics
from typing import Any

from ai.agent_catalog import get_catalog_entry
from ai.base_agent import Agent


class CatalogRuntimeAgent(Agent):
    """Safe local runtime for catalog capabilities.

    Every catalog capability is a real Agent and can be inspected, started,
    stopped and exercised through a deterministic local API. External side
    effects are deliberately disabled here; integrations can be added behind
    explicit adapters later.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.key = str(config.get("key", "unknown"))
        entry = get_catalog_entry(self.key) or {}
        self.name = str(entry.get("name", self.key))
        self.layer = str(entry.get("layer", "Unknown"))
        self.description = str(entry.get("role", "Catalog runtime agent"))
        self.capabilities = list(entry.get("capabilities", []))
        self.started_at: str | None = None
        self.last_action: str | None = None
        self.action_count = 0
        self._state: dict[str, Any] = {}

    async def start(self) -> None:
        self.running = True
        self.started_at = dt.datetime.now(dt.timezone.utc).isoformat()

    async def stop(self) -> None:
        self.running = False

    async def status(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "runtime": "local",
            "external_side_effects": False,
            "key": self.key,
            "layer": self.layer,
            "capabilities": self.capabilities,
            "started_at": self.started_at,
            "last_action": self.last_action,
            "action_count": self.action_count,
            "state_keys": sorted(self._state.keys()),
        }

    async def on_tick(self) -> None:
        # Keep catalog agents lightweight on Streamlit's single process.
        if self.running:
            self._state["last_tick"] = dt.datetime.now(dt.timezone.utc).isoformat()

    async def execute(self, action: str = "inspect", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        action = (action or "inspect").strip().lower()
        self.last_action = action
        self.action_count += 1

        if action in {"inspect", "status"}:
            return await self.status()

        handler = getattr(self, f"_action_{self.key}", None)
        if handler is not None:
            return handler(action, payload)

        return {
            "ok": True,
            "agent": self.key,
            "action": action,
            "result": "accepted_for_local_processing",
            "external_side_effects": False,
            "payload": payload,
        }

    def _action_wallet(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        accounts = self._state.setdefault("accounts", {})
        if action == "set_account":
            name = str(payload.get("name", "account"))
            accounts[name] = float(payload.get("balance", 0.0))
        total = sum(float(v) for v in accounts.values())
        return {"ok": True, "accounts": accounts, "total_net_worth": round(total, 2), "currency": payload.get("currency", "USD")}

    def _action_accounting(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        ledger = self._state.setdefault("ledger", [])
        if action == "add":
            ledger.append({"type": payload.get("type", "expense"), "amount": float(payload.get("amount", 0)), "category": payload.get("category", "uncategorized")})
        income = sum(x["amount"] for x in ledger if x["type"] == "income")
        expense = sum(x["amount"] for x in ledger if x["type"] == "expense")
        return {"ok": True, "entries": len(ledger), "income": round(income, 2), "expenses": round(expense, 2), "profit": round(income - expense, 2)}

    def _action_financial_planner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        income = float(payload.get("income", 0))
        expenses = float(payload.get("expenses", 0))
        savings_target = max(0.0, income - expenses)
        return {"ok": True, "income": income, "expenses": expenses, "available": round(savings_target, 2), "recommended_savings": round(savings_target * 0.5, 2)}

    def _action_strategy(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        prices = [float(x) for x in payload.get("prices", [])]
        if len(prices) < 2:
            return {"ok": True, "signal": "insufficient_data", "required": 2}
        fast = statistics.mean(prices[-min(5, len(prices)):])
        slow = statistics.mean(prices)
        signal = "buy" if fast > slow else "sell" if fast < slow else "hold"
        return {"ok": True, "signal": signal, "fast_mean": fast, "slow_mean": slow}

    def _action_backtesting(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        returns = [float(x) for x in payload.get("returns", [])]
        if not returns:
            return {"ok": True, "trades": 0, "total_return": 0.0, "win_rate": 0.0, "max_drawdown": 0.0}
        equity = 1.0
        peak = equity
        max_dd = 0.0
        wins = 0
        for value in returns:
            equity *= 1.0 + value
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak)
            wins += value > 0
        avg = statistics.mean(returns)
        stdev = statistics.stdev(returns) if len(returns) > 1 else 0.0
        sharpe = (avg / stdev) * (len(returns) ** 0.5) if stdev else 0.0
        return {"ok": True, "trades": len(returns), "total_return": round(equity - 1, 6), "win_rate": round(wins / len(returns), 4), "max_drawdown": round(max_dd, 4), "sharpe": round(sharpe, 4)}

    def _action_risk(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        equity = float(payload.get("equity", 0))
        daily_loss = float(payload.get("daily_loss", 0))
        exposure = float(payload.get("exposure", 0))
        max_loss = float(payload.get("max_daily_loss", equity * 0.02 if equity else 0))
        blocked = equity <= 0 or daily_loss >= max_loss or exposure > float(payload.get("max_exposure", equity * 0.5 if equity else 0))
        return {"ok": True, "blocked": blocked, "daily_loss": daily_loss, "exposure": exposure, "max_daily_loss": max_loss}

    def _action_portfolio(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        capital = float(payload.get("capital", 0))
        weights = payload.get("weights", {})
        total = sum(float(v) for v in weights.values())
        normalized = {k: round(float(v) / total, 6) for k, v in weights.items()} if total else {}
        amounts = {k: round(capital * v, 2) for k, v in normalized.items()}
        return {"ok": True, "weights": normalized, "amounts": amounts, "weight_total": round(sum(normalized.values()), 6)}

    def _action_market_regime(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        prices = [float(x) for x in payload.get("prices", [])]
        if len(prices) < 3:
            return {"ok": True, "regime": "unknown"}
        change = (prices[-1] / prices[0]) - 1 if prices[0] else 0
        volatility = statistics.pstdev(prices) / statistics.mean(prices) if statistics.mean(prices) else 0
        regime = "bull" if change > 0.05 else "bear" if change < -0.05 else "volatile" if volatility > 0.1 else "sideways"
        return {"ok": True, "regime": regime, "change": round(change, 4), "relative_volatility": round(volatility, 4)}

    def _action_memory(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        memories = self._state.setdefault("memories", [])
        if action == "remember":
            memories.append({"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "value": payload.get("value")})
        return {"ok": True, "count": len(memories), "recent": memories[-10:]}

    def _action_recommendation(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "recommendation": payload.get("recommendation", "collect more evidence"), "approval_required": True, "side_effects": False}

    def _action_self_evaluation(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        metrics = [float(v) for v in payload.get("metrics", [])]
        score = sum(metrics) / len(metrics) if metrics else 0.0
        return {"ok": True, "score": round(max(0.0, min(100.0, score)), 2), "sample_count": len(metrics)}

    def _action_content(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        topic = str(payload.get("topic", "Mother AI"))
        draft = f"Draft content about {topic}. This is a local draft and has not been published."
        return {"ok": True, "draft": draft, "published": False}

    def _action_seo(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        keywords = [str(x) for x in payload.get("keywords", [])]
        return {"ok": True, "keywords": [{"keyword": k, "length": len(k.split())} for k in keywords]}

    def _action_news(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "items": list(payload.get("items", [])), "source": "local_input", "fetched": False}

    def _action_sentiment(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload.get("text", "")).lower()
        positive = sum(text.count(w) for w in ("good", "positive", "growth", "up", "win"))
        negative = sum(text.count(w) for w in ("bad", "negative", "loss", "down", "risk"))
        label = "positive" if positive > negative else "negative" if negative > positive else "neutral"
        return {"ok": True, "sentiment": label, "positive_hits": positive, "negative_hits": negative}

    def _action_health(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "checks": {"process": "ok", "database": "not_checked", "network": "not_checked"}, "note": "Local Streamlit health mode"}

    def _action_testing(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "tests_requested": payload.get("tests", ["smoke"]), "executed": False, "reason": "Use CI or an approved local runner for subprocess tests."}

    def _action_debug(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload.get("error", ""))
        return {"ok": True, "error_type": "unknown" if not text else text.split(":", 1)[0], "message": text, "suggestion": "capture the full traceback and reproduce with a focused test"}

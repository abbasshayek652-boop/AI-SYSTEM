from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from gateway.auth import AuthContext, get_viewer
from integrations.binance import BinanceReadOnlyAdapter
from integrations.bootstrap import register_default_adapters
from integrations.registry import get_adapter, health_all
from services.canonical_events import emit

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/health")
async def health(_: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    register_default_adapters()
    items = [item.public_dict() for item in health_all()]
    for item in items:
        emit(
            "integration.health_checked",
            category="integration",
            source="integration-health",
            payload={
                "key": item["key"],
                "configured": item["configured"],
                "reachable": item["reachable"],
                "authenticated": item["authenticated"],
                "healthy": item["healthy"],
            },
        )
    return {"count": len(items), "healthy_count": sum(bool(item["healthy"]) for item in items), "items": items}


@router.get("/binance/balances")
async def binance_balances(_: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    """Read-only Binance balance snapshot; no trading/execution capability is exposed."""
    register_default_adapters()
    adapter = get_adapter("binance")
    if not isinstance(adapter, BinanceReadOnlyAdapter):
        raise HTTPException(status_code=503, detail="Binance read-only adapter unavailable")
    try:
        raw = adapter.fetch_balances()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        emit("integration.balance_failed", category="integration", source="binance", payload={"error": type(exc).__name__})
        raise HTTPException(status_code=502, detail="Binance balance request failed") from exc

    balances: list[dict[str, Any]] = []
    totals = raw.get("total", {}) or {}
    free = raw.get("free", {}) or {}
    used = raw.get("used", {}) or {}
    for asset, total in totals.items():
        try:
            total_value = float(total or 0)
        except (TypeError, ValueError):
            continue
        if total_value == 0:
            continue
        balances.append({
            "asset": asset,
            "free": float(free.get(asset) or 0),
            "used": float(used.get(asset) or 0),
            "total": total_value,
        })

    emit(
        "integration.balance_read",
        category="integration",
        source="binance",
        payload={"asset_count": len(balances), "sandbox": adapter.sandbox},
    )
    return {"key": "binance", "sandbox": adapter.sandbox, "read_only": True, "balances": balances}

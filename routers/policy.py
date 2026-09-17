from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from gateway.auth import AuthContext, get_viewer
from policy.engine import policy_engine

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("")
async def policies(_: AuthContext = Depends(get_viewer)) -> dict[str, Any]:
    return {"count": len(policy_engine.public_policies()), "items": policy_engine.public_policies()}

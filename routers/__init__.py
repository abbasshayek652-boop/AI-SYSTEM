from routers.agents import router as agents_router
from routers.catalog import router as catalog_router
from routers.console import router as console_router
from routers.control import router as control_router
from routers.core import router as core_router
from routers.executive import router as executive_router
from routers.learning import router as learning_router
from routers.planner import router as planner_router
from routers.wallet import router as wallet_router

__all__ = [
    "agents_router",
    "catalog_router",
    "console_router",
    "control_router",
    "core_router",
    "executive_router",
    "learning_router",
    "planner_router",
    "wallet_router",
]

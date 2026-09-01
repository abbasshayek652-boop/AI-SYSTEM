from __future__ import annotations

from ai.agent_catalog import catalog
from ai.registry import hydrate_agents, load_registry


def test_registry_loads_all_catalog_agents() -> None:
    registry = load_registry()
    agents = hydrate_agents(registry)
    assert len(catalog()) == 50
    assert len(agents) == 50
    assert {item["key"] for item in catalog()} == set(agents)


def test_runtime_catalog_agents_are_safe_and_inspectable() -> None:
    registry = load_registry()
    agents = hydrate_agents(registry)
    for key, agent in agents.items():
        assert hasattr(agent, "start")
        assert hasattr(agent, "stop")
        assert hasattr(agent, "status")
        if key not in {"crypto", "gold", "learning"}:
            assert getattr(agent, "config", {}).get("key", key) == key or key in {"mother", "scheduler", "workflow", "content", "linkedin"}

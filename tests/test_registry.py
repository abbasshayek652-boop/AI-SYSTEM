from __future__ import annotations

import json

import pytest

from ai.registry import AgentSpec, Registry, load_registry


def test_registry_validation() -> None:
    registry = Registry(
        agents=[AgentSpec(key="learning", module="ai.learning_engine", class_name="LearningAgent")]
    )
    assert registry.agents[0].key == "learning"


def test_default_registry_is_independent_of_cwd(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    registry = load_registry()
    assert len(registry.agents) == 50
    assert len({agent.key for agent in registry.agents}) == 50


def test_registry_rejects_duplicate_keys(tmp_path) -> None:
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(
            {
                "agents": [
                    {"key": "duplicate", "module": "agents.catalog_runtime", "class_name": "CatalogRuntimeAgent"},
                    {"key": "duplicate", "module": "agents.catalog_runtime", "class_name": "CatalogRuntimeAgent"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate agent keys"):
        load_registry(path)

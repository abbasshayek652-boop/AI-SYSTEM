from __future__ import annotations

import importlib
import json
import logging
import pathlib
from typing import Any, Dict, List, Type

from pydantic import BaseModel, Field, ValidationError

from ai.base_agent import Agent

LOGGER = logging.getLogger(__name__)
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class AgentSpec(BaseModel):
    key: str
    module: str
    class_name: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class Registry(BaseModel):
    agents: List[AgentSpec]


def load_registry(path: str | pathlib.Path | None = None) -> Registry:
    """Read and validate the registry independently of the process cwd."""
    registry_path = pathlib.Path(path) if path is not None else BASE_DIR / "registry.json"
    if not registry_path.is_absolute():
        registry_path = BASE_DIR / registry_path

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        registry = Registry(**data)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Invalid registry configuration: {registry_path}") from exc

    keys = [spec.key for spec in registry.agents]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"Duplicate agent keys in registry: {', '.join(duplicates)}")

    return registry


def _resolve_class(module: str, class_name: str) -> Type[Agent]:
    mod = importlib.import_module(module)
    cls = getattr(mod, class_name)
    if not issubclass(cls, Agent):  # type: ignore[arg-type]
        raise TypeError(f"{class_name} is not an Agent subclass")
    return cls


def hydrate_agents(registry: Registry) -> Dict[str, Agent]:
    """Instantiate all enabled agents from the registry."""
    instances: Dict[str, Agent] = {}
    for spec_data in registry.agents:
        spec = spec_data if isinstance(spec_data, AgentSpec) else AgentSpec(**spec_data)
        if not spec.enabled:
            LOGGER.info("Skipping disabled agent %s", spec.key)
            continue
        cls = _resolve_class(spec.module, spec.class_name)
        LOGGER.info("Hydrating agent %s from %s.%s", spec.key, spec.module, spec.class_name)
        instances[spec.key] = cls(spec.config)
    return instances

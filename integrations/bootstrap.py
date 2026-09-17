from __future__ import annotations

from integrations.binance import BinanceReadOnlyAdapter
from integrations.env_adapter import EnvConnectionAdapter
from integrations.registry import all_adapters, register


def register_default_adapters() -> None:
    existing = {adapter.key for adapter in all_adapters()}
    adapters = (
        BinanceReadOnlyAdapter(),
        EnvConnectionAdapter("linkedin", ("LINKEDIN_ACCESS_TOKEN",), ("profile.read", "content.draft", "content.publish.approval")),
        EnvConnectionAdapter("telegram", ("TELEGRAM_BOT_TOKEN",), ("message.send.approval",)),
        EnvConnectionAdapter("github", ("GITHUB_TOKEN",), ("repository.read", "issue.read", "pull_request.read")),
    )
    for adapter in adapters:
        if adapter.key not in existing:
            register(adapter)

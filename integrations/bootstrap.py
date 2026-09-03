from __future__ import annotations

from integrations.binance import BinanceReadOnlyAdapter
from integrations.env_adapter import EnvConnectionAdapter
from integrations.registry import register


def register_default_adapters() -> None:
    if not __import__("integrations.registry", fromlist=["_ADAPTERS"])._ADAPTERS:
        register(BinanceReadOnlyAdapter())
        register(EnvConnectionAdapter("linkedin", ("LINKEDIN_ACCESS_TOKEN",), ("profile.read", "content.draft", "content.publish.approval")))
        register(EnvConnectionAdapter("telegram", ("TELEGRAM_BOT_TOKEN",), ("message.send.approval",)))
        register(EnvConnectionAdapter("github", ("GITHUB_TOKEN",), ("repository.read", "issue.read", "pull_request.read")))

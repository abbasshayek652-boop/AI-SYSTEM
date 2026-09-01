from __future__ import annotations

from typing import Any

# Product-level catalog. Runtime implementations are intentionally separated
# from this catalog so an advertised capability is never mistaken for a live
# production integration.

CATALOG_VERSION = "1.0"

_AGENT_ROWS: tuple[tuple[str, str, str, str, str, tuple[str, ...]], ...] = (
    ("mother", "Executive", "Mother Agent", "CEO / system brain", "implemented", ("decisioning", "coordination", "budgets", "approvals", "n8n")),
    ("scheduler", "Executive", "Scheduler Agent", "system scheduler", "implemented", ("scheduling", "queueing", "retry", "priorities")),
    ("workflow", "Executive", "Workflow Agent", "workflow executor", "scaffold", ("workflows", "n8n", "queue")),
    ("wallet", "Finance", "Wallet Agent", "treasury", "scaffold", ("net worth", "cash", "accounts", "allocation")),
    ("financial_planner", "Finance", "Financial Planner Agent", "financial planning", "scaffold", ("budget", "cash flow", "allocation", "emergency fund")),
    ("accounting", "Finance", "Accounting Agent", "accounting", "scaffold", ("income", "expenses", "invoices", "tax", "pnl")),
    ("investment", "Finance", "Investment Agent", "long-term investing", "scaffold", ("stocks", "etfs", "bitcoin", "gold", "diversification")),
    ("crypto", "Trading", "Crypto Trading Agent", "crypto trading", "implemented", ("market analysis", "signals", "paper", "shadow", "risk")),
    ("gold", "Trading", "Gold Trading Agent", "metals trading", "implemented", ("paxg", "gold", "silver", "risk")),
    ("strategy", "Trading", "Strategy Agent", "strategy research", "scaffold", ("ema", "rsi", "macd", "ml", "optimization")),
    ("backtesting", "Trading", "Backtesting Agent", "historical evaluation", "scaffold", ("history", "benchmarks", "drawdown", "sharpe", "win rate")),
    ("risk", "Trading", "Risk Agent", "independent risk control", "scaffold", ("drawdown", "daily loss", "exposure", "leverage", "correlation")),
    ("portfolio", "Trading", "Portfolio Agent", "portfolio construction", "scaffold", ("position sizing", "allocation", "diversification", "exposure")),
    ("arbitrage", "Trading", "Arbitrage Agent", "cross-market arbitrage", "scaffold", ("cross exchange", "funding", "basis", "price difference")),
    ("market_regime", "Trading", "Market Regime Agent", "market regime detection", "scaffold", ("bull", "bear", "sideways", "volatility")),
    ("learning", "Learning", "Learning Engine", "system learning", "implemented", ("telemetry", "training", "evaluation", "policies")),
    ("memory", "Learning", "Memory Agent", "system memory", "scaffold", ("history", "decisions", "metrics", "errors")),
    ("pattern_recognition", "Learning", "Pattern Recognition Agent", "pattern discovery", "scaffold", ("patterns", "failures", "winning combinations")),
    ("recommendation", "Learning", "Recommendation Agent", "recommendations", "scaffold", ("recommendations", "approval", "configuration")),
    ("self_evaluation", "Learning", "Self Evaluation Agent", "agent evaluation", "scaffold", ("daily", "weekly", "monthly", "scores")),
    ("content", "Content", "Content Agent", "content production", "implemented", ("articles", "linkedin", "twitter", "medium", "newsletter")),
    ("linkedin", "Content", "LinkedIn Agent", "LinkedIn publishing", "existing", ("posts", "documents", "scheduling")),
    ("youtube", "Content", "YouTube Agent", "video publishing", "scaffold", ("videos", "shorts", "seo", "descriptions")),
    ("tiktok", "Content", "TikTok Agent", "short-form publishing", "scaffold", ("shorts", "captions", "hashtags")),
    ("newsletter", "Content", "Newsletter Agent", "email publishing", "scaffold", ("campaigns", "subscribers", "automation")),
    ("seo", "Content", "SEO Agent", "search optimization", "scaffold", ("keywords", "competitors", "ranking", "optimization")),
    ("freelance", "Business", "Freelance Agent", "freelance opportunities", "scaffold", ("jobs", "clients", "projects", "contracts")),
    ("crm", "Business", "CRM Agent", "customer pipeline", "scaffold", ("leads", "sales", "deals", "pipeline")),
    ("proposal", "Business", "Proposal Agent", "business documents", "scaffold", ("pdf", "proposals", "contracts", "invoices")),
    ("research", "Business", "Research Agent", "research synthesis", "scaffold", ("papers", "github", "blogs", "news", "docs")),
    ("opportunity", "Business", "Opportunity Agent", "opportunity discovery", "scaffold", ("market gaps", "products", "income ideas")),
    ("news", "Intelligence", "News Agent", "news intelligence", "scaffold", ("financial", "crypto", "ai", "business")),
    ("sentiment", "Intelligence", "Sentiment Agent", "sentiment intelligence", "scaffold", ("twitter", "reddit", "news", "fear and greed")),
    ("economic", "Intelligence", "Economic Agent", "macro intelligence", "scaffold", ("inflation", "rates", "gdp", "fed", "ecb", "calendar")),
    ("competitor", "Intelligence", "Competitor Agent", "competitive intelligence", "scaffold", ("competitors", "pricing", "products", "features")),
    ("health", "Infrastructure", "Health Agent", "infrastructure health", "scaffold", ("cpu", "ram", "gpu", "disk", "latency")),
    ("monitoring", "Infrastructure", "Monitoring Agent", "observability", "scaffold", ("logs", "metrics", "alerts")),
    ("deployment", "Infrastructure", "Deployment Agent", "deployment automation", "scaffold", ("docker", "cloud run", "kubernetes", "github")),
    ("backup", "Infrastructure", "Backup Agent", "backup management", "scaffold", ("database", "registry", "configuration", "models")),
    ("cost", "Infrastructure", "Cost Agent", "cost management", "scaffold", ("google cloud", "ai apis", "hosting", "budgets")),
    ("security", "Security", "Security Agent", "security controls", "scaffold", ("permissions", "tokens", "secrets", "encryption")),
    ("audit", "Security", "Audit Agent", "audit trail", "scaffold", ("who", "when", "why", "actions")),
    ("compliance", "Security", "Compliance Agent", "policy compliance", "scaffold", ("policies", "security", "rate limits")),
    ("code_suggestion", "Development", "Code Suggestion Agent", "code recommendations", "scaffold", ("analysis", "suggestions", "no direct edits")),
    ("documentation", "Development", "Documentation Agent", "documentation", "scaffold", ("readme", "api docs", "architecture")),
    ("testing", "Development", "Testing Agent", "quality assurance", "scaffold", ("pytest", "integration", "performance")),
    ("debug", "Development", "Debug Agent", "diagnostics", "scaffold", ("errors", "exceptions", "stack traces")),
    ("github", "Development", "GitHub Agent", "repository automation", "scaffold", ("branches", "prs", "issues", "releases", "approval")),
    ("notification", "Communication", "Notification Agent", "unified notifications", "scaffold", ("slack", "discord", "teams", "email", "push", "sms")),
    ("dashboard", "Communication", "Dashboard Agent", "dashboard data service", "scaffold", ("realtime", "charts", "metrics", "controls", "alerts")),
)


def catalog() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "layer": layer,
            "name": name,
            "role": role,
            "implementation": implementation,
            "capabilities": list(capabilities),
        }
        for key, layer, name, role, implementation, capabilities in _AGENT_ROWS
    ]


def get_catalog_entry(key: str) -> dict[str, Any] | None:
    return next((item for item in catalog() if item["key"] == key), None)


def catalog_layers() -> list[str]:
    return list(dict.fromkeys(item["layer"] for item in catalog()))

from ai.agent_catalog import CATALOG_VERSION, catalog, catalog_layers
from agents.mother_agent import MotherAgent


def test_catalog_has_fifty_unique_agents() -> None:
    items = catalog()
    keys = [item["key"] for item in items]
    assert CATALOG_VERSION == "1.0"
    assert len(items) == 50
    assert len(keys) == len(set(keys))
    assert "Executive" in catalog_layers()
    assert "Communication" in catalog_layers()


def test_mother_requires_approval_for_high_impact_actions() -> None:
    mother = MotherAgent({})
    decision = mother.decide("deploy release", ["deployment"], action="deployment")
    assert decision["approval_required"] is True
    assert decision["approved"] is False

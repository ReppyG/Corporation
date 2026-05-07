from agent_builder.config.schema import OrgConfig
from agent_builder.core.organization import Organization


def test_create_agent_and_status():
    cfg = OrgConfig.model_validate({"organization": {"name": "T"}, "agents": []})
    org = Organization(name="T", config=cfg)
    org.create_agent({"id": "ceo", "name": "CEO", "role": "Chief"})
    status = org.get_organization_status()
    assert status["agent_count"] == 1

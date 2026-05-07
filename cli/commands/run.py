from agent_builder.config.loader import ConfigLoader
from agent_builder.config.validator import validate_config
from agent_builder.core.organization import Organization


def cmd_run(args):
    cfg = validate_config(ConfigLoader.load(args.config))
    org = Organization(name=cfg.organization.name, config=cfg)
    for agent in cfg.agents:
        org.create_agent(agent.model_dump())
    for dep in cfg.hierarchy.departments:
        org.create_department(dep.model_dump())
    status = org.get_organization_status()
    print(f"Organization running: {status['name']} (agents={status['agent_count']})")
    return 0

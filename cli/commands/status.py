from agent_builder.config.loader import ConfigLoader
from agent_builder.config.validator import validate_config
from agent_builder.core.organization import Organization


def cmd_status(args):
    cfg = validate_config(ConfigLoader.load(args.config))
    org = Organization(name=cfg.organization.name, config=cfg)
    for agent in cfg.agents:
        org.create_agent(agent.model_dump())
    print(org.get_organization_status())
    return 0

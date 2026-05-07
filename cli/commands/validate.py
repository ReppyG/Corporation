from agent_builder.config.loader import ConfigLoader
from agent_builder.config.validator import validate_config


def cmd_validate(args):
    cfg = ConfigLoader.load(args.config)
    validated = validate_config(cfg)
    print(f"Configuration valid for organization: {validated.organization.name}")
    return 0

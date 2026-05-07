from agent_builder.config.schema import OrgConfig


def validate_config(config_dict: dict) -> OrgConfig:
    return OrgConfig.model_validate(config_dict)

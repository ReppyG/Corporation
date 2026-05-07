from typing import List, Optional

from pydantic import BaseModel, Field


class OrganizationSettings(BaseModel):
    name: str
    description: Optional[str] = None
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    memory_storage: str = "json"
    meeting_interval_minutes: int = Field(default=30, ge=1)


class DepartmentSchema(BaseModel):
    name: str
    head_role: str
    team_size: int = Field(default=1, ge=1)
    agent_role_template: Optional[str] = None


class HierarchySchema(BaseModel):
    board: Optional[dict] = None
    departments: List[DepartmentSchema] = Field(default_factory=list)


class AgentSchema(BaseModel):
    id: str
    name: str
    role: str
    prompt_file: Optional[str] = None


class OrgConfig(BaseModel):
    organization: OrganizationSettings
    hierarchy: HierarchySchema = Field(default_factory=HierarchySchema)
    agents: List[AgentSchema] = Field(default_factory=list)

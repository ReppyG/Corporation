from datetime import datetime, UTC
from typing import Dict, List

from agent_builder.config.schema import OrgConfig
from agent_builder.core.agent import Agent
from agent_builder.core.communication import MessageBus
from agent_builder.core.logging import AuditLog
from agent_builder.core.memory import SharedMemory
from agent_builder.core.role import Role
from agent_builder.hierarchy.department import Department
from agent_builder.hierarchy.team import Team
from agent_builder.llm.anthropic import AnthropicProvider
from agent_builder.llm.gemini import GeminiProvider
from agent_builder.llm.openai import OpenAIProvider
from agent_builder.meeting.agenda import Agenda
from agent_builder.meeting.meeting import Meeting


class Organization:
    def __init__(self, name: str, config: OrgConfig):
        self.name = name
        self.config = config
        self.memory = SharedMemory(storage_type=config.organization.memory_storage)
        self.message_bus = MessageBus()
        self.audit = AuditLog(org_name=name)
        self.agents: Dict[str, Agent] = {}
        self.departments: Dict[str, Department] = {}
        self.meetings: Dict[str, dict] = {}

    def _provider(self):
        provider = self.config.organization.llm_provider.lower()
        model = self.config.organization.llm_model
        if provider == "gemini":
            return GeminiProvider(api_key="", model=model)
        if provider == "anthropic":
            return AnthropicProvider(api_key="", model=model)
        if provider == "openai":
            return OpenAIProvider(api_key="", model=model)
        raise ValueError(f"Unsupported provider: {provider}")

    def create_agent(self, agent_config: dict) -> Agent:
        role = Role(
            name=agent_config.get("role", "Contributor"),
            description=agent_config.get("role", ""),
            system_prompt=agent_config.get("system_prompt", f"You are {agent_config['name']}"),
            authority_level=agent_config.get("authority_level", 1),
        )
        agent = Agent(
            agent_id=agent_config["id"],
            name=agent_config["name"],
            role=role,
            llm_provider=self._provider(),
            memory=self.memory,
            message_bus=self.message_bus,
            audit_log=self.audit,
        )
        self.agents[agent.agent_id] = agent
        self.audit.log_action(agent.agent_id, "agent_created", agent_config)
        return agent

    def create_department(self, dept_config: dict) -> Department:
        head = dept_config["head_role"]
        dept = Department(name=dept_config["name"], head_agent_id=head, team=Team(name=dept_config["name"]))
        self.departments[dept.name] = dept
        self.audit.log_action("system", "department_created", dept_config)
        return dept

    def schedule_meeting(self, agents: List[Agent], agenda: Agenda, interval_minutes: int):
        meeting_id = f"meeting-{len(self.meetings)+1}"
        self.meetings[meeting_id] = {
            "participants": [a.agent_id for a in agents],
            "agenda": agenda,
            "interval_minutes": interval_minutes,
            "scheduled_at": datetime.now(UTC).isoformat(),
        }
        self.audit.log_action("system", "meeting_scheduled", {"meeting_id": meeting_id})
        return meeting_id

    def run_meeting(self, meeting_id: str):
        cfg = self.meetings[meeting_id]
        participants = [self.agents[a] for a in cfg["participants"] if a in self.agents]
        meeting = Meeting(meeting_id=meeting_id, agenda=cfg["agenda"], participants=participants)
        transcript = meeting.run()
        self.audit.log_meeting(transcript)
        return transcript

    def get_organization_status(self) -> dict:
        return {
            "name": self.name,
            "agent_count": len(self.agents),
            "department_count": len(self.departments),
            "meeting_count": len(self.meetings),
            "agents": list(self.agents.keys()),
            "departments": list(self.departments.keys()),
        }

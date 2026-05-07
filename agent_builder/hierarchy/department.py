from dataclasses import dataclass, field
from typing import List

from agent_builder.hierarchy.team import Team


@dataclass
class Department:
    name: str
    head_agent_id: str
    team: Team = field(default_factory=lambda: Team(name="default"))

    def assign_member(self, agent_id: str):
        self.team.add_member(agent_id)

from dataclasses import dataclass, field
from typing import List


@dataclass
class Team:
    name: str
    members: List[str] = field(default_factory=list)

    def add_member(self, agent_id: str):
        if agent_id not in self.members:
            self.members.append(agent_id)

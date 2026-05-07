from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Role:
    name: str
    description: str
    system_prompt: str
    authority_level: int
    decision_rights: List[str] = field(default_factory=list)
    reports_to: List[str] = field(default_factory=list)

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def can_make_decision(self, decision_type: str) -> bool:
        return self.authority_level >= 10 or decision_type in self.decision_rights

    def get_reporting_chain(self) -> List[str]:
        return list(self.reports_to)

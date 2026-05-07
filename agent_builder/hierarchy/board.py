from dataclasses import dataclass, field
from typing import List


@dataclass
class Board:
    name: str
    members: List[str] = field(default_factory=list)

    def quorum(self) -> int:
        return (len(self.members) // 2) + 1

from dataclasses import dataclass, field
from typing import List


@dataclass
class AgendaItem:
    title: str
    description: str = ""


@dataclass
class Agenda:
    title: str
    items: List[AgendaItem] = field(default_factory=list)

    def add_item(self, item: AgendaItem):
        self.items.append(item)

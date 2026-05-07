from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from threading import Lock
from typing import Dict, List


@dataclass
class Message:
    from_agent: str
    to_agent: str
    message: str
    timestamp: str


class MessageBus:
    def __init__(self):
        self._inboxes: Dict[str, List[Message]] = defaultdict(list)
        self._lock = Lock()

    def send_message(self, from_agent: str, to_agent: str, message: str):
        with self._lock:
            self._inboxes[to_agent].append(
                Message(from_agent=from_agent, to_agent=to_agent, message=message, timestamp=datetime.now(UTC).isoformat())
            )

    def broadcast(self, from_agent: str, to_agents: List[str], message: str):
        for to_agent in to_agents:
            self.send_message(from_agent=from_agent, to_agent=to_agent, message=message)

    def get_inbox(self, agent_id: str) -> List[Message]:
        with self._lock:
            messages = list(self._inboxes.get(agent_id, []))
            self._inboxes[agent_id] = []
        return messages

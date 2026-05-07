import json
from dataclasses import dataclass, asdict
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import List, Optional


@dataclass
class LogEntry:
    timestamp: str
    category: str
    agent_id: str
    action: str
    details: dict


class AuditLog:
    def __init__(self, org_name: str, base_dir: str = "agent_builder_data/logs"):
        self.org_name = org_name
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.base_dir / f"{org_name}.jsonl"

    def _append(self, entry: LogEntry):
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "
")

    def log_action(self, agent_id: str, action: str, details: dict):
        self._append(LogEntry(datetime.now(UTC).isoformat(), "action", agent_id, action, details))

    def log_decision(self, agent_id: str, decision: str, reasoning: str, authority_level: int):
        self._append(
            LogEntry(
                datetime.now(UTC).isoformat(),
                "decision",
                agent_id,
                decision,
                {"reasoning": reasoning, "authority_level": authority_level},
            )
        )

    def log_meeting(self, meeting_transcript):
        self._append(LogEntry(datetime.now(UTC).isoformat(), "meeting", "system", "meeting_logged", meeting_transcript.to_dict()))

    def get_history(self, agent_id: str = None, days: int = 7) -> List[LogEntry]:
        if not self.log_file.exists():
            return []
        cutoff = datetime.now(UTC) - timedelta(days=days)
        out: List[LogEntry] = []
        for line in self.log_file.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            ts = datetime.fromisoformat(row["timestamp"])
            if ts < cutoff:
                continue
            if agent_id and row["agent_id"] != agent_id:
                continue
            out.append(LogEntry(**row))
        return out

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MeetingTranscript:
    meeting_id: str
    records: List[Dict[str, Any]] = field(default_factory=list)

    def add_record(self, record: Dict[str, Any]):
        self.records.append(record)

    def to_dict(self) -> Dict[str, Any]:
        return {"meeting_id": self.meeting_id, "records": self.records}

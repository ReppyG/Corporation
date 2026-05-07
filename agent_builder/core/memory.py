import json
from pathlib import Path
from typing import Dict, List, Any


class SharedMemory:
    def __init__(self, storage_type: str = "json", data_dir: str = "agent_builder_data/memory"):
        if storage_type != "json":
            raise ValueError("Only json storage_type is currently supported")
        self.storage_type = storage_type
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_dir / "shared_memory.json"
        if not self.db_file.exists():
            self.db_file.write_text("{}", encoding="utf-8")

    def _read(self) -> Dict[str, Any]:
        return json.loads(self.db_file.read_text(encoding="utf-8"))

    def _write(self, data: Dict[str, Any]):
        self.db_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def save(self, key: str, value: dict):
        data = self._read()
        data[key] = value
        self._write(data)

    def load(self, key: str) -> dict:
        return self._read().get(key, {})

    def search(self, query: str) -> List[dict]:
        query_l = query.lower()
        matches: List[dict] = []
        for k, v in self._read().items():
            blob = json.dumps({"key": k, "value": v}).lower()
            if query_l in blob:
                matches.append({"key": k, "value": v})
        return matches

    def get_agent_context(self, agent_id: str, limit: int = 10) -> dict:
        all_items = self.search(agent_id)
        return {"agent_id": agent_id, "matches": all_items[:limit]}

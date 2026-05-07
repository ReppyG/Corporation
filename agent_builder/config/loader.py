import json
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigLoader:
    @staticmethod
    def load(path: str) -> Dict[str, Any]:
        file = Path(path)
        if not file.exists():
            raise FileNotFoundError(path)
        text = file.read_text(encoding="utf-8")
        if file.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(text) or {}
        if file.suffix == ".json":
            return json.loads(text)
        raise ValueError("Unsupported config format; use YAML or JSON")

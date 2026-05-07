from pathlib import Path


class FileSystemTool:
    def execute(self, operation: str = "read", path: str = "", content: str = ""):
        target = Path(path)
        if operation == "read":
            return target.read_text(encoding="utf-8")
        if operation == "write":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {"status": "written", "path": str(target)}
        if operation == "exists":
            return target.exists()
        raise ValueError(f"Unsupported operation: {operation}")

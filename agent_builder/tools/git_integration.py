import subprocess
from pathlib import Path


class GitIntegrationTool:
    def execute(self, repo_path: str, args: list[str]):
        repo = Path(repo_path)
        cmd = ["git", "--no-pager", *args]
        result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False)
        return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

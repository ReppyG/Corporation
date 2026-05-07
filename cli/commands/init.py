import shutil
from pathlib import Path


def cmd_init(args):
    src = Path(args.template)
    dst = Path.cwd() / "new-organization"
    if dst.exists():
        raise SystemExit(f"Destination already exists: {dst}")
    shutil.copytree(src, dst)
    print(f"Initialized organization at {dst}")
    return 0

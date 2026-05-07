from pathlib import Path


def cmd_logs(args):
    log_file = Path("agent_builder_data/logs") / f"{args.org}.jsonl"
    if not log_file.exists():
        print("No logs found")
        return 0
    lines = log_file.read_text(encoding="utf-8").splitlines()
    if args.agent:
        lines = [ln for ln in lines if f'"agent_id": "{args.agent}"' in ln]
    for line in lines[-args.tail:]:
        print(line)
    return 0

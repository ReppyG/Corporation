import argparse
import json

from cli.commands.init import cmd_init
from cli.commands.logs import cmd_logs
from cli.commands.migrate import cmd_migrate
from cli.commands.run import cmd_run
from cli.commands.status import cmd_status
from cli.commands.validate import cmd_validate
from cli.prompts.generate import cmd_generate_prompts


def build_parser():
    parser = argparse.ArgumentParser(prog="agent-builder")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--template", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--config", required=True)

    p_run = sub.add_parser("run")
    p_run.add_argument("--config", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--config", required=True)

    p_logs = sub.add_parser("logs")
    p_logs.add_argument("--org", required=True)
    p_logs.add_argument("--agent", required=False)
    p_logs.add_argument("--tail", type=int, default=50)

    p_migrate = sub.add_parser("migrate")
    p_migrate.add_argument("--from-version", required=True)
    p_migrate.add_argument("--to-version", required=True)

    p_gen = sub.add_parser("generate-prompts")
    p_gen.add_argument("--template", required=True)
    p_gen.add_argument("--count", type=int, required=True)
    p_gen.add_argument("--output", required=True)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    cmd = args.command
    if cmd == "init":
        return cmd_init(args)
    if cmd == "validate":
        return cmd_validate(args)
    if cmd == "run":
        return cmd_run(args)
    if cmd == "status":
        return cmd_status(args)
    if cmd == "logs":
        return cmd_logs(args)
    if cmd == "migrate":
        return cmd_migrate(args)
    if cmd == "generate-prompts":
        return cmd_generate_prompts(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

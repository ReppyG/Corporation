from pathlib import Path


def cmd_generate_prompts(args):
    template = Path(args.template).read_text(encoding="utf-8")
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(1, args.count + 1):
        rendered = template.replace("{{INDEX}}", str(idx)).replace("{{NAME}}", f"Agent-{idx}")
        (out_dir / f"agent_{idx}.md").write_text(rendered, encoding="utf-8")
    print(f"Generated {args.count} prompts in {out_dir}")
    return 0

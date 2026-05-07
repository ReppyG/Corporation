# agent-builder

A reusable Python framework for building autonomous hierarchical multi-agent organizations.

## Features

- Generic framework for any organization model
- Hierarchies (board, departments, teams)
- Shared memory, messaging, structured meetings, voting
- Multi-provider LLM interface (Gemini, Anthropic, OpenAI)
- CLI for init/validate/run/status/logs/migrate/prompt generation
- Nexus example organization included
- Docker + Kubernetes deployment manifests

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
agent-builder validate --config examples/nexus_corporation/config.yaml
agent-builder run --config examples/nexus_corporation/config.yaml
```

See `CONFIG.md`, `EXAMPLES.md`, and `docs/` for full details.

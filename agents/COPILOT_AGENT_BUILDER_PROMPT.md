# AI Agent Builder Framework - GitHub Copilot Prompt

## Overview

Build a **reusable, production-ready Python framework** for creating autonomous multi-agent systems. This framework should be generic enough to build ANY hierarchical AI organization (not just Nexus), but include templates and examples for the Nexus project.

The framework will be deployed on Oracle Cloud and managed through OpenClaw.

---

## Project Name

`agent-builder` (A framework for building autonomous agent organizations)

---

## Repository Structure

```
agent-builder/
├── README.md
├── LICENSE (MIT)
├── requirements.txt
├── setup.py
├── .gitignore
├── .env.example
├── CONFIG.md
├── EXAMPLES.md
│
├── agent_builder/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py           # Base Agent class
│   │   ├── organization.py    # Organization/Corporation class
│   │   ├── role.py            # Role/Persona definitions
│   │   ├── memory.py          # Shared memory system
│   │   ├── communication.py   # Inter-agent messaging
│   │   └── logging.py         # Audit trail & logs
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── provider.py        # Base LLM provider interface
│   │   ├── gemini.py          # Google Gemini implementation
│   │   ├── anthropic.py       # Claude implementation
│   │   └── openai.py          # OpenAI implementation
│   │
│   ├── hierarchy/
│   │   ├── __init__.py
│   │   ├── board.py           # Board of Directors pattern
│   │   ├── department.py      # Department/Division pattern
│   │   ├── team.py            # Team pattern
│   │   └── reporting.py       # Reporting chains
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py      # Web research capability
│   │   ├── file_system.py     # File creation/editing
│   │   ├── code_execution.py  # Run Python code
│   │   ├── git_integration.py # Git operations
│   │   └── notifications.py   # Alerts & messages
│   │
│   ├── meeting/
│   │   ├── __init__.py
│   │   ├─��� meeting.py         # Meeting coordinator
│   │   ├── agenda.py          # Meeting agenda
│   │   ├── voting.py          # Voting/decision system
│   │   └── transcript.py      # Meeting records
│   │
│   └── config/
│       ├── __init__.py
│       ├── loader.py          # Load config from YAML/JSON
│       ├── validator.py       # Validate org structure
│       └── schema.py          # Config schemas
│
├── examples/
│   ├── nexus_corporation/
│   │   ├── config.yaml        # Nexus org structure
│   │   ├── agents.yaml        # All 33 agent definitions
│   │   ├── charter.md         # Nexus governance charter
│   │   └── prompts/
│   │       ├── ceo.md
│   │       ├── engineering_head.md
│   │       ├── coder.md
│   │       ├── qa_head.md
│   │       ├── reviewer.md
│   │       ├── test_head.md
│   │       ├── game_breaker.md
│   │       └── shareholder.md
│   │
│   ├── simple_startup/        # (Optional) Simpler example
│   │   ├── config.yaml
│   │   └── agents.yaml
│   │
│   └── research_lab/          # (Optional) Another example
│       ├── config.yaml
│       └── agents.yaml
│
├── templates/
│   ├── agent_prompt_template.md
│   ├── config_template.yaml
│   ├── organization_template.yaml
│   └── role_template.yaml
│
├── docs/
│   ├── getting_started.md
│   ├── architecture.md
│   ├── creating_agents.md
│   ├── building_hierarchies.md
│   ├── memory_system.md
│   ├── llm_providers.md
│   ├── tools_and_capabilities.md
│   └── deployment.md
│
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_organization.py
│   ├── test_memory.py
│   ├── test_communication.py
│   └── test_hierarchy.py
│
└── cli/
    ├── __init__.py
    ├── main.py               # CLI entry point
    ├── commands/
    │   ├── init.py          # Initialize new org
    │   ├── validate.py      # Validate config
    │   ├── run.py           # Start organization
    │   ├── status.py        # Check status
    │   ├── logs.py          # View logs
    │   └── migrate.py       # Migrate between versions
    └── prompts/
        └── generate.py      # Generate agent prompts from templates
```

---

## Core Modules

### 1. `agent.py` - Base Agent Class

```python
class Agent:
    def __init__(self, agent_id: str, name: str, role: Role, llm_provider):
        """Initialize an autonomous agent"""
        pass
    
    def think(self, prompt: str, use_memory: bool = True, use_web: bool = False) -> str:
        """Agent thinks and responds"""
        pass
    
    def receive_message(self, from_agent: str, message: str):
        """Receive message from another agent"""
        pass
    
    def execute_tool(self, tool_name: str, **kwargs):
        """Execute a capability (file write, web search, etc)"""
        pass
    
    def log_action(self, action: str, details: dict):
        """Log all actions for audit trail"""
        pass
```

### 2. `organization.py` - Corporation/Organization Management

```python
class Organization:
    def __init__(self, name: str, config: OrgConfig):
        """Initialize organization"""
        pass
    
    def create_agent(self, agent_config: dict) -> Agent:
        """Create and register a new agent"""
        pass
    
    def create_department(self, dept_config: dict) -> Department:
        """Create a department with a head and team"""
        pass
    
    def schedule_meeting(self, agents: List[Agent], agenda: Agenda, interval_minutes: int):
        """Schedule recurring meetings"""
        pass
    
    def run_meeting(self, meeting_id: str):
        """Execute a meeting between agents"""
        pass
    
    def get_organization_status(self) -> dict:
        """Return full org status for reporting"""
        pass
```

### 3. `role.py` - Agent Personas

```python
class Role:
    def __init__(self, name: str, description: str, system_prompt: str, authority_level: int):
        """Define an agent's role and responsibilities"""
        pass
    
    def get_system_prompt(self) -> str:
        """Return the role's system prompt"""
        pass
    
    def can_make_decision(self, decision_type: str) -> bool:
        """Check if this role has authority for a decision"""
        pass
    
    def get_reporting_chain(self) -> List[str]:
        """Get who this role reports to"""
        pass
```

### 4. `memory.py` - Shared Memory & Context

```python
class SharedMemory:
    def __init__(self, storage_type: str = "json"):
        """Initialize shared memory system"""
        pass
    
    def save(self, key: str, value: dict):
        """Save data accessible to all agents"""
        pass
    
    def load(self, key: str) -> dict:
        """Load data"""
        pass
    
    def search(self, query: str) -> List[dict]:
        """Semantic search across memory"""
        pass
    
    def get_agent_context(self, agent_id: str, limit: int = 10) -> dict:
        """Get agent-specific context for their next thinking"""
        pass
```

### 5. `communication.py` - Inter-Agent Messaging

```python
class MessageBus:
    def __init__(self):
        """Initialize message routing system"""
        pass
    
    def send_message(self, from_agent: str, to_agent: str, message: str):
        """Send message between agents"""
        pass
    
    def broadcast(self, from_agent: str, to_agents: List[str], message: str):
        """Send message to multiple agents"""
        pass
    
    def get_inbox(self, agent_id: str) -> List[Message]:
        """Get messages waiting for agent"""
        pass
```

### 6. `meeting.py` - Structured Meetings

```python
class Meeting:
    def __init__(self, meeting_id: str, agenda: Agenda, participants: List[Agent]):
        """Initialize meeting"""
        pass
    
    def add_agenda_item(self, item: AgendaItem):
        """Add item to meeting"""
        pass
    
    def run(self) -> MeetingTranscript:
        """Execute meeting and return transcript"""
        pass
    
    def vote(self, question: str, options: List[str]) -> VotingResult:
        """Conduct a vote"""
        pass
```

### 7. `logging.py` - Audit Trail

```python
class AuditLog:
    def __init__(self, org_name: str):
        """Initialize audit logging"""
        pass
    
    def log_action(self, agent_id: str, action: str, details: dict):
        """Log an action"""
        pass
    
    def log_decision(self, agent_id: str, decision: str, reasoning: str, authority_level: int):
        """Log a decision"""
        pass
    
    def log_meeting(self, meeting_transcript: MeetingTranscript):
        """Log a meeting"""
        pass
    
    def get_history(self, agent_id: str = None, days: int = 7) -> List[LogEntry]:
        """Retrieve history"""
        pass
```

---

## LLM Provider Interface

All LLM implementations follow this interface:

```python
class LLMProvider:
    def __init__(self, api_key: str, model: str):
        pass
    
    def generate(self, prompt: str, system_prompt: str, temperature: float = 0.7) -> str:
        """Generate response"""
        pass
    
    def generate_with_context(self, prompt: str, system_prompt: str, context: List[dict]) -> str:
        """Generate with conversation history"""
        pass
    
    def validate_key(self) -> bool:
        """Verify API key is valid"""
        pass
```

---

## Configuration Format (YAML)

Organizations are defined in YAML for easy customization:

```yaml
# organization.yaml
organization:
  name: "Nexus Corporation"
  description: "AI-driven development company building Nexus"
  llm_provider: "gemini"
  llm_model: "gemini-2.5-flash"
  memory_storage: "json"
  meeting_interval_minutes: 30
  
hierarchy:
  board:
    name: "Board of Directors"
    size: 10
    role_template: "templates/shareholder.md"
  
  departments:
    - name: "Engineering"
      head_role: "Engineering-Head"
      team_size: 10
      agent_role_template: "templates/coder.md"
    
    - name: "Quality Assurance"
      head_role: "QA-Head"
      team_size: 10
      agent_role_template: "templates/reviewer.md"
    
    - name: "Testing"
      head_role: "Testing-Head"
      team_size: 10
      agent_role_template: "templates/game_breaker.md"

agents:
  - id: "ceo"
    name: "CEO"
    role: "Chief Executive Officer"
    prompt_file: "examples/nexus_corporation/prompts/ceo.md"
```

---

## CLI Commands

```bash
# Initialize a new organization
agent-builder init --template examples/nexus_corporation

# Validate configuration
agent-builder validate --config organization.yaml

# Start the organization (runs meetings, agents, etc)
agent-builder run --config organization.yaml

# Check status
agent-builder status --config organization.yaml

# View logs
agent-builder logs --org nexus --agent ceo --tail 50

# Generate agent prompts from templates
agent-builder generate-prompts --template templates/coder.md --count 10 --output prompts/
```

---

## Key Features

✅ **Generic Framework** - Not tied to any specific project
✅ **Multiple LLM Providers** - Gemini, Claude, OpenAI, etc.
✅ **Hierarchical Organizations** - Board, Departments, Teams
✅ **Inter-Agent Communication** - Message passing, broadcasts
✅ **Shared Memory** - Context accessible to all agents
✅ **Structured Meetings** - Recurring meetings with agendas and voting
✅ **Audit Trails** - Complete history of all decisions
✅ **Tool Capabilities** - Web search, file operations, code execution
✅ **YAML Configuration** - Easy to customize without coding
✅ **Multiple Examples** - Nexus + other sample orgs
✅ **Full Documentation** - Getting started, architecture, deployment
✅ **CLI Tools** - Initialize, validate, run, monitor
✅ **Production Ready** - Error handling, logging, resource limits

---

## Requirements

```
google-generativeai>=0.3.0
anthropic>=0.7.0
openai>=1.0.0
pyyaml>=6.0
pydantic>=2.0
requests>=2.31.0
beautifulsoup4>=4.12.0
duckduckgo-search>=3.9.0
gitpython>=3.1.0
pytest>=7.4.0
python-dotenv>=1.0.0
```

---

## Deployment

This framework is designed to run on:
- ✅ Local development machine
- ✅ Docker containers
- ✅ Oracle Cloud free tier (1GB RAM optimized)
- ✅ Kubernetes clusters
- ✅ GitHub Codespaces

Include Docker configuration and Kubernetes manifests in the repo.

---

## Documentation Files to Create

1. **README.md** - Overview, quick start, examples
2. **EXAMPLES.md** - Detailed examples for different org types
3. **CONFIG.md** - Configuration reference
4. **docs/getting_started.md** - Step-by-step tutorial
5. **docs/architecture.md** - System design
6. **docs/creating_agents.md** - How to create custom agents
7. **docs/building_hierarchies.md** - Org structure patterns
8. **docs/deployment.md** - Deploy to Oracle,

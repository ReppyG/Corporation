from typing import Dict, Optional

from agent_builder.core.communication import MessageBus
from agent_builder.core.logging import AuditLog
from agent_builder.core.memory import SharedMemory
from agent_builder.core.role import Role
from agent_builder.tools.file_system import FileSystemTool
from agent_builder.tools.web_search import WebSearchTool


class Agent:
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: Role,
        llm_provider,
        memory: Optional[SharedMemory] = None,
        message_bus: Optional[MessageBus] = None,
        audit_log: Optional[AuditLog] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.llm_provider = llm_provider
        self.memory = memory or SharedMemory()
        self.message_bus = message_bus or MessageBus()
        self.audit_log = audit_log
        self.tools = {
            "web_search": WebSearchTool(),
            "file_system": FileSystemTool(),
        }

    def think(self, prompt: str, use_memory: bool = True, use_web: bool = False) -> str:
        context_items = []
        if use_memory:
            context_items = self.memory.get_agent_context(self.agent_id, limit=10).get("matches", [])
        if use_web:
            web_result = self.execute_tool("web_search", query=prompt, limit=3)
            context_items.append({"role": "user", "content": f"[web search result]: {web_result}"})

        # Build messages list: system role first, then context, then the new prompt
        system_prompt = self.role.get_system_prompt()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for item in context_items:
            if isinstance(item, dict) and "role" in item:
                messages.append(item)
            elif isinstance(item, dict):
                messages.append({"role": "user", "content": str(item)})
        messages.append({"role": "user", "content": prompt})

        result = self.llm_provider.generate_with_context(messages)
        self.log_action("think", {"prompt": prompt, "used_memory": use_memory, "used_web": use_web})
        return result

    def receive_message(self, from_agent: str, message: str):
        self.message_bus.send_message(from_agent=from_agent, to_agent=self.agent_id, message=message)
        self.log_action("receive_message", {"from_agent": from_agent, "message": message})

    def execute_tool(self, tool_name: str, **kwargs):
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        result = self.tools[tool_name].execute(**kwargs)
        self.log_action("execute_tool", {"tool_name": tool_name, "kwargs": kwargs})
        return result

    def log_action(self, action: str, details: dict):
        if self.audit_log:
            self.audit_log.log_action(self.agent_id, action, details)

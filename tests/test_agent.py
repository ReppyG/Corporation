from agent_builder.core.agent import Agent
from agent_builder.core.role import Role
from agent_builder.llm.gemini import GeminiProvider


def test_agent_think_returns_text():
    role = Role(name="tester", description="", system_prompt="You are tester", authority_level=1)
    agent = Agent(agent_id="a1", name="A1", role=role, llm_provider=GeminiProvider(api_key="k", model="m"))
    result = agent.think("hello")
    assert "hello" in result

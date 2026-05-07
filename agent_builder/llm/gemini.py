from typing import List

from agent_builder.llm.provider import LLMProvider


class GeminiProvider(LLMProvider):
    def generate(self, prompt: str, system_prompt: str, temperature: float = 0.7) -> str:
        return f"[gemini:{self.model}] {system_prompt[:80]} :: {prompt}"

    def generate_with_context(self, prompt: str, system_prompt: str, context: List[dict]) -> str:
        return self.generate(prompt=f"Context items={len(context)} | {prompt}", system_prompt=system_prompt)

    def validate_key(self) -> bool:
        return bool(self.api_key)

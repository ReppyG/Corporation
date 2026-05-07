from abc import ABC, abstractmethod
from typing import List


class LLMProvider(ABC):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str, temperature: float = 0.7) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_with_context(self, prompt: str, system_prompt: str, context: List[dict]) -> str:
        raise NotImplementedError

    @abstractmethod
    def validate_key(self) -> bool:
        raise NotImplementedError

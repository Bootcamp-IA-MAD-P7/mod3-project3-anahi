from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model_name: str


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int) -> LLMResponse:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass

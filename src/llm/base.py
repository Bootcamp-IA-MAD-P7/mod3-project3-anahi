from abc import ABC, abstractmethod
from dataclasses import dataclass

from langchain_core.messages import BaseMessage


@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model_name: str


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(
        self, prompt: list[BaseMessage], user_id: str, bypass_limits: bool = False
    ) -> LLMResponse:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass

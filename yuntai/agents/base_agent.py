"""基础 Agent 类"""
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, model: BaseChatModel | None = None) -> None:
        self.model = model

    @abstractmethod
    def invoke(self, input_data: dict[str, object]) -> dict[str, object]:
        """执行 Agent"""
        pass

    def set_model(self, model: BaseChatModel) -> None:
        """设置模型"""
        self.model = model

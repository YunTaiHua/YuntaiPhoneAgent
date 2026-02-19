"""
基础 Agent 类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from langchain_core.language_models import BaseChatModel


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, model: Optional[BaseChatModel] = None):
        self.model = model
    
    @abstractmethod
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent"""
        pass
    
    def set_model(self, model: BaseChatModel):
        """设置模型"""
        self.model = model

"""
基础 Agent 类
=============

本模块定义了所有 Agent 的抽象基类，规定了 Agent 必须实现的基本接口。

类说明：
    - BaseAgent: Agent 抽象基类，定义了 invoke 和 set_model 等基本方法

使用示例：
    >>> from yuntai.agents import BaseAgent
    >>> 
    >>> class MyAgent(BaseAgent):
    ...     def invoke(self, input_data: dict) -> dict:
    ...         return {"result": "success"}

设计模式：
    - 使用抽象基类模式（ABC），强制子类实现 invoke 方法
    - 支持依赖注入，允许外部设置模型实例
"""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseChatModel


class BaseAgent(ABC):
    """
    Agent 基类
    
    所有 Agent 的抽象基类，定义了 Agent 必须实现的基本接口。
    使用抽象基类模式确保子类实现核心方法。
    
    Attributes:
        model: LangChain 聊天模型实例，用于调用 LLM
    
    使用示例：
        >>> class MyAgent(BaseAgent):
        ...     def invoke(self, input_data: dict) -> dict:
        ...         response = self.model.invoke(input_data["messages"])
        ...         return {"result": response.content}
    """
    
    def __init__(self, model: BaseChatModel | None = None) -> None:
        """
        初始化 Agent 基类
        
        Args:
            model: LangChain 聊天模型实例，可选参数
                   如果不传入，需要在后续通过 set_model 方法设置
        """
        # 存储模型实例，用于后续调用
        self.model = model

    @abstractmethod
    def invoke(self, input_data: dict[str, object]) -> dict[str, object]:
        """
        执行 Agent 的核心方法（抽象方法）
        
        这是 Agent 的主要入口点，子类必须实现此方法。
        方法接收输入数据，处理后返回结果。
        
        Args:
            input_data: 输入数据字典，包含执行所需的所有参数
                       具体内容由子类定义
        
        Returns:
            执行结果字典，包含处理后的输出数据
            具体内容由子类定义
        
        Raises:
            NotImplementedError: 如果子类未实现此方法
        
        使用示例：
            >>> result = agent.invoke({"query": "你好"})
            >>> print(result["response"])
        """
        pass

    def set_model(self, model: BaseChatModel) -> None:
        """
        设置模型实例
        
        允许在 Agent 创建后动态设置或更换模型。
        这在需要使用不同模型配置时非常有用。
        
        Args:
            model: LangChain 聊天模型实例
        
        使用示例：
            >>> from yuntai.models import get_chat_model
            >>> agent.set_model(get_chat_model())
        """
        # 更新模型实例
        self.model = model

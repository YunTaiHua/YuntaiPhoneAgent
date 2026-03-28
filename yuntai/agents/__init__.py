"""
Agent 模块
==========

本模块提供智能代理（Agent）的核心实现，用于处理各类任务。

模块包含以下 Agent 类：
    - BaseAgent: Agent 基类，定义了所有 Agent 的基本接口
    - JudgementAgent: 任务判断 Agent，用于分析用户意图和任务类型
    - ChatAgent: 聊天 Agent，用于自由对话和智能回复
    - PhoneAgent: 手机操作 Agent，用于执行手机自动化任务

使用示例：
    >>> from yuntai.agents import ChatAgent, JudgementAgent
    >>> 
    >>> # 创建聊天 Agent
    >>> chat_agent = ChatAgent()
    >>> reply = chat_agent.chat("你好")
    >>> 
    >>> # 创建判断 Agent
    >>> judge_agent = JudgementAgent()
    >>> result = judge_agent.judge("打开微信发消息给张三")
"""

from .base_agent import BaseAgent
from .judgement_agent import JudgementAgent
from .chat_agent import ChatAgent
from .phone_agent import PhoneAgent

# 模块公开接口
__all__ = [
    "BaseAgent",
    "JudgementAgent",
    "ChatAgent",
    "PhoneAgent",
]

"""
记忆管理模块
============

本模块提供对话记忆管理功能，支持 LangChain 记忆机制。

主要组件:
    - ConversationMemoryManager: 对话记忆管理器
    - FreeChatMemory: 自由聊天记忆
    - ChatSessionMemory: 聊天会话记忆

功能特点:
    - 支持 LangChain Callbacks 自动记录对话历史
    - 支持永久记忆存储
    - 支持历史上下文检索
"""
import logging

logger = logging.getLogger(__name__)

from .conversation_memory import ConversationMemoryManager

__all__ = ["ConversationMemoryManager"]

"""
聊天工具模块
============

提供时间信息和历史上下文相关的工具函数。

主要功能:
    - get_current_time_info: 获取当前时间信息
    - get_history_context: 获取历史对话上下文
    - build_chat_system_prompt: 构建聊天系统提示词

使用示例:
    >>> from yuntai.tools import get_current_time_info, get_history_context
    >>> time_info = get_current_time_info()
    >>> context = get_history_context(file_manager, "QQ", "张三")
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from yuntai.tools.time_tool import TimeTool
from yuntai.prompts import (
    CHAT_BUILD_SYSTEM_PROMPT_BASE,
    CHAT_TIME_INSTRUCTION,
    CHAT_FINAL_INSTRUCTION,
)

if TYPE_CHECKING:
    from yuntai.services.file_manager import FileManager

logger = logging.getLogger(__name__)


def get_current_time_info() -> str:
    """
    获取当前时间信息
    
    返回格式化的当前时间信息字符串。
    
    Returns:
        时间信息字符串
    """
    return TimeTool.get_time_info()


def get_history_context(
    file_manager: FileManager,
    target_app: str | None = None,
    target_object: str | None = None,
    limit: int = 5
) -> str:
    """
    获取历史对话上下文
    
    从文件管理器中获取最近的聊天记录和永久记忆，
    构建格式化的历史上下文字符串。
    
    Args:
        file_manager: 文件管理器实例
        target_app: 目标 APP，可选
        target_object: 聊天对象，可选
        limit: 最大历史记录数
    
    Returns:
        格式化的历史上下文字符串
    """
    context_parts = []
    
    if target_app and target_object:
        chat_history = file_manager.get_recent_conversation_history(
            target_app, target_object, limit=limit
        )
        if chat_history:
            context_parts.append("\n=== 最近聊天记录 ===")
            for i, chat in enumerate(chat_history):
                context_parts.append(f"{i + 1}. {chat.get('content', '')[:100]}...")
    
    free_chat_history = file_manager.get_recent_free_chats(limit=limit)
    if free_chat_history:
        context_parts.append("\n=== 最近自由对话 ===")
        for i, chat in enumerate(free_chat_history):
            user_input = chat.get('user_input', '')
            assistant_reply = chat.get('assistant_reply', '')
            context_parts.append(f"{i + 1}. 用户: {user_input[:50]}...")
            context_parts.append(f"   助手: {assistant_reply[:50]}...")
    
    forever_memory = file_manager.read_forever_memory()
    if forever_memory:
        context_parts.append(f"\n=== 永久记忆 ===\n{forever_memory}")
    
    logger.debug(f"获取历史上下文: {len(context_parts)} 部分")
    return "\n".join(context_parts)


def build_chat_system_prompt(
    include_time: bool = True,
    include_memory: bool = True,
    file_manager: FileManager | None = None,
    forever_memory_content: str = ""
) -> str:
    """
    构建聊天系统提示词
    
    根据参数动态构建包含时间信息和记忆的系统提示词。
    
    Args:
        include_time: 是否包含时间信息
        include_memory: 是否包含记忆
        file_manager: 文件管理器实例
        forever_memory_content: 永久记忆内容
    
    Returns:
        构建好的系统提示词
    """
    prompt_parts = [CHAT_BUILD_SYSTEM_PROMPT_BASE]
    
    if include_time:
        time_info = get_current_time_info()
        prompt_parts.append(f"\n{time_info}")
        prompt_parts.append(CHAT_TIME_INSTRUCTION)
    
    if include_memory and forever_memory_content:
        prompt_parts.append(f"\n=== 永久记忆 ===\n{forever_memory_content}")
    
    prompt_parts.append(CHAT_FINAL_INSTRUCTION)
    
    logger.debug("构建聊天系统提示词完成")
    return "\n".join(prompt_parts)

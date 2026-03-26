"""
聊天工具模块
提供时间信息和历史上下文
"""
import datetime
import time

from yuntai.tools.time_tool import TimeTool
from yuntai.prompts import (
    CHAT_BUILD_SYSTEM_PROMPT_BASE,
    CHAT_TIME_INSTRUCTION,
    CHAT_FINAL_INSTRUCTION,
)


def get_current_time_info() -> str:
    """获取当前时间信息"""
    return TimeTool.get_time_info()


def get_history_context(
    file_manager,
    target_app: str | None = None,
    target_object: str | None = None,
    limit: int = 5
) -> str:
    """
    获取历史对话上下文
    
    Args:
        file_manager: 文件管理器实例
        target_app: 目标 APP
        target_object: 聊天对象
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
    
    return "\n".join(context_parts)


def build_chat_system_prompt(
    include_time: bool = True,
    include_memory: bool = True,
    file_manager = None,
    forever_memory_content: str = ""
) -> str:
    """
    构建聊天系统提示词
    
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
    
    return "\n".join(prompt_parts)

"""
聊天工具模块
提供时间信息和历史上下文
"""
import datetime
import time
from typing import List, Dict, Any, Optional

from yuntai.tools.time_tool import TimeTool


def get_current_time_info() -> str:
    """获取当前时间信息"""
    return TimeTool.get_time_info()


def get_history_context(
    file_manager,
    target_app: Optional[str] = None,
    target_object: Optional[str] = None,
    limit: int = 5
) -> str:
    """获取历史对话上下文"""
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
    file_manager=None,
    forever_memory_content: str = ""
) -> str:
    """构建聊天系统提示词"""
    prompt_parts = [
        """你是一个友好的助手，名字叫'小芸'（不用刻意用"小芸："放在对话开头做标注），性别为女，请用自然又俏皮可爱的方式回应用户。

你有记忆功能，可以记住之前的对话内容。"""
    ]
    
    if include_time:
        time_info = get_current_time_info()
        prompt_parts.append(f"\n{time_info}")
        prompt_parts.append("""
**重要**：
- 如果用户询问时间，请使用上述当前时间信息回答
- 不要编造时间，要准确使用提供的时间信息
- 回答时可以自然地提及时间，如"现在的时间是14:30"或"今天是2026年1月31日"
- 如果用户询问具体时间，请直接返回准确时间，不要添加不必要的对话内容
- 如果用户未提及时间相关问题不要强行将时间添加到对话中""")
    
    if include_memory and forever_memory_content:
        prompt_parts.append(f"\n=== 永久记忆 ===\n{forever_memory_content}")
    
    prompt_parts.append("\n请基于以上信息和用户当前的问题，生成一个连贯、友好的回复。")
    
    return "\n".join(prompt_parts)

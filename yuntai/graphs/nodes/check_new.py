"""
检查新消息节点

负责检测是否有新的对方消息，基于已读消息列表进行判断。
"""

from __future__ import annotations

from yuntai.graphs.state import ReplyState
from yuntai.tools import is_similar


def check_new_message(state: ReplyState) -> dict[str, bool | str | list[str]]:
    """
    检查是否有新消息节点
    
    根据已读消息列表判断是否有新的对方消息。
    
    输入: current_other_messages, seen_other_messages
    输出: is_new_message, latest_message, seen_other_messages
    
    Args:
        state: 回复状态字典
    
    Returns:
        包含新消息检测结果的字典
    """
    other_messages = state["current_other_messages"]
    seen_messages = state.get("seen_other_messages", [])
    
    if not other_messages:
        print("⏭️ 没有对方消息")
        return {
            "is_new_message": False,
            "latest_message": "",
        }
    
    truly_new: list[str] = []
    for msg in other_messages:
        is_seen = any(is_similar(msg, seen, 0.7) for seen in seen_messages)
        if not is_seen:
            truly_new.append(msg)
    
    is_new = len(truly_new) > 0
    latest_new = truly_new[-1] if truly_new else ""
    
    updated_seen = seen_messages + other_messages
    
    if is_new:
        print(f"💬 发现新消息: {latest_new[:50]}...")
    else:
        print("⏭️ 没有新消息")
    
    return {
        "is_new_message": is_new,
        "latest_message": latest_new,
        "seen_other_messages": updated_seen,
    }

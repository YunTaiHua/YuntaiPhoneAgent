"""
消息归属判断节点

负责判断消息的归属（对方消息或我方消息），基于已知消息和界面特征进行判断。
"""

from __future__ import annotations

from yuntai.graphs.state import ReplyState
from yuntai.tools import is_similar, DEFAULT_SIMILARITY_THRESHOLD
from yuntai.core.config import SIMILARITY_THRESHOLD


def determine_ownership(state: ReplyState) -> dict[str, list[str]]:
    """
    判断消息归属节点
    
    根据已知消息列表和消息界面特征判断消息归属。
    
    输入: parsed_messages, other_messages, my_messages
    输出: current_other_messages, current_my_messages
    
    Args:
        state: 回复状态字典
    
    Returns:
        包含归属判断结果的字典
    """
    messages = state["parsed_messages"]
    known_other = state["other_messages"]
    known_my = state["my_messages"]
    
    if not messages:
        return {
            "current_other_messages": [],
            "current_my_messages": [],
        }
    
    other_messages: list[str] = []
    my_messages: list[str] = []
    
    for msg in messages:
        content = msg.get("content", "").strip()
        position = msg.get("position", "")
        color = msg.get("color", "")
        
        if len(content) < 2:
            continue
        
        is_my_message = any(
            is_similar(content, m, SIMILARITY_THRESHOLD) 
            for m in known_my
        )
        if is_my_message:
            my_messages.append(content)
            continue
        
        is_other_message = any(
            is_similar(content, m, SIMILARITY_THRESHOLD)
            for m in known_other
        )
        if is_other_message:
            other_messages.append(content)
            continue
        
        if position == "左侧有头像":
            other_messages.append(content)
        elif position == "右侧有头像":
            my_messages.append(content)
        else:
            if color == "白色":
                other_messages.append(content)
            elif color in ["红色", "粉色", "蓝色", "绿色", "紫色", "黑色", "灰色", "橙色", "黄色"]:
                my_messages.append(content)
    
    print(f"📋 对方消息 {len(other_messages)} 条，我方消息 {len(my_messages)} 条")
    
    return {
        "current_other_messages": other_messages,
        "current_my_messages": my_messages,
    }

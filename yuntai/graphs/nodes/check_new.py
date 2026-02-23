"""
检查新消息节点
"""
from difflib import SequenceMatcher

from yuntai.graphs.state import ReplyState


def check_new_message(state: ReplyState) -> dict:
    """
    检查是否有新消息节点
    
    输入: current_other_messages, seen_other_messages
    输出: is_new_message, latest_message, seen_other_messages
    """
    other_messages = state["current_other_messages"]
    seen_messages = state.get("seen_other_messages", [])
    
    if not other_messages:
        print("⏭️ 没有对方消息")
        return {
            "is_new_message": False,
            "latest_message": "",
        }
    
    truly_new = []
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


def is_similar(msg1: str, msg2: str, threshold: float) -> bool:
    if not msg1 or not msg2:
        return False
    
    import re
    def clean(text):
        return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower()
    
    c1, c2 = clean(msg1), clean(msg2)
    if not c1 or not c2:
        return msg1 == msg2
    
    if c1 == c2 or c1 in c2 or c2 in c1:
        return True
    
    return SequenceMatcher(None, c1, c2).ratio() >= threshold

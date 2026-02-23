"""
检查新消息节点
"""
from difflib import SequenceMatcher

from yuntai.graphs.state import ReplyState


def check_new_message(state: ReplyState) -> dict:
    """
    检查是否有新消息节点
    
    输入: current_other_messages, previous_latest_message, last_sent_reply
    输出: is_new_message, latest_message
    """
    other_messages = state["current_other_messages"]
    previous_latest = state["previous_latest_message"]
    last_sent_reply = state["last_sent_reply"]
    cycle_count = state["cycle_count"]
    
    if not other_messages:
        print("⏭️ 没有对方消息")
        return {
            "is_new_message": False,
            "latest_message": "",
        }
    
    latest_message = other_messages[-1]
    
    is_new = True
    
    if cycle_count > 1 and previous_latest:
        if is_similar(previous_latest, latest_message, 0.6):
            is_new = False
    
    if last_sent_reply and is_similar(latest_message, last_sent_reply, 0.7):
        is_new = False
    
    if is_new:
        print(f"💬 发现新消息: {latest_message[:50]}...")
    else:
        print("⏭️ 没有新消息")
    
    return {
        "is_new_message": is_new,
        "latest_message": latest_message,
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

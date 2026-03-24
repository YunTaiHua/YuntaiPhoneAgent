"""消息归属判断节点"""
from difflib import SequenceMatcher

from yuntai.graphs.state import ReplyState

SIMILARITY_THRESHOLD = 0.6


def determine_ownership(state: ReplyState) -> dict:
    """
    判断消息归属节点
    
    输入: parsed_messages, other_messages, my_messages
    输出: current_other_messages, current_my_messages
    """
    messages = state["parsed_messages"]
    known_other = state["other_messages"]
    known_my = state["my_messages"]
    
    if not messages:
        return {
            "current_other_messages": [],
            "current_my_messages": [],
        }
    
    other_messages = []
    my_messages = []
    
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


def is_similar(msg1: str, msg2: str, threshold: float = 0.6) -> bool:
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

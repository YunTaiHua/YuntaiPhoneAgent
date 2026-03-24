"""更新记忆节点"""
import datetime
import threading

from yuntai.graphs.state import ReplyState

_file_manager: object | None = None
_tts_manager: object | None = None


def set_managers(file_manager: object | None = None, tts_manager: object | None = None) -> None:
    """设置管理器实例"""
    global _file_manager, _tts_manager
    _file_manager = file_manager
    _tts_manager = tts_manager


def update_memory(state: ReplyState) -> dict:
    """
    更新记忆节点
    
    输入: send_success, generated_reply, current_other_messages, latest_message
    输出: other_messages, my_messages, last_sent_reply, previous_latest_message
    """
    if not state.get("send_success"):
        return {}
    
    reply = state["generated_reply"]
    latest_message = state["latest_message"]
    current_other = state["current_other_messages"]
    current_my = state["current_my_messages"]
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    cycle_count = state["cycle_count"]
    
    new_my_messages = [reply] if reply else []
    new_other_messages = current_other
    
    if _file_manager:
        session_data = {
            "type": "chat_session",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_app": app_name,
            "target_object": chat_object,
            "cycle": cycle_count,
            "reply_generated": reply,
            "other_messages": [latest_message],
            "sent_success": True
        }
        _file_manager.save_conversation_history(session_data)
    
    if _tts_manager and getattr(_tts_manager, 'tts_enabled', False):
        threading.Timer(0.5, lambda: _tts_manager.speak_text_intelligently(reply)).start()
    
    return {
        "last_sent_reply": reply,
        "previous_latest_message": latest_message,
    }


def prune_messages(state: ReplyState) -> dict:
    """修剪消息列表，保持最大 50 条"""
    other = list(state["other_messages"])
    my = list(state["my_messages"])
    
    if len(other) > 50:
        other = other[-50:]
    if len(my) > 50:
        my = my[-50:]
    
    return {
        "other_messages": other,
        "my_messages": my,
    }

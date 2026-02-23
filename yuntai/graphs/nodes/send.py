"""
发送消息节点
"""
from yuntai.graphs.state import ReplyState
from yuntai.graphs.nodes.extract import _get_phone_agent


def send_message(state: ReplyState) -> dict:
    """
    发送消息节点
    
    输入: app_name, chat_object, device_id, generated_reply
    输出: send_success
    """
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    device_id = state["device_id"]
    reply = state["generated_reply"]
    
    if not reply:
        return {"send_success": False}
    
    if state.get("terminate_flag"):
        return {"send_success": False}
    
    print(f"📤 准备发送回复: {reply[:50]}...")
    
    agent = _get_phone_agent(device_id)
    success, result = agent.send_message(app_name, chat_object, reply)
    
    if success:
        print("✅ 回复已发送")
    else:
        print(f"❌ 回复发送失败: {result}")
    
    return {"send_success": success}

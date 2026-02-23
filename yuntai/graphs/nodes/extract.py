"""
提取聊天记录节点
"""
from yuntai.graphs.state import ReplyState
from yuntai.agents.phone_agent import PhoneAgent


_phone_agent_cache: dict = {}


def _get_phone_agent(device_id: str) -> PhoneAgent:
    if device_id not in _phone_agent_cache:
        _phone_agent_cache[device_id] = PhoneAgent(device_id)
    return _phone_agent_cache[device_id]


def extract_records(state: ReplyState) -> dict:
    """
    提取聊天记录节点
    
    输入: app_name, chat_object, device_id
    输出: extracted_records, cycle_count
    """
    from yuntai.graphs.nodes.control import check_terminate
    
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    device_id = state["device_id"]
    cycle_count = state["cycle_count"] + 1
    
    print(f"\n{'='*60}")
    print(f"📊 循环轮次 {cycle_count}/{state['max_cycles']}")
    print(f"{'='*60}")
    
    if check_terminate() or state.get("terminate_flag"):
        print("🛑 检测到终止信号")
        return {
            "cycle_count": cycle_count,
            "should_continue": False,
            "terminate_flag": True,
            "extracted_records": "",
        }
    
    agent = _get_phone_agent(device_id)
    success, records = agent.extract_chat_records(app_name, chat_object)
    
    if not success:
        print(f"❌ 提取聊天记录失败: {records}")
        return {
            "cycle_count": cycle_count,
            "extracted_records": "",
            "error": records,
        }
    
    return {
        "cycle_count": cycle_count,
        "extracted_records": records,
        "error": None,
    }

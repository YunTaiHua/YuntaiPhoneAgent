"""
提取聊天记录节点

负责从手机应用中提取聊天记录，使用缓存机制优化性能。
提供缓存清理功能防止内存泄漏。
"""

from __future__ import annotations

import threading
from typing import Any

from yuntai.graphs.state import ReplyState
from yuntai.agents.phone_agent import PhoneAgent
from yuntai.core.config import PHONE_AGENT_CACHE_MAX_SIZE


_phone_agent_cache: dict[str, PhoneAgent] = {}
_cache_lock: threading.Lock = threading.Lock()


def _get_phone_agent(device_id: str) -> PhoneAgent:
    """
    获取或创建 PhoneAgent 实例
    
    使用缓存机制避免重复创建实例，提高性能。
    当缓存超过最大限制时，自动清理最旧的条目。
    
    Args:
        device_id: 设备ID
    
    Returns:
        PhoneAgent 实例
    """
    with _cache_lock:
        if device_id in _phone_agent_cache:
            return _phone_agent_cache[device_id]
        
        if len(_phone_agent_cache) >= PHONE_AGENT_CACHE_MAX_SIZE:
            oldest_key = next(iter(_phone_agent_cache))
            del _phone_agent_cache[oldest_key]
            print(f"🧹 已清理最旧的 PhoneAgent 缓存: {oldest_key}")
        
        agent = PhoneAgent(device_id)
        _phone_agent_cache[device_id] = agent
        return agent


def clear_cache(device_id: str | None = None) -> None:
    """
    清理 PhoneAgent 缓存
    
    清理指定设备的缓存，如果未指定则清理全部缓存。
    建议在设备断开连接或应用退出时调用。
    
    Args:
        device_id: 设备ID，为 None 时清理全部缓存
    
    Example:
        >>> clear_cache("device_123")  # 清理指定设备缓存
        >>> clear_cache()  # 清理全部缓存
    """
    with _cache_lock:
        if device_id is not None:
            if device_id in _phone_agent_cache:
                del _phone_agent_cache[device_id]
                print(f"🧹 已清理设备缓存: {device_id}")
        else:
            _phone_agent_cache.clear()
            print("🧹 已清理全部 PhoneAgent 缓存")


def get_cache_size() -> int:
    """
    获取当前缓存大小
    
    Returns:
        缓存中的 PhoneAgent 实例数量
    """
    with _cache_lock:
        return len(_phone_agent_cache)


def extract_records(state: ReplyState) -> dict[str, Any]:
    """
    提取聊天记录节点
    
    从指定应用的聊天界面提取聊天记录。
    
    输入: app_name, chat_object, device_id
    输出: extracted_records, cycle_count
    
    Args:
        state: 回复状态字典，包含以下字段:
            - app_name: 应用名称
            - chat_object: 聊天对象
            - device_id: 设备ID
            - cycle_count: 当前循环次数
            - max_cycles: 最大循环次数
            - terminate_flag: 终止标志
    
    Returns:
        包含提取结果的字典:
            - cycle_count: 更新后的循环次数
            - extracted_records: 提取的聊天记录
            - error: 错误信息（如有）
            - should_continue: 是否继续（如有终止信号）
            - terminate_flag: 终止标志
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

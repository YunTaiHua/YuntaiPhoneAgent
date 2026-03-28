"""
提取聊天记录节点模块
====================

本模块负责从手机应用中提取聊天记录，使用缓存机制优化性能。

主要功能：
    - 从手机应用提取聊天记录
    - PhoneAgent 实例缓存管理
    - 缓存清理功能防止内存泄漏

函数说明：
    - extract_records: 提取聊天记录节点函数
    - clear_cache: 清理 PhoneAgent 缓存
    - get_cache_size: 获取当前缓存大小

使用示例：
    >>> from yuntai.graphs.nodes import extract_records
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = extract_records(state)
"""
from __future__ import annotations

import logging
import threading
from typing import Any

from yuntai.graphs.state import ReplyState
from yuntai.agents.phone_agent import PhoneAgent
from yuntai.core.config import PHONE_AGENT_CACHE_MAX_SIZE

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# PhoneAgent 缓存字典
_phone_agent_cache: dict[str, PhoneAgent] = {}
# 缓存访问锁
_cache_lock: threading.Lock = threading.Lock()


def _get_phone_agent(device_id: str) -> PhoneAgent:
    """
    获取或创建 PhoneAgent 实例
    
    使用缓存机制避免重复创建实例，提高性能。
    当缓存超过最大限制时，自动清理最旧的条目。
    
    Args:
        device_id: 设备 ID
    
    Returns:
        PhoneAgent: PhoneAgent 实例
    
    使用示例：
        >>> agent = _get_phone_agent("device_123")
    """
    with _cache_lock:
        # 检查缓存中是否存在
        if device_id in _phone_agent_cache:
            logger.debug("从缓存获取 PhoneAgent: %s", device_id)
            return _phone_agent_cache[device_id]
        
        # 检查缓存大小，超过限制时清理最旧的条目
        if len(_phone_agent_cache) >= PHONE_AGENT_CACHE_MAX_SIZE:
            oldest_key = next(iter(_phone_agent_cache))
            del _phone_agent_cache[oldest_key]
            logger.info("已清理最旧的 PhoneAgent 缓存: %s", oldest_key)
            print(f"🧹 已清理最旧的 PhoneAgent 缓存: {oldest_key}")
        
        # 创建新的 PhoneAgent 实例
        agent = PhoneAgent(device_id)
        _phone_agent_cache[device_id] = agent
        logger.debug("创建并缓存 PhoneAgent: %s", device_id)
        return agent


def clear_cache(device_id: str | None = None) -> None:
    """
    清理 PhoneAgent 缓存
    
    清理指定设备的缓存，如果未指定则清理全部缓存。
    建议在设备断开连接或应用退出时调用。
    
    Args:
        device_id: 设备 ID，为 None 时清理全部缓存
    
    使用示例：
        >>> clear_cache("device_123")  # 清理指定设备缓存
        >>> clear_cache()  # 清理全部缓存
    """
    with _cache_lock:
        if device_id is not None:
            # 清理指定设备的缓存
            if device_id in _phone_agent_cache:
                del _phone_agent_cache[device_id]
                logger.info("已清理设备缓存: %s", device_id)
                print(f"🧹 已清理设备缓存: {device_id}")
        else:
            # 清理全部缓存
            _phone_agent_cache.clear()
            logger.info("已清理全部 PhoneAgent 缓存")
            print("🧹 已清理全部 PhoneAgent 缓存")


def get_cache_size() -> int:
    """
    获取当前缓存大小
    
    Returns:
        int: 缓存中的 PhoneAgent 实例数量
    """
    with _cache_lock:
        return len(_phone_agent_cache)


def extract_records(state: ReplyState) -> dict[str, Any]:
    """
    提取聊天记录节点
    
    从指定应用的聊天界面提取聊天记录。
    
    输入状态字段:
        - app_name: 应用名称
        - chat_object: 聊天对象
        - device_id: 设备 ID
        - cycle_count: 当前循环次数
        - max_cycles: 最大循环次数
        - terminate_flag: 终止标志
    
    输出状态字段:
        - cycle_count: 更新后的循环次数
        - extracted_records: 提取的聊天记录
        - error: 错误信息（如有）
        - should_continue: 是否继续（如有终止信号）
        - terminate_flag: 终止标志
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, Any]: 包含提取结果的字典
    
    使用示例：
        >>> result = extract_records(state)
        >>> records = result.get("extracted_records", "")
    """
    # 导入终止检查函数
    from yuntai.graphs.nodes.control import check_terminate
    
    # 获取状态参数
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    device_id = state["device_id"]
    cycle_count = state["cycle_count"] + 1
    
    # 打印循环信息
    print(f"\n{'='*60}")
    print(f"📊 循环轮次 {cycle_count}/{state['max_cycles']}")
    print(f"{'='*60}")
    
    logger.debug("提取聊天记录: APP=%s, 对象=%s, 循环=%d", app_name, chat_object, cycle_count)
    
    # 检查终止信号
    if check_terminate() or state.get("terminate_flag"):
        logger.info("检测到终止信号，停止提取")
        print("🛑 检测到终止信号")
        return {
            "cycle_count": cycle_count,
            "should_continue": False,
            "terminate_flag": True,
            "extracted_records": "",
        }
    
    # 获取 PhoneAgent 实例
    agent = _get_phone_agent(device_id)
    
    # 提取聊天记录
    success, records = agent.extract_chat_records(app_name, chat_object)
    
    if not success:
        # 提取失败
        logger.error("提取聊天记录失败: %s", records)
        print(f"❌ 提取聊天记录失败: {records}")
        return {
            "cycle_count": cycle_count,
            "extracted_records": "",
            "error": records,
        }
    
    # 提取成功
    logger.debug("提取聊天记录成功，长度: %d", len(records))
    return {
        "cycle_count": cycle_count,
        "extracted_records": records,
        "error": None,
    }

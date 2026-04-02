"""
流程控制节点模块
================

本模块提供流程控制功能，包括终止检查和等待操作。

主要功能：
    - 检查是否应该终止工作流
    - 执行等待操作
    - 管理终止事件

函数说明：
    - set_terminate_event: 设置终止事件
    - check_terminate: 检查是否终止
    - check_continue: 检查是否继续节点函数
    - do_wait: 等待节点函数

使用示例：
    >>> from yuntai.graphs.nodes import check_continue, do_wait
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = check_continue(state)
"""
import logging
import time
import threading

from yuntai.graphs.state import ReplyState
from phone_agent.events import emit_agent_event

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# 全局终止事件
_terminate_event: threading.Event | None = None


def set_terminate_event(event: threading.Event) -> None:
    """
    设置终止事件
    
    设置全局的终止事件对象，用于控制工作流的终止。
    
    Args:
        event: threading.Event 实例
    
    使用示例：
        >>> event = threading.Event()
        >>> set_terminate_event(event)
    """
    global _terminate_event
    _terminate_event = event
    logger.debug("已设置终止事件")


def check_terminate() -> bool:
    """
    检查是否收到终止信号
    
    Returns:
        bool: 是否应该终止
    """
    if _terminate_event and _terminate_event.is_set():
        return True
    return False


def check_continue(state: ReplyState) -> dict[str, bool]:
    """
    检查是否继续节点
    
    根据循环次数和终止标志判断是否应该继续执行。
    
    输入状态字段:
        - cycle_count: 当前循环次数
        - max_cycles: 最大循环次数
        - terminate_flag: 终止标志
    
    输出状态字段:
        - should_continue: 是否应该继续
        - terminate_flag: 终止标志
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, bool]: 包含继续判断结果的字典
    
    使用示例：
        >>> result = check_continue(state)
        >>> if result["should_continue"]:
        ...     print("继续执行")
    """
    # 获取循环参数
    cycle_count = state["cycle_count"]
    max_cycles = state["max_cycles"]
    
    # 检查终止信号
    if check_terminate() or state.get("terminate_flag"):
        logger.info("检测到终止信号，正在退出...")
        emit_agent_event("status", {"message": "🛑 检测到终止信号，正在退出..."}, source="yuntai.reply.control")
        return {
            "should_continue": False,
            "terminate_flag": True
        }
    
    # 检查是否达到最大循环次数
    if cycle_count >= max_cycles:
        logger.info("达到最大循环次数: %d", max_cycles)
        emit_agent_event("status", {"message": f"📊 达到最大循环次数 {max_cycles}"}, source="yuntai.reply.control")
        return {"should_continue": False}
    
    # 继续执行
    logger.debug("继续执行，当前循环: %d/%d", cycle_count, max_cycles)
    return {"should_continue": True}


def do_wait(state: ReplyState) -> dict[str, object]:
    """
    等待节点
    
    在循环之间等待指定时间，同时检查终止信号。
    
    输入状态字段:
        - wait_seconds: 等待秒数
        - terminate_flag: 终止标志
    
    输出状态字段:
        - 无（仅等待）
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, object]: 空字典
    
    使用示例：
        >>> result = do_wait(state)
    """
    # 获取等待时间
    wait_seconds = state.get("wait_seconds", 1)
    
    logger.debug("等待 %d 秒", wait_seconds)
    emit_agent_event("status", {"message": f"⏳ 等待 {wait_seconds} 秒..."}, source="yuntai.reply.control")
    
    # 分段等待，便于响应终止信号
    for _ in range(wait_seconds):
        # 检查终止信号
        if check_terminate() or state.get("terminate_flag"):
            logger.debug("等待期间检测到终止信号")
            break
        time.sleep(1)
    
    return {}

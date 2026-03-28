"""
检查新消息节点模块
==================

本模块负责检测是否有新的对方消息，基于已读消息列表进行判断。

主要功能：
    - 检测是否有新的对方消息
    - 维护已读消息列表
    - 过滤重复消息

函数说明：
    - check_new_message: 检查新消息节点函数

使用示例：
    >>> from yuntai.graphs.nodes import check_new_message
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = check_new_message(state)
"""
import logging

from yuntai.graphs.state import ReplyState
from yuntai.tools import is_similar

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def check_new_message(state: ReplyState) -> dict[str, object]:
    """
    检查是否有新消息节点
    
    根据已读消息列表判断是否有新的对方消息。
    使用相似度匹配过滤重复消息。
    
    输入状态字段:
        - current_other_messages: 当前轮次对方消息
        - seen_other_messages: 已读对方消息列表
    
    输出状态字段:
        - is_new_message: 是否有新消息
        - latest_message: 最新消息内容
        - seen_other_messages: 更新后的已读消息列表
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, object]: 包含新消息检测结果的字典
    
    使用示例：
        >>> result = check_new_message(state)
        >>> if result["is_new_message"]:
        ...     print(f"新消息: {result['latest_message']}")
    """
    # 获取当前对方消息和已读消息
    other_messages = state["current_other_messages"]
    seen_messages = state.get("seen_other_messages", [])
    
    # 检查是否有对方消息
    if not other_messages:
        logger.debug("没有对方消息")
        print("⏭️ 没有对方消息")
        return {
            "is_new_message": False,
            "latest_message": "",
        }
    
    logger.debug("检查新消息，当前消息数: %d, 已读消息数: %d", 
                len(other_messages), len(seen_messages))
    
    # 过滤已读消息，找出真正的新消息
    truly_new: list[str] = []
    for msg in other_messages:
        # 检查是否与已读消息相似
        is_seen = any(is_similar(msg, seen, 0.7) for seen in seen_messages)
        if not is_seen:
            truly_new.append(msg)
    
    # 判断是否有新消息
    is_new = len(truly_new) > 0
    
    # 获取最新消息
    latest_new = truly_new[-1] if truly_new else ""
    
    # 更新已读消息列表
    updated_seen = seen_messages + other_messages
    
    # 打印结果
    if is_new:
        logger.info("发现新消息: %s...", latest_new[:50] if len(latest_new) > 50 else latest_new)
        print(f"💬 发现新消息: {latest_new[:50]}...")
    else:
        logger.debug("没有新消息")
        print("⏭️ 没有新消息")
    
    return {
        "is_new_message": is_new,
        "latest_message": latest_new,
        "seen_other_messages": updated_seen,
    }

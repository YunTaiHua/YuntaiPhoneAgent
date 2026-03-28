"""
消息归属判断节点模块
====================

本模块负责判断消息的归属（对方消息或我方消息），基于已知消息和界面特征进行判断。

主要功能：
    - 基于相似度匹配判断消息归属
    - 基于头像位置判断消息归属
    - 基于气泡颜色判断消息归属

函数说明：
    - determine_ownership: 判断消息归属节点函数

使用示例：
    >>> from yuntai.graphs.nodes import determine_ownership
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = determine_ownership(state)
"""
import logging

from yuntai.graphs.state import ReplyState
from yuntai.tools import is_similar
from yuntai.core.config import SIMILARITY_THRESHOLD

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def determine_ownership(state: ReplyState) -> dict[str, list[str]]:
    """
    判断消息归属节点
    
    根据已知消息列表和消息界面特征判断消息归属。
    判断优先级：
    1. 与已知我方消息相似
    2. 与已知对方消息相似
    3. 头像位置（左侧为对方，右侧为我方）
    4. 气泡颜色（白色为对方，其他颜色为我方）
    
    输入状态字段:
        - parsed_messages: 解析后的消息列表
        - other_messages: 已知对方消息列表
        - my_messages: 已知我方消息列表
    
    输出状态字段:
        - current_other_messages: 当前轮次对方消息
        - current_my_messages: 当前轮次我方消息
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, list[str]]: 包含归属判断结果的字典
    
    使用示例：
        >>> result = determine_ownership(state)
        >>> other_msgs = result["current_other_messages"]
        >>> my_msgs = result["current_my_messages"]
    """
    # 获取消息列表
    messages = state["parsed_messages"]
    known_other = state["other_messages"]
    known_my = state["my_messages"]
    
    # 检查是否有消息需要处理
    if not messages:
        logger.debug("没有消息需要判断归属")
        return {
            "current_other_messages": [],
            "current_my_messages": [],
        }
    
    logger.debug("开始判断消息归属，消息数: %d", len(messages))
    
    # 初始化结果列表
    other_messages: list[str] = []
    my_messages: list[str] = []
    
    # 遍历消息进行判断
    for msg in messages:
        content = msg.get("content", "").strip()
        position = msg.get("position", "")
        color = msg.get("color", "")
        
        # 过滤过短的消息
        if len(content) < 2:
            continue
        
        # 优先级 1: 检查是否与已知我方消息相似
        is_my_message = any(
            is_similar(content, m, SIMILARITY_THRESHOLD) 
            for m in known_my
        )
        if is_my_message:
            my_messages.append(content)
            logger.debug("消息归类为我方（相似匹配）: %s...", content[:20])
            continue
        
        # 优先级 2: 检查是否与已知对方消息相似
        is_other_message = any(
            is_similar(content, m, SIMILARITY_THRESHOLD)
            for m in known_other
        )
        if is_other_message:
            other_messages.append(content)
            logger.debug("消息归类为对方（相似匹配）: %s...", content[:20])
            continue
        
        # 优先级 3: 根据头像位置判断
        if position == "左侧有头像":
            other_messages.append(content)
            logger.debug("消息归类为对方（左侧头像）: %s...", content[:20])
        elif position == "右侧有头像":
            my_messages.append(content)
            logger.debug("消息归类为我方（右侧头像）: %s...", content[:20])
        else:
            # 优先级 4: 根据气泡颜色判断
            if color == "白色":
                other_messages.append(content)
                logger.debug("消息归类为对方（白色气泡）: %s...", content[:20])
            elif color in ["红色", "粉色", "蓝色", "绿色", "紫色", "黑色", "灰色", "橙色", "黄色"]:
                my_messages.append(content)
                logger.debug("消息归类为我方（彩色气泡）: %s...", content[:20])
            else:
                # 无法判断，默认归为对方消息
                other_messages.append(content)
                logger.debug("消息归类为对方（默认）: %s...", content[:20])
    
    # 打印统计信息
    print(f"📋 对方消息 {len(other_messages)} 条，我方消息 {len(my_messages)} 条")
    logger.debug("归属判断完成: 对方 %d 条, 我方 %d 条", len(other_messages), len(my_messages))
    
    return {
        "current_other_messages": other_messages,
        "current_my_messages": my_messages,
    }

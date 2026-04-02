"""
发送消息节点模块
================

本模块负责发送生成的回复消息到手机应用。

主要功能：
    - 发送回复消息到指定聊天对象
    - 处理发送失败情况

函数说明：
    - send_message: 发送消息节点函数

使用示例：
    >>> from yuntai.graphs.nodes import send_message
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = send_message(state)
"""
import logging

from yuntai.graphs.state import ReplyState
from yuntai.graphs.nodes.extract import _get_phone_agent
from phone_agent.events import emit_agent_event

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def send_message(state: ReplyState) -> dict[str, bool]:
    """
    发送消息节点
    
    将生成的回复发送到指定的聊天对象。
    
    输入状态字段:
        - app_name: 应用名称
        - chat_object: 聊天对象
        - device_id: 设备 ID
        - generated_reply: 生成的回复内容
        - terminate_flag: 终止标志
    
    输出状态字段:
        - send_success: 发送是否成功
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, bool]: 包含发送结果的字典
    
    使用示例：
        >>> result = send_message(state)
        >>> if result["send_success"]:
        ...     print("消息发送成功")
    """
    # 获取状态参数
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    device_id = state["device_id"]
    reply = state["generated_reply"]
    
    # 检查回复是否为空
    if not reply:
        logger.debug("回复为空，跳过发送")
        return {"send_success": False}
    
    # 检查终止标志
    if state.get("terminate_flag"):
        logger.debug("检测到终止标志，跳过发送")
        return {"send_success": False}
    
    logger.info("准备发送回复: %s...", reply[:50])
    emit_agent_event("status", {"message": f"📤 准备发送回复: {reply[:50]}..."}, source="yuntai.reply.send")
    
    # 获取 PhoneAgent 实例
    agent = _get_phone_agent(device_id)
    
    # 发送消息
    success, result = agent.send_message(app_name, chat_object, reply)
    
    if success:
        logger.info("回复发送成功")
        emit_agent_event("status", {"message": "✅ 回复已发送"}, source="yuntai.reply.send")
    else:
        logger.error("回复发送失败: %s", result)
        emit_agent_event("error", {"message": f"回复发送失败: {result}"}, source="yuntai.reply.send", level="error")
    
    return {"send_success": success}

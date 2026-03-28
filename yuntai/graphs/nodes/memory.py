"""
更新记忆节点模块
================

本模块负责更新对话记忆，保存对话历史并触发 TTS 播报。

主要功能：
    - 保存对话历史到文件
    - 触发 TTS 语音播报
    - 管理全局管理器实例

函数说明：
    - set_managers: 设置管理器实例
    - update_memory: 更新记忆节点函数
    - prune_messages: 修剪消息列表

使用示例：
    >>> from yuntai.graphs.nodes import update_memory
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = update_memory(state)
"""
import datetime
import logging
import threading

from yuntai.graphs.state import ReplyState

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# 全局管理器实例
_file_manager: object | None = None
_tts_manager: object | None = None


def set_managers(
    file_manager: object | None = None,
    tts_manager: object | None = None
) -> None:
    """
    设置管理器实例
    
    设置全局的文件管理器和 TTS 管理器实例。
    在工作流初始化时调用。
    
    Args:
        file_manager: 文件管理器实例
        tts_manager: TTS 管理器实例
    
    使用示例：
        >>> set_managers(file_manager, tts_manager)
    """
    global _file_manager, _tts_manager
    _file_manager = file_manager
    _tts_manager = tts_manager
    logger.debug("已设置管理器实例")


def update_memory(state: ReplyState) -> dict[str, object]:
    """
    更新记忆节点
    
    保存对话历史到文件，并触发 TTS 语音播报。
    
    输入状态字段:
        - send_success: 发送是否成功
        - generated_reply: 生成的回复
        - current_other_messages: 当前轮次对方消息
        - latest_message: 最新消息
        - app_name: 应用名称
        - chat_object: 聊天对象
        - cycle_count: 循环次数
    
    输出状态字段:
        - last_sent_reply: 最后发送的回复
        - previous_latest_message: 上一轮最新消息
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, object]: 包含更新结果的字典
    
    使用示例：
        >>> result = update_memory(state)
    """
    # 检查发送是否成功
    if not state.get("send_success"):
        logger.debug("发送未成功，跳过记忆更新")
        return {}
    
    # 获取状态参数
    reply = state["generated_reply"]
    latest_message = state["latest_message"]
    current_other = state["current_other_messages"]
    current_my = state["current_my_messages"]
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    cycle_count = state["cycle_count"]
    
    logger.debug("更新记忆，循环: %d", cycle_count)
    
    # 保存对话历史到文件
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
        logger.debug("已保存对话历史")
    
    # 触发 TTS 语音播报
    if _tts_manager and getattr(_tts_manager, 'tts_enabled', False):
        # 延迟播报，避免与发送操作冲突
        threading.Timer(0.5, lambda: _tts_manager.speak_text_intelligently(reply)).start()
        logger.debug("已安排 TTS 播报")
    
    return {
        "last_sent_reply": reply,
        "previous_latest_message": latest_message,
    }


def prune_messages(state: ReplyState) -> dict[str, list[str]]:
    """
    修剪消息列表
    
    保持消息列表不超过 50 条，防止内存占用过大。
    
    输入状态字段:
        - other_messages: 对方消息列表
        - my_messages: 我方消息列表
    
    输出状态字段:
        - other_messages: 修剪后的对方消息列表
        - my_messages: 修剪后的我方消息列表
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, list[str]]: 包含修剪后消息列表的字典
    
    使用示例：
        >>> result = prune_messages(state)
    """
    # 复制消息列表
    other = list(state["other_messages"])
    my = list(state["my_messages"])
    
    # 修剪超过 50 条的消息
    if len(other) > 50:
        other = other[-50:]
        logger.debug("修剪对方消息列表至 50 条")
    
    if len(my) > 50:
        my = my[-50:]
        logger.debug("修剪我方消息列表至 50 条")
    
    return {
        "other_messages": other,
        "my_messages": my,
    }

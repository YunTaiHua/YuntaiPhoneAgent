"""
生成回复节点模块
================

本模块负责根据聊天记录生成智能回复，支持 LangChain Callbacks 实现流式输出。

主要功能：
    - 使用 AI 模型生成回复
    - 支持流式输出
    - 过滤相似回复

函数说明：
    - generate_reply: 生成回复节点函数

使用示例：
    >>> from yuntai.graphs.nodes import generate_reply
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = generate_reply(state)
"""
import logging

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage

from yuntai.graphs.state import ReplyState
from yuntai.models import get_chat_model
from yuntai.callbacks import get_callback_manager
from yuntai.prompts import REPLY_NODE_SYSTEM_PROMPT, REPLY_NODE_USER_PROMPT
from yuntai.tools.similarity import is_similar
from yuntai.tools.callback_utils import prepare_callbacks
from phone_agent.events import emit_agent_event

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def generate_reply(
    state: ReplyState,
    callbacks: list[BaseCallbackHandler] | None = None
) -> dict[str, str]:
    """
    生成回复节点（支持 Callbacks 流式输出）
    
    根据最新消息和历史对话生成智能回复。
    
    输入状态字段:
        - latest_message: 最新消息内容
        - current_other_messages: 当前轮次对方消息
        - last_sent_reply: 上次发送的回复
    
    输出状态字段:
        - generated_reply: 生成的回复内容
    
    Args:
        state: 回复状态字典
        callbacks: 自定义回调处理器列表
    
    Returns:
        dict[str, str]: 包含生成回复的字典
    
    使用示例：
        >>> result = generate_reply(state)
        >>> reply = result.get("generated_reply", "")
    """
    # 获取状态参数
    latest_message = state["latest_message"]
    other_messages = state["current_other_messages"]
    last_sent_reply = state["last_sent_reply"]
    
    # 检查消息有效性
    if not latest_message or len(latest_message) < 2:
        logger.debug("消息内容无效")
        emit_agent_event("status", {"message": "⏭️ 消息内容无效"}, source="yuntai.reply.reply")
        return {"generated_reply": ""}
    
    logger.debug("开始生成回复，最新消息: %s...", latest_message[:50])
    
    # 获取历史消息（排除最新消息）
    history_messages = other_messages[:-1] if len(other_messages) > 1 else []
    
    # 构建历史对话提示词
    history_prompt = ""
    if history_messages:
        history_prompt = "\n\n=== 历史对话 ===\n"
        for i, msg in enumerate(history_messages[-5:], 1):
            history_prompt += f"{i}. {msg[:50]}...\n"
    
    # 构建完整提示词
    prompt = REPLY_NODE_USER_PROMPT.format(
        latest_message=latest_message,
        history_prompt=history_prompt
    )
    
    try:
        # 准备回调处理器
        all_callbacks = prepare_callbacks(callbacks)
        
        # 获取聊天模型
        model = get_chat_model()
        
        # 构建消息列表
        messages = [
            SystemMessage(content=REPLY_NODE_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # 构建回调配置
        config = {"callbacks": all_callbacks} if all_callbacks else {}
        
        # 调用模型生成回复
        response = model.invoke(messages, config=config)
        
        # 提取并清理回复
        reply = response.content.strip()
        
        # 只保留第一句话
        if "。" in reply:
            reply = reply.split("。")[0] + "。"
        
        # 检查回复有效性
        if len(reply) < 2:
            logger.debug("未能生成有效回复")
            emit_agent_event("status", {"message": "⏭️ 未能生成有效回复"}, source="yuntai.reply.reply")
            return {"generated_reply": ""}
        
        # 检查是否与上次回复相似
        if last_sent_reply and is_similar(reply, last_sent_reply, 0.7):
            logger.debug("回复与上次相似，跳过")
            emit_agent_event("status", {"message": "⏭️ 回复与上次相似，跳过"}, source="yuntai.reply.reply")
            return {"generated_reply": ""}
        
        # 打印生成的回复
        logger.info("生成回复: %s...", reply[:50])
        emit_agent_event("status", {"message": f"💬 生成回复: {reply[:50]}..."}, source="yuntai.reply.reply")
        
        return {"generated_reply": reply}
        
    except Exception as e:
        # 记录错误日志
        logger.error("生成回复失败: %s", str(e), exc_info=True)
        emit_agent_event("error", {"message": f"生成回复失败: {str(e)}"}, source="yuntai.reply.reply", level="error")
        return {"generated_reply": ""}

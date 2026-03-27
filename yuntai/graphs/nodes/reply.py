"""
生成回复节点，支持 LangChain Callbacks 实现流式输出

该模块负责根据聊天记录生成智能回复，支持流式输出和回调机制。
"""

from __future__ import annotations

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage

from yuntai.graphs.state import ReplyState
from yuntai.models import get_zhipu_client, get_chat_model
from yuntai.core.config import ZHIPU_CHAT_MODEL
from yuntai.callbacks import get_callback_manager, StreamingCallbackHandler
from yuntai.prompts import REPLY_NODE_SYSTEM_PROMPT, REPLY_NODE_USER_PROMPT
from yuntai.tools import is_similar, prepare_callbacks


def generate_reply(
    state: ReplyState,
    callbacks: list[BaseCallbackHandler] | None = None
) -> dict[str, str]:
    """
    生成回复节点（支持 Callbacks 流式输出）
    
    根据最新消息和历史对话生成智能回复。
    
    输入: latest_message, current_other_messages
    输出: generated_reply
    
    Args:
        state: 回复状态字典
        callbacks: 自定义回调处理器列表
    
    Returns:
        包含生成回复的字典
    """
    latest_message = state["latest_message"]
    other_messages = state["current_other_messages"]
    last_sent_reply = state["last_sent_reply"]
    
    if not latest_message or len(latest_message) < 2:
        print("⏭️ 消息内容无效")
        return {"generated_reply": ""}
    
    history_messages = other_messages[:-1] if len(other_messages) > 1 else []
    
    history_prompt = ""
    if history_messages:
        history_prompt = "\n\n=== 历史对话 ===\n"
        for i, msg in enumerate(history_messages[-5:], 1):
            history_prompt += f"{i}. {msg[:50]}...\n"
    
    prompt = REPLY_NODE_USER_PROMPT.format(
        latest_message=latest_message,
        history_prompt=history_prompt
    )
    
    try:
        all_callbacks = prepare_callbacks(callbacks)
        
        model = get_chat_model()
        
        messages = [
            SystemMessage(content=REPLY_NODE_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        config = {"callbacks": all_callbacks} if all_callbacks else {}
        
        response = model.invoke(messages, config=config)
        
        reply = response.content.strip()
        
        if "。" in reply:
            reply = reply.split("。")[0] + "。"
        
        if len(reply) < 2:
            print("⏭️ 未能生成有效回复")
            return {"generated_reply": ""}
        
        if last_sent_reply and is_similar(reply, last_sent_reply, 0.7):
            print("⏭️ 回复与上次相似，跳过")
            return {"generated_reply": ""}
        
        print(f"💬 生成回复: {reply[:50]}...")
        return {"generated_reply": reply}
        
    except Exception as e:
        print(f"❌ 生成回复失败: {e}")
        return {"generated_reply": ""}

"""
生成回复节点
支持 LangChain Callbacks 实现流式输出
"""
from typing import Optional, List
from langchain_core.callbacks import BaseCallbackHandler

from yuntai.graphs.state import ReplyState
from yuntai.models import get_zhipu_client, get_chat_model
from yuntai.core.config import ZHIPU_CHAT_MODEL
from yuntai.callbacks import get_callback_manager, StreamingCallbackHandler


def generate_reply(
    state: ReplyState,
    callbacks: Optional[List[BaseCallbackHandler]] = None
) -> dict:
    """
    生成回复节点（支持 Callbacks 流式输出）
    
    输入: latest_message, current_other_messages
    输出: generated_reply
    
    Args:
        state: 回复状态
        callbacks: 自定义回调处理器列表
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
    
    system_prompt = """你是一个友好的助手，名字叫'小芸'，性别为女。
根据对方的消息，生成一个自然、友好的回复。
回复要简洁，通常1-2句话即可。
直接输出回复内容，不要加任何标注。"""
    
    prompt = f"""对方发来消息：{latest_message}
{history_prompt}

请生成回复："""
    
    try:
        # 准备回调处理器
        all_callbacks = _prepare_callbacks(callbacks)
        
        # 使用 LangChain 模型（支持 callbacks）
        model = get_chat_model()
        
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        # 使用回调配置
        config = {"callbacks": all_callbacks} if all_callbacks else {}
        
        # 调用模型
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


def _prepare_callbacks(
    callbacks: Optional[List[BaseCallbackHandler]] = None
) -> List[BaseCallbackHandler]:
    """
    准备回调处理器列表
    
    Args:
        callbacks: 用户提供的回调列表
    
    Returns:
        合并后的回调处理器列表
    """
    all_callbacks = []
    
    # 添加全局回调
    callback_manager = get_callback_manager()
    global_callbacks = callback_manager.get_callbacks(include_global=True)
    all_callbacks.extend(global_callbacks)
    
    # 添加用户提供的回调
    if callbacks:
        all_callbacks.extend(callbacks)
    
    return all_callbacks


def is_similar(msg1: str, msg2: str, threshold: float) -> bool:
    from difflib import SequenceMatcher
    import re
    
    def clean(text):
        return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower()
    
    c1, c2 = clean(msg1), clean(msg2)
    if not c1 or not c2:
        return False
    
    if c1 == c2 or c1 in c2 or c2 in c1:
        return True
    
    return SequenceMatcher(None, c1, c2).ratio() >= threshold

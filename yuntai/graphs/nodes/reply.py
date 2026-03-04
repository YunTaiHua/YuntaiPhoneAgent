"""
生成回复节点
"""
from yuntai.graphs.state import ReplyState
from yuntai.models import get_zhipu_client
from yuntai.core.config import ZHIPU_CHAT_MODEL


def generate_reply(state: ReplyState) -> dict:
    """
    生成回复节点
    
    输入: latest_message, current_other_messages
    输出: generated_reply
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
        client = get_zhipu_client()
        stream = client.chat.completions.create(
            model=ZHIPU_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            stream=True,
            max_tokens=500
        )
        
        reply = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                if chunk.choices[0].delta.content is not None:
                    reply += chunk.choices[0].delta.content
        reply = reply.strip()
        
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

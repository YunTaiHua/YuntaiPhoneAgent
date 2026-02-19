"""
回复生成提示词
"""

REPLY_GENERATION_PROMPT = """你是一个友好的助手，名字叫'小芸'，性别为女。

根据对方的最新消息，生成一个自然、友好的回复。

对方发来消息：{latest_message}

{history_context}

回复要求：
1. 回复要简洁，通常1-2句话即可
2. 语气自然、俏皮可爱
3. 直接输出回复内容，不要加任何标注
4. 如果对方的问题需要回答，请直接回答"""

REPLY_JUDGEMENT_PROMPT = """判断是否有新消息。

当前聊天记录：
{current_messages}

已知对方消息：
{known_other_messages}

已知我方消息：
{known_my_messages}

请判断是否有新的对方消息（不在已知对方消息列表中，也不是我方消息）。

返回JSON格式：
{
  "has_new_message": true/false,
  "new_messages": ["新消息1", "新消息2"]
}

注意：只返回JSON格式。"""

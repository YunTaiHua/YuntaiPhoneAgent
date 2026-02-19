"""
消息工具模块
处理消息解析、归属判断、回复生成等
"""
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher

from zhipuai import ZhipuAI

from yuntai.config import ZHIPU_CHAT_MODEL


SIMILARITY_THRESHOLD = 0.6
MAX_MESSAGE_LIST_LENGTH = 50


def parse_messages(record: str, zhipu_client: ZhipuAI) -> List[Dict[str, str]]:
    """
    解析聊天记录，提取消息
    
    Args:
        record: 聊天记录文本
        zhipu_client: 智谱AI客户端
    
    Returns:
        消息列表，每个消息包含 content, position, color
    """
    if not record or len(record.strip()) < 10:
        return []
    
    prompt_text = f"""从以下聊天记录中提取所有有效消息，返回JSON格式。

聊天记录：
{record[:2000]}

返回格式要求：
{{
  "messages": [
    {{"content": "消息内容", "position": "左侧有头像/右侧有头像/未知", "color": "白色/红色/蓝色/绿色/粉色/紫色/黑色/灰色/橙色/黄色/未知"}}
  ]
}}

重要：
1. 只输出JSON，不要有其他文字
2. position只能是：左侧有头像、右侧有头像、未知
3. 消息内容要完整，不要截断
"""
    
    try:
        response = zhipu_client.chat.completions.create(
            model=ZHIPU_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "你必须只输出符合要求的JSON，不要加任何额外文字！"},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        resp_content = response.choices[0].message.content.strip()
        if resp_content.startswith("```"):
            resp_content = resp_content.replace("```json", "").replace("```", "").strip()
        
        structured_data = json.loads(resp_content)
        messages = structured_data.get("messages", [])
        
        final_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            content = msg.get("content", "").strip()
            position = msg.get("position", "未知")
            color = msg.get("color", "未知")
            
            if len(content) >= 2 and not any(existing["content"] == content for existing in final_messages):
                final_messages.append({
                    "content": content,
                    "position": _standardize_position(position),
                    "color": _standardize_color(color)
                })
        
        return final_messages
    
    except Exception as e:
        print(f"解析消息失败: {e}")
        return _emergency_extract(record)


def _standardize_position(position: str) -> str:
    """标准化头像位置"""
    if not position or position == "未知":
        return "未知"
    if "左" in position.lower():
        return "左侧有头像"
    elif "右" in position.lower():
        return "右侧有头像"
    return "未知"


def _standardize_color(color: str) -> str:
    """标准化气泡颜色"""
    if not color or color == "未知":
        return "未知"
    color_lower = color.lower()
    color_map = {
        "粉红": "粉色", "红": "红色", "蓝": "蓝色", "绿": "绿色",
        "紫": "紫色", "黑": "黑色", "灰": "灰色", "橙": "橙色", "黄": "黄色", "白": "白色"
    }
    for key, val in color_map.items():
        if key in color_lower:
            return val
    return "未知"


def _emergency_extract(record: str) -> List[Dict[str, str]]:
    """紧急提取方法：当AI解析失败时使用"""
    record_clean = re.sub(r"思考过程:|性能指标:|总推理时间:|首 Token 延迟|思考完成延迟", "", record)
    record_clean = re.sub(r"[^\u4e00-\u9fff\w\s\.,，。！？；：""''💪~]", "", record_clean)
    
    sentences = re.split(r"[。！？；：\n]", record_clean)
    final_messages = []
    
    for sent in sentences:
        sent = sent.strip().strip('"').strip("'")
        if (len(sent) >= 2 and not sent.isdigit() and not sent.startswith("20:") 
            and "气泡" not in sent and "头像" not in sent and "消息" not in sent):
            if not any(existing["content"] == sent for existing in final_messages):
                position = "右侧有头像" if "芸苔" in sent or "💪" in sent or "~" in sent else "左侧有头像"
                color = "红色" if position == "右侧有头像" else "白色"
                final_messages.append({
                    "content": sent,
                    "position": position,
                    "color": color
                })
    
    return final_messages


def is_message_similar(msg1: str, msg2: str, threshold: float = 0.6) -> bool:
    """判断两条消息是否相似"""
    if not msg1 or not msg2:
        return False
    
    def clean_text(text):
        if not text:
            return ""
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        return text.lower()
    
    clean_msg1 = clean_text(msg1)
    clean_msg2 = clean_text(msg2)
    
    if not clean_msg1 or not clean_msg2:
        return msg1 == msg2 or msg1 in msg2 or msg2 in msg1
    
    if clean_msg1 == clean_msg2:
        return True
    
    if clean_msg1 in clean_msg2 or clean_msg2 in clean_msg1:
        return True
    
    similarity = SequenceMatcher(None, clean_msg1, clean_msg2).ratio()
    return similarity >= threshold


def determine_message_ownership(
    messages: List[Dict[str, str]],
    my_messages_list: List[str],
    other_messages_list: List[str]
) -> Tuple[List[str], List[str]]:
    """
    判断消息归属
    
    Args:
        messages: 解析后的消息列表
        my_messages_list: 已知的我方消息列表
        other_messages_list: 已知的对方消息列表
    
    Returns:
        (对方消息列表, 我方消息列表)
    """
    other_messages = []
    my_messages = []
    
    for msg in messages:
        content = msg.get("content", "").strip()
        position = msg.get("position", "")
        color = msg.get("color", "")
        
        if not content or len(content) < 2:
            continue
        
        is_my_message = False
        for my_msg in my_messages_list:
            if is_message_similar(content, my_msg, threshold=SIMILARITY_THRESHOLD):
                is_my_message = True
                my_messages.append(content)
                break
        
        if is_my_message:
            continue
        
        is_other_message = False
        for other_msg in other_messages_list:
            if is_message_similar(content, other_msg, threshold=SIMILARITY_THRESHOLD):
                is_other_message = True
                other_messages.append(content)
                break
        
        if is_other_message:
            continue
        
        if position == "左侧有头像":
            other_messages.append(content)
        elif position == "右侧有头像":
            my_messages.append(content)
        else:
            if color == "白色":
                other_messages.append(content)
            elif color in ["红色", "粉色", "蓝色", "绿色", "紫色", "黑色", "灰色", "橙色", "黄色"]:
                my_messages.append(content)
    
    return other_messages, my_messages


def generate_reply(
    latest_message: str,
    history_messages: List[str],
    zhipu_client: ZhipuAI,
    system_prompt: str = ""
) -> str:
    """
    生成回复内容
    
    Args:
        latest_message: 最新消息
        history_messages: 历史消息列表
        zhipu_client: 智谱AI客户端
        system_prompt: 系统提示词
    
    Returns:
        生成的回复
    """
    if not latest_message:
        return ""
    
    history_prompt = ""
    if history_messages:
        history_prompt = "\n\n=== 历史对话（按时间顺序，从旧到新）===\n"
        for i, msg in enumerate(history_messages[-5:], 1):
            history_prompt += f"{i}. {msg[:50]}...\n"
    
    default_system = """你是一个友好的助手，名字叫'小芸'，性别为女。
根据对方的消息，生成一个自然、友好的回复。
回复要简洁，通常1-2句话即可。
直接输出回复内容，不要加任何标注。"""
    
    prompt = f"""对方发来消息：{latest_message}
{history_prompt}

请生成回复："""
    
    try:
        response = zhipu_client.chat.completions.create(
            model=ZHIPU_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or default_system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        reply = response.choices[0].message.content.strip()
        
        if "。" in reply:
            reply = reply.split("。")[0] + "。"
        
        return reply
    
    except Exception as e:
        print(f"生成回复失败: {e}")
        return ""


def check_new_messages(
    current_other_messages: List[str],
    previous_other_messages: List[str],
    my_messages_list: List[str]
) -> Tuple[bool, List[str]]:
    """
    检查是否有新消息
    
    Args:
        current_other_messages: 当前解析的对方消息
        previous_other_messages: 之前已知的对方消息
        my_messages_list: 已知的我方消息
    
    Returns:
        (是否有新消息, 新消息列表)
    """
    new_messages = []
    
    for msg in current_other_messages:
        is_new = True
        
        for existing_msg in previous_other_messages:
            if is_message_similar(msg, existing_msg, threshold=0.5):
                is_new = False
                break
        
        if is_new:
            for my_msg in my_messages_list:
                if is_message_similar(msg, my_msg, threshold=0.5):
                    is_new = False
                    break
        
        if is_new:
            new_messages.append(msg)
    
    return len(new_messages) > 0, new_messages

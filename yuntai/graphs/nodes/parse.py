"""解析消息节点"""
import json

from yuntai.graphs.state import ReplyState
from yuntai.models import get_zhipu_client
from yuntai.core.config import ZHIPU_CHAT_MODEL
from yuntai.prompts import (
    PARSE_MESSAGES_SYSTEM_PROMPT,
    PARSE_MESSAGES_PROMPT,
    PARSE_MESSAGES_MAX_LENGTH,
)


def parse_messages(state: ReplyState) -> dict:
    """
    解析消息节点
    
    输入: extracted_records
    输出: parse_success, parsed_messages
    """
    records = state["extracted_records"]
    
    if not records or len(records.strip()) < 10:
        print("⏭️ 聊天记录为空")
        return {
            "parse_success": False,
            "parsed_messages": [],
        }
    
    client = get_zhipu_client()
    
    records_text = records[:PARSE_MESSAGES_MAX_LENGTH]
    prompt_text = PARSE_MESSAGES_PROMPT.format(records=records_text)
    
    try:
        stream = client.chat.completions.create(
            model=ZHIPU_CHAT_MODEL,
            messages=[
                {"role": "system", "content": PARSE_MESSAGES_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0,
            stream=True,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        resp_content = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                if chunk.choices[0].delta.content is not None:
                    resp_content += chunk.choices[0].delta.content
        resp_content = resp_content.strip()
        if resp_content.startswith("```"):
            resp_content = resp_content.replace("```json", "").replace("```", "").strip()
        
        structured_data = json.loads(resp_content)
        raw_messages = structured_data.get("messages", [])
        
        parsed_messages = []
        for msg in raw_messages:
            if not isinstance(msg, dict):
                continue
            content = msg.get("content", "").strip()
            if len(content) >= 2:
                parsed_messages.append({
                    "content": content,
                    "position": _standardize_position(msg.get("position", "未知")),
                    "color": _standardize_color(msg.get("color", "未知"))
                })
        
        print(f"📋 解析到 {len(parsed_messages)} 条消息")
        return {
            "parse_success": True,
            "parsed_messages": parsed_messages,
        }
        
    except Exception as e:
        print(f"❌ 解析消息失败: {e}")
        return {
            "parse_success": False,
            "parsed_messages": _emergency_extract(records),
        }


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


def _emergency_extract(record: str) -> list[dict[str, str]]:
    """紧急提取方法：当AI解析失败时使用"""
    import re
    record_clean = re.sub(r"思考过程:|性能指标:|总推理时间:|首 Token 延迟|思考完成延迟", "", record)
    record_clean = re.sub(r"[^\u4e00-\u9fff\w\s\.,，。！？；：""''💪~]", "", record_clean)
    
    sentences = re.split(r"[。！？；：\n]", record_clean)
    messages = []
    
    for sent in sentences:
        sent = sent.strip().strip('"').strip("'")
        if len(sent) >= 2 and not sent.isdigit():
            position = "右侧有头像" if "芸苔" in sent or "💪" in sent or "~" in sent else "左侧有头像"
            color = "红色" if position == "右侧有头像" else "白色"
            messages.append({"content": sent, "position": position, "color": color})
    
    return messages

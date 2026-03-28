"""
消息工具模块
============

处理消息解析、归属判断、回复生成等核心功能。

主要功能:
    - parse_messages: 解析聊天记录，提取消息
    - determine_message_ownership: 判断消息归属
    - generate_reply: 生成回复内容
    - check_new_messages: 检查是否有新消息

内部函数:
    - _standardize_position: 标准化头像位置
    - _standardize_color: 标准化气泡颜色
    - _emergency_extract: 紧急提取方法

使用示例:
    >>> from yuntai.tools import parse_messages, generate_reply
    >>> messages = parse_messages(record, zhipu_client)
    >>> reply = generate_reply(latest_msg, history, zhipu_client)
"""
from __future__ import annotations

import json
import logging
import re

from zhipuai import ZhipuAI

from yuntai.tools.similarity import is_similar
from yuntai.core.config import (
    ZHIPU_CHAT_MODEL,
    SIMILARITY_THRESHOLD,
    SIMILARITY_CHECK_NEW_THRESHOLD,
    PARSE_MAX_TOKENS,
    REPLY_MAX_TOKENS,
    REPLY_TEMPERATURE,
    REPLY_HISTORY_LIMIT,
    MIN_MESSAGE_LENGTH,
)

from yuntai.prompts import (
    PARSE_MESSAGES_SYSTEM_PROMPT,
    PARSE_MESSAGES_PROMPT,
    PARSE_MESSAGES_MAX_LENGTH,
    REPLY_NODE_SYSTEM_PROMPT,
    REPLY_NODE_USER_PROMPT,
)

logger = logging.getLogger(__name__)


def parse_messages(record: str, zhipu_client: ZhipuAI) -> list[dict[str, str]]:
    """
    解析聊天记录，提取消息
    
    使用智谱 AI 模型从原始聊天记录中智能提取结构化消息。
    如果 AI 解析失败，会自动降级到紧急提取方法。
    
    Args:
        record: 原始聊天记录文本
        zhipu_client: 智谱 AI 客户端实例
    
    Returns:
        消息列表，每个消息包含 content, position, color 字段
    """
    if not record or len(record.strip()) < 10:
        logger.debug("聊天记录为空或过短，跳过解析")
        return []
    
    records_text = record[:PARSE_MESSAGES_MAX_LENGTH]
    prompt_text = PARSE_MESSAGES_PROMPT.format(records=records_text)
    
    try:
        stream = zhipu_client.chat.completions.create(
            model=ZHIPU_CHAT_MODEL,
            messages=[
                {"role": "system", "content": PARSE_MESSAGES_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0,
            stream=True,
            max_tokens=PARSE_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        resp_content = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content is not None:
                    resp_content += delta.content
        
        resp_content = resp_content.strip()
        
        if resp_content.startswith("```"):
            resp_content = resp_content.replace("```json", "").replace("```", "").strip()
        
        structured_data = json.loads(resp_content)
        messages = structured_data.get("messages", [])
        
        final_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                logger.warning("跳过非字典类型的消息: %s", type(msg))
                continue
            
            content = msg.get("content", "").strip()
            position = msg.get("position", "未知")
            color = msg.get("color", "未知")
            
            if len(content) >= MIN_MESSAGE_LENGTH and not any(
                existing["content"] == content for existing in final_messages
            ):
                final_messages.append({
                    "content": content,
                    "position": _standardize_position(position),
                    "color": _standardize_color(color)
                })
        
        logger.info("成功解析 %d 条消息", len(final_messages))
        return final_messages
    
    except json.JSONDecodeError as e:
        logger.error("JSON解析失败: %s", str(e))
        print(f"解析消息失败: JSON格式错误")
        return _emergency_extract(record)
    except Exception as e:
        logger.warning("解析消息失败: %s", str(e), exc_info=True)
        print(f"解析消息失败: {e}")
        return _emergency_extract(record)


def _standardize_position(position: str) -> str:
    """
    标准化头像位置
    
    将各种形式的位置描述统一为标准格式。
    
    Args:
        position: 原始位置描述
        
    Returns:
        标准化后的位置（"左侧有头像" | "右侧有头像" | "未知"）
    """
    if not position or position == "未知":
        return "未知"
    
    position_lower = position.lower()
    if "左" in position_lower:
        return "左侧有头像"
    elif "右" in position_lower:
        return "右侧有头像"
    
    return "未知"


def _standardize_color(color: str) -> str:
    """
    标准化气泡颜色
    
    将各种颜色描述统一为标准颜色名称。
    
    Args:
        color: 原始颜色描述
        
    Returns:
        标准化后的颜色名称
    """
    if not color or color == "未知":
        return "未知"
    
    color_lower = color.lower()
    color_map = {
        "粉红": "粉色", "红": "红色", "蓝": "蓝色", "绿": "绿色",
        "紫": "紫色", "黑": "黑色", "灰": "灰色", "橙": "橙色", 
        "黄": "黄色", "白": "白色"
    }
    
    for key, val in color_map.items():
        if key in color_lower:
            return val
    
    return "未知"


def _emergency_extract(record: str) -> list[dict[str, str]]:
    """
    紧急提取方法：当 AI 解析失败时使用
    
    使用正则表达式和简单规则从原始文本中提取消息，
    作为 AI 解析失败时的降级方案。
    
    Args:
        record: 原始聊天记录文本
        
    Returns:
        提取的消息列表
    """
    logger.info("使用紧急提取方法处理聊天记录")
    
    record_clean = re.sub(
        r"思考过程:|性能指标:|总推理时间:|首 Token 延迟|思考完成延迟", 
        "", 
        record
    )
    record_clean = re.sub(
        r"[^\u4e00-\u9fff\w\s\.,，。！？；：\"''💪~]", 
        "", 
        record_clean
    )
    
    sentences = re.split(r"[。！？；：\n]", record_clean)
    final_messages = []
    
    for sent in sentences:
        sent = sent.strip().strip('"').strip("'")
        
        if (len(sent) >= MIN_MESSAGE_LENGTH 
            and not sent.isdigit() 
            and not sent.startswith("20:")
            and "气泡" not in sent 
            and "头像" not in sent 
            and "消息" not in sent):
            
            if not any(existing["content"] == sent for existing in final_messages):
                position = "右侧有头像" if "芸苔" in sent or "💪" in sent or "~" in sent else "左侧有头像"
                color = "红色" if position == "右侧有头像" else "白色"
                final_messages.append({
                    "content": sent,
                    "position": position,
                    "color": color
                })
    
    logger.info("紧急提取完成，共提取 %d 条消息", len(final_messages))
    return final_messages


def determine_message_ownership(
    messages: list[dict[str, str]],
    my_messages_list: list[str],
    other_messages_list: list[str]
) -> tuple[list[str], list[str]]:
    """
    判断消息归属
    
    根据已知的历史消息、头像位置和气泡颜色，
    判断每条消息属于我方还是对方。
    
    Args:
        messages: 解析后的消息列表
        my_messages_list: 已知的我方消息列表
        other_messages_list: 已知的对方消息列表
    
    Returns:
        元组 (对方消息列表, 我方消息列表)
    """
    other_messages = []
    my_messages = []
    
    for msg in messages:
        content = msg.get("content", "").strip()
        position = msg.get("position", "")
        color = msg.get("color", "")
        
        if not content or len(content) < MIN_MESSAGE_LENGTH:
            continue
        
        is_my_message = False
        for my_msg in my_messages_list:
            if is_similar(content, my_msg, threshold=SIMILARITY_THRESHOLD):
                is_my_message = True
                my_messages.append(content)
                break
        
        if is_my_message:
            continue
        
        is_other_message = False
        for other_msg in other_messages_list:
            if is_similar(content, other_msg, threshold=SIMILARITY_THRESHOLD):
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
    
    logger.debug("消息归属判断完成: 对方%d条, 我方%d条", len(other_messages), len(my_messages))
    return other_messages, my_messages


def generate_reply(
    latest_message: str,
    history_messages: list[str],
    zhipu_client: ZhipuAI,
    system_prompt: str = ""
) -> str:
    """
    生成回复内容
    
    根据最新消息和历史对话，使用 AI 智能生成合适的回复。
    
    Args:
        latest_message: 最新收到的消息
        history_messages: 历史消息列表
        zhipu_client: 智谱 AI 客户端实例
        system_prompt: 可选的自定义系统提示词
    
    Returns:
        生成的回复内容，失败时返回空字符串
    """
    if not latest_message:
        logger.debug("最新消息为空，跳过回复生成")
        return ""
    
    history_prompt = ""
    if history_messages:
        history_prompt = "\n\n=== 历史对话（按时间顺序，从旧到新）===\n"
        for i, msg in enumerate(history_messages[-REPLY_HISTORY_LIMIT:], 1):
            preview = msg[:50] + "..." if len(msg) > 50 else msg
            history_prompt += f"{i}. {preview}\n"
    
    user_prompt = REPLY_NODE_USER_PROMPT.format(
        latest_message=latest_message,
        history_prompt=history_prompt
    )
    
    try:
        stream = zhipu_client.chat.completions.create(
            model=ZHIPU_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or REPLY_NODE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=REPLY_TEMPERATURE,
            stream=True,
            max_tokens=REPLY_MAX_TOKENS
        )
        
        reply = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content is not None:
                    reply += delta.content
        
        reply = reply.strip()
        
        if "。" in reply:
            reply = reply.split("。")[0] + "。"
        
        logger.debug("成功生成回复: %s...", reply[:30])
        return reply
    
    except Exception as e:
        logger.error("生成回复失败: %s", str(e), exc_info=True)
        print(f"生成回复失败: {e}")
        return ""


def check_new_messages(
    current_other_messages: list[str],
    previous_other_messages: list[str],
    my_messages_list: list[str]
) -> tuple[bool, list[str]]:
    """
    检查是否有新消息
    
    通过相似度比较，检测当前消息列表中是否有之前未出现过的新消息。
    
    Args:
        current_other_messages: 当前解析的对方消息列表
        previous_other_messages: 之前已知的对方消息列表
        my_messages_list: 已知的我方消息列表（用于排除）
    
    Returns:
        元组 (是否有新消息, 新消息列表)
    """
    new_messages = []
    
    for msg in current_other_messages:
        is_new = True
        
        for existing_msg in previous_other_messages:
            if is_similar(msg, existing_msg, threshold=SIMILARITY_CHECK_NEW_THRESHOLD):
                is_new = False
                break
        
        if is_new:
            for my_msg in my_messages_list:
                if is_similar(msg, my_msg, threshold=SIMILARITY_CHECK_NEW_THRESHOLD):
                    is_new = False
                    break
        
        if is_new:
            new_messages.append(msg)
    
    has_new = len(new_messages) > 0
    if has_new:
        logger.info("检测到 %d 条新消息", len(new_messages))
    
    return has_new, new_messages

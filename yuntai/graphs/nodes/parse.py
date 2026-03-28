"""
解析消息节点模块
================

本模块负责解析聊天记录，使用智谱 AI 模型将非结构化文本转换为结构化消息列表。

主要功能：
    - 使用 AI 模型解析聊天记录
    - 标准化消息位置和颜色
    - 提供紧急提取方法作为后备

函数说明：
    - parse_messages: 解析消息节点函数
    - _standardize_position: 标准化头像位置
    - _standardize_color: 标准化气泡颜色
    - _emergency_extract: 紧急提取方法

使用示例：
    >>> from yuntai.graphs.nodes import parse_messages
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = parse_messages(state)
"""
import json
import logging

from yuntai.graphs.state import ReplyState
from yuntai.models import get_zhipu_client
from yuntai.core.config import ZHIPU_CHAT_MODEL
from yuntai.prompts import (
    PARSE_MESSAGES_SYSTEM_PROMPT,
    PARSE_MESSAGES_PROMPT,
    PARSE_MESSAGES_MAX_LENGTH,
)

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def parse_messages(state: ReplyState) -> dict[str, object]:
    """
    解析消息节点
    
    使用智谱 AI 模型将非结构化聊天记录转换为结构化消息列表。
    
    输入状态字段:
        - extracted_records: 提取的原始聊天记录
    
    输出状态字段:
        - parse_success: 解析是否成功
        - parsed_messages: 解析后的消息列表
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict: 包含解析结果的字典
    
    使用示例：
        >>> result = parse_messages(state)
        >>> messages = result.get("parsed_messages", [])
    """
    # 获取聊天记录
    records = state["extracted_records"]
    
    # 检查记录是否为空
    if not records or len(records.strip()) < 10:
        logger.debug("聊天记录为空或过短")
        print("⏭️ 聊天记录为空")
        return {
            "parse_success": False,
            "parsed_messages": [],
        }
    
    logger.debug("开始解析聊天记录，长度: %d", len(records))
    
    # 获取智谱 AI 客户端
    client = get_zhipu_client()
    
    # 截断过长的记录
    records_text = records[:PARSE_MESSAGES_MAX_LENGTH]
    
    # 构建提示词
    prompt_text = PARSE_MESSAGES_PROMPT.format(records=records_text)
    
    try:
        # 调用 AI 模型解析
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
        
        # 收集流式响应
        resp_content = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                if chunk.choices[0].delta.content is not None:
                    resp_content += chunk.choices[0].delta.content
        
        # 清理响应内容
        resp_content = resp_content.strip()
        if resp_content.startswith("```"):
            resp_content = resp_content.replace("```json", "").replace("```", "").strip()
        
        # 解析 JSON
        structured_data = json.loads(resp_content)
        raw_messages = structured_data.get("messages", [])
        
        # 处理消息列表
        parsed_messages = []
        for msg in raw_messages:
            if not isinstance(msg, dict):
                continue
            
            # 提取并清理内容
            content = msg.get("content", "").strip()
            if len(content) >= 2:
                parsed_messages.append({
                    "content": content,
                    "position": _standardize_position(msg.get("position", "未知")),
                    "color": _standardize_color(msg.get("color", "未知"))
                })
        
        logger.debug("解析成功，消息数: %d", len(parsed_messages))
        print(f"📋 解析到 {len(parsed_messages)} 条消息")
        
        return {
            "parse_success": True,
            "parsed_messages": parsed_messages,
        }
        
    except Exception as e:
        # 解析失败，使用紧急提取方法
        logger.warning("AI 解析失败: %s，使用紧急提取", str(e))
        print(f"❌ 解析消息失败: {e}")
        
        return {
            "parse_success": False,
            "parsed_messages": _emergency_extract(records),
        }


def _standardize_position(position: str) -> str:
    """
    标准化头像位置
    
    将各种位置描述统一为标准格式。
    
    Args:
        position: 原始位置描述
    
    Returns:
        str: 标准化后的位置（"左侧有头像"、"右侧有头像" 或 "未知"）
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
    
    将各种颜色描述统一为标准格式。
    
    Args:
        color: 原始颜色描述
    
    Returns:
        str: 标准化后的颜色
    """
    if not color or color == "未知":
        return "未知"
    
    color_lower = color.lower()
    
    # 颜色映射表
    color_map = {
        "粉红": "粉色",
        "红": "红色",
        "蓝": "蓝色",
        "绿": "绿色",
        "紫": "紫色",
        "黑": "黑色",
        "灰": "灰色",
        "橙": "橙色",
        "黄": "黄色",
        "白": "白色"
    }
    
    # 遍历映射表查找匹配
    for key, val in color_map.items():
        if key in color_lower:
            return val
    
    return "未知"


def _emergency_extract(record: str) -> list[dict[str, str]]:
    """
    紧急提取方法
    
    当 AI 解析失败时使用，基于规则提取消息。
    
    Args:
        record: 原始聊天记录
    
    Returns:
        list[dict[str, str]]: 提取的消息列表
    """
    import re
    
    logger.debug("使用紧急提取方法")
    
    # 清理记录
    record_clean = re.sub(r"思考过程:|性能指标:|总推理时间:|首 Token 延迟|思考完成延迟", "", record)
    record_clean = re.sub(r"[^\u4e00-\u9fff\w\s\.,，。！？；：""''💪~]", "", record_clean)
    
    # 分割句子
    sentences = re.split(r"[。！？；：\n]", record_clean)
    messages = []
    
    for sent in sentences:
        # 清理句子
        sent = sent.strip().strip('"').strip("'")
        
        # 过滤无效句子
        if len(sent) >= 2 and not sent.isdigit():
            # 根据特征判断消息归属
            if "芸苔" in sent or "💪" in sent or "~" in sent:
                position = "右侧有头像"
                color = "红色"
            else:
                position = "左侧有头像"
                color = "白色"
            
            messages.append({
                "content": sent,
                "position": position,
                "color": color
            })
    
    return messages

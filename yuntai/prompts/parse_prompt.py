"""
消息解析提示词模块
==================

提供消息解析场景的提示词模板，用于解析聊天记录、提取消息内容。

主要组件:
    - PARSE_MESSAGES_SYSTEM_PROMPT: 消息解析系统提示词
    - PARSE_MESSAGES_PROMPT: 消息解析提示词模板
    - PARSE_MESSAGES_MAX_LENGTH: 最大解析长度

使用场景:
    - 解析聊天记录
    - 提取消息内容和属性
"""
import logging

logger = logging.getLogger(__name__)

PARSE_MESSAGES_SYSTEM_PROMPT = "你必须只输出符合要求的JSON，不要加任何额外文字！"

PARSE_MESSAGES_PROMPT = """从以下聊天记录中提取所有有效消息，返回JSON格式。

聊天记录：
{records}

返回格式要求：
{{
  "messages": [
    {{"content": "消息内容", "position": "左侧有头像/右侧有头像/未知", "color": "白色/红色/蓝色/绿色/粉色/紫色/黑色/灰色/橙色/黄色/未知"}}
  ]
}}

重要：
1. 只输出JSON，不要有其他文字
2. position只能是：左侧有头像、右侧有头像、未知
3. 消息内容要完整，不要截断"""

PARSE_MESSAGES_MAX_LENGTH = 2000

__all__ = [
    "PARSE_MESSAGES_SYSTEM_PROMPT",
    "PARSE_MESSAGES_PROMPT",
    "PARSE_MESSAGES_MAX_LENGTH",
]

"""
工具函数模块
============

提供项目通用的工具函数，包括时间工具、手机操作工具、聊天工具等。

主要组件:
    - TimeTool: 时间工具类
    - open_app_tool: 打开 APP 工具函数
    - execute_phone_operation: 执行手机操作工具函数
    - extract_chat_records_tool: 提取聊天记录工具函数
    - send_message_tool: 发送消息工具函数
    - get_current_time_info: 获取当前时间信息
    - get_history_context: 获取历史上下文
    - parse_messages: 解析消息
    - determine_message_ownership: 判断消息归属
    - generate_reply: 生成回复
    - check_new_messages: 检查新消息
    - is_similar: 判断文本相似性
    - calculate_similarity: 计算相似度
    - prepare_callbacks: 准备回调处理器

功能特点:
    - 时间信息获取和格式化
    - 手机操作封装
    - 消息解析和处理
    - 文本相似度计算
    - 回调处理器管理
"""
import logging

logger = logging.getLogger(__name__)

from .time_tool import TimeTool
from .phone_tools import (
    open_app_tool,
    execute_phone_operation,
    extract_chat_records_tool,
    send_message_tool,
)
from .chat_tools import (
    get_current_time_info,
    get_history_context,
)
from .message_tools import (
    parse_messages,
    determine_message_ownership,
    generate_reply,
    check_new_messages,
)
from .similarity import (
    is_similar,
    calculate_similarity,
    clean_text,
    DEFAULT_SIMILARITY_THRESHOLD,
)
from .callback_utils import (
    prepare_callbacks,
    prepare_callbacks_with_manager,
    get_global_callbacks,
)

__all__ = [
    "TimeTool",
    "open_app_tool",
    "execute_phone_operation",
    "extract_chat_records_tool",
    "send_message_tool",
    "get_current_time_info",
    "get_history_context",
    "parse_messages",
    "determine_message_ownership",
    "generate_reply",
    "check_new_messages",
    "is_similar",
    "calculate_similarity",
    "clean_text",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "prepare_callbacks",
    "prepare_callbacks_with_manager",
    "get_global_callbacks",
]

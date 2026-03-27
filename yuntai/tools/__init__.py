"""
工具函数模块

提供项目通用的工具函数，包括：
- 时间工具
- 手机操作工具
- 聊天工具
- 消息处理工具
- 相似度计算工具
- 回调处理工具
"""

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

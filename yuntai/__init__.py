#!/usr/bin/env python3
"""
Yuntai - 芸薹手机助手模块包
"""

# 导出配置
from .config import (
    Color, SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    MAX_HISTORY_LENGTH, MAX_CYCLE_TIMES, MAX_RETRY_TIMES, WAIT_INTERVAL,
    CONNECTION_CONFIG_FILE
)

# 导出管理器类
from .connection_manager import ConnectionManager
from .file_manager import FileManager
from .agent_executor import AgentExecutor
from .utils import Utils

# 注意：TaskRecognizer 和 SmartContinuousReplyManager 需要客户端，所以不能在 __init__ 中实例化
# 只导出类本身
from .task_recognizer import TaskRecognizer
from .reply_manager import SmartContinuousReplyManager

# ZHIPU_CLIENT 需要在主文件中初始化
ZHIPU_CLIENT = None

__all__ = [
    'Color', 'SHORTCUTS', 'ZHIPU_API_KEY', 'ZHIPU_CLIENT',
    'CONVERSATION_HISTORY_FILE', 'RECORD_LOGS_DIR', 'FOREVER_MEMORY_FILE',
    'MAX_HISTORY_LENGTH', 'MAX_CYCLE_TIMES', 'MAX_RETRY_TIMES', 'WAIT_INTERVAL',
    'CONNECTION_CONFIG_FILE',
    'ConnectionManager', 'FileManager', 'TaskRecognizer',
    'SmartContinuousReplyManager', 'AgentExecutor', 'Utils'
]
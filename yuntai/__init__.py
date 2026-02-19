#!/usr/bin/env python3
"""
Yuntai - 芸薹手机助手模块包
使用 LangChain 重构版本
"""

# 导出配置
from .config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    MAX_HISTORY_LENGTH, MAX_CYCLE_TIMES, MAX_RETRY_TIMES, WAIT_INTERVAL,
    CONNECTION_CONFIG_FILE
)

# 导出管理器类
from .connection_manager import ConnectionManager
from .file_manager import FileManager
from .agent_executor import AgentExecutor
from .utils import Utils

# 重构模块
from .gui_view import GUIView
from .gui_controller import GUIController
from .task_manager import TaskManager
from .main_app import MainApp
from .output_capture import SimpleOutputCapture
from .multimodal_processor import MultimodalProcessor
from .multimodal_other import MultimodalOther, ImagePreviewWindow, VideoPreviewWindow
from .audio_processor import AudioProcessor

# TTS 工具函数
from .utils import (
    load_synthesized_files,
    get_current_tts_status,
    cleanup_tts_resources
)

# 时间工具
from .tools import TimeTool

# 新模块 - LangChain 重构
from .models import (
    get_judgement_model,
    get_chat_model,
    get_phone_model,
    get_zhipu_client,
)

from .agents import (
    JudgementAgent,
    ChatAgent,
    PhoneAgent,
    ReplyAgent,
)

from .chains import (
    TaskChain,
    ReplyChain,
)

from .memory import ConversationMemoryManager

from .prompts import (
    TASK_JUDGEMENT_PROMPT,
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
    CHAT_SYSTEM_PROMPT,
)

# ZHIPU_CLIENT 需要在主文件中初始化
ZHIPU_CLIENT = None

__all__ = [
    # 原来的配置
    'SHORTCUTS', 'ZHIPU_API_KEY', 'ZHIPU_CLIENT',
    'CONVERSATION_HISTORY_FILE', 'RECORD_LOGS_DIR', 'FOREVER_MEMORY_FILE',
    'MAX_HISTORY_LENGTH', 'MAX_CYCLE_TIMES', 'MAX_RETRY_TIMES', 'WAIT_INTERVAL',
    'CONNECTION_CONFIG_FILE',

    # 原来的管理器类
    'ConnectionManager', 'FileManager', 'AgentExecutor', 'Utils',

    # 重构模块
    "GUIView",
    "GUIController",
    "TaskManager",
    "MainApp",
    "SimpleOutputCapture",

    # 工具函数
    "load_synthesized_files",
    "get_current_tts_status",
    "cleanup_tts_resources",

    # 时间工具
    "TimeTool",

    # 多模态处理器
    "MultimodalProcessor",
    "MultimodalOther",
    "ImagePreviewWindow",
    "VideoPreviewWindow",

    # 音频处理
    "AudioProcessor",

    # 新模块 - LangChain 重构
    "get_judgement_model",
    "get_chat_model",
    "get_phone_model",
    "get_zhipu_client",

    "JudgementAgent",
    "ChatAgent",
    "PhoneAgent",
    "ReplyAgent",

    "TaskChain",
    "ReplyChain",

    "ConversationMemoryManager",

    "TASK_JUDGEMENT_PROMPT",
    "TASK_TYPE_FREE_CHAT",
    "TASK_TYPE_BASIC_OPERATION",
    "TASK_TYPE_SINGLE_REPLY",
    "TASK_TYPE_CONTINUOUS_REPLY",
    "TASK_TYPE_COMPLEX_OPERATION",
    "CHAT_SYSTEM_PROMPT",
]

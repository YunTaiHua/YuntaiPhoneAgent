#!/usr/bin/env python3
"""
Yuntai - 芸薹手机助手模块包
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

# 注意：TaskRecognizer 和 SmartContinuousReplyManager 需要客户端，所以不能在 __init__ 中实例化
# 只导出类本身
from .task_recognizer import TaskRecognizer
from .reply_manager import SmartContinuousReplyManager

# 重构模块
from .gui_view import GUIView
from .gui_controller import GUIController
from .task_manager import TaskManager
from .main_app import MainApp
from .agent_core import TerminableContinuousReplyManager
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

# ZHIPU_CLIENT 需要在主文件中初始化
ZHIPU_CLIENT = None

__all__ = [
    # 原来的配置
    'SHORTCUTS', 'ZHIPU_API_KEY', 'ZHIPU_CLIENT',
    'CONVERSATION_HISTORY_FILE', 'RECORD_LOGS_DIR', 'FOREVER_MEMORY_FILE',
    'MAX_HISTORY_LENGTH', 'MAX_CYCLE_TIMES', 'MAX_RETRY_TIMES', 'WAIT_INTERVAL',
    'CONNECTION_CONFIG_FILE',

    # 原来的管理器类
    'ConnectionManager', 'FileManager', 'TaskRecognizer',
    'SmartContinuousReplyManager', 'AgentExecutor', 'Utils',

    # 重构模块
    "GUIView",
    "GUIController",
    "TaskManager",
    "MainApp",
    "TerminableContinuousReplyManager",
    "SimpleOutputCapture",

    # 工具函数
    "load_synthesized_files",
    "get_current_tts_status",
    "cleanup_tts_resources",

    # 多模态处理器
    "MultimodalProcessor",
    "MultimodalOther",
    "ImagePreviewWindow",
    "VideoPreviewWindow",

    # 音频处理
    "AudioProcessor",
]
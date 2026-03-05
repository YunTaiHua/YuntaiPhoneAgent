#!/usr/bin/env python3
"""
Yuntai - 芸薹手机助手模块包
使用 LangChain 重构版本
"""

# 导出配置 - 这些不会触发循环导入
from yuntai.core.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    MAX_HISTORY_LENGTH, MAX_CYCLE_TIMES, MAX_RETRY_TIMES, WAIT_INTERVAL,
    CONNECTION_CONFIG_FILE
)

# 导出管理器类
from yuntai.services.connection_manager import ConnectionManager
from yuntai.services.file_manager import FileManager
from yuntai.core.agent_executor import AgentExecutor
from yuntai.core.utils import Utils

# ZHIPU_CLIENT 需要在主文件中初始化
ZHIPU_CLIENT = None

# TTS 工具函数
from yuntai.core.utils import (
    load_synthesized_files,
    get_current_tts_status,
    cleanup_tts_resources
)

# 时间工具
from yuntai.tools import TimeTool

# 新模块 - LangChain 重构
from yuntai.models import (
    get_judgement_model,
    get_chat_model,
    get_phone_model,
    get_zhipu_client,
)

from yuntai.agents import (
    JudgementAgent,
    ChatAgent,
    PhoneAgent,
)

from yuntai.chains import (
    TaskChain,
    ReplyChain,
)

from yuntai.memory import ConversationMemoryManager

from yuntai.prompts import (
    TASK_JUDGEMENT_PROMPT,
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
    CHAT_SYSTEM_PROMPT,
)


# ==================== 延迟导入 ====================
# 以下模块使用延迟导入，避免循环依赖

def __getattr__(name):
    """延迟导入机制，避免循环依赖"""
    if name == 'GUIView':
        from yuntai.gui.gui_view import GUIView
        return GUIView
    elif name == 'GUIController':
        from yuntai.gui.gui_controller import GUIController
        return GUIController
    elif name == 'TaskManager':
        from yuntai.services.task_manager import TaskManager
        return TaskManager
    elif name == 'MainApp':
        from yuntai.core.main_app import MainApp
        return MainApp
    elif name == 'SimpleOutputCapture':
        from yuntai.gui.output_capture import SimpleOutputCapture
        return SimpleOutputCapture
    elif name == 'MultimodalProcessor':
        from yuntai.processors.multimodal_processor import MultimodalProcessor
        return MultimodalProcessor
    elif name == 'MediaGenerator':
        from yuntai.processors.media_generator import MediaGenerator
        return MediaGenerator
    elif name == 'ImagePreviewWindow':
        from yuntai.views.dynamic import ImagePreviewWindow
        return ImagePreviewWindow
    elif name == 'VideoPreviewWindow':
        from yuntai.views.dynamic import VideoPreviewWindow
        return VideoPreviewWindow
    elif name == 'AudioProcessor':
        from yuntai.processors.audio_processor import AudioProcessor
        return AudioProcessor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    "MediaGenerator",
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

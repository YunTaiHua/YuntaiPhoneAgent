"""
Yuntai - 芸薹手机助手模块包
============================

本模块是芸薹手机助手的核心包，提供手机自动化操作、智能对话、语音合成等功能。

主要功能模块：
    - agents: 智能代理模块，包含任务判断、聊天、手机操作等 Agent
    - callbacks: LangChain 回调处理器，支持流式输出、日志记录、记忆管理
    - chains: 任务链和回复链，用于编排复杂的工作流
    - core: 核心模块，包含配置管理、应用主入口、工具函数
    - graphs: 状态图模块，用于处理复杂的对话流程
    - gui: 图形界面模块，提供 PyQt5 GUI 控制器和视图
    - handlers: 处理器模块，处理连接、动态任务、系统事件、TTS 等
    - managers: 管理器模块，包含 TTS 引擎、音频处理、数据库管理
    - memory: 记忆管理模块，管理对话历史和永久记忆
    - models: 模型模块，封装智谱 AI 模型的调用
    - processors: 处理器模块，处理音频、媒体生成、多模态输入
    - prompts: 提示词模块，包含各种场景的提示词模板
    - services: 服务模块，提供连接管理、文件管理、任务管理
    - tools: 工具模块，提供各种实用工具函数
    - views: 视图模块，包含各种 GUI 视图组件

使用示例：
    >>> from yuntai import MainApp, ConnectionManager, FileManager
    >>> from yuntai import ChatAgent, PhoneAgent, JudgementAgent
    >>> 
    >>> # 初始化应用
    >>> app = MainApp()
    >>> app.run()

注意事项：
    - 使用前需要配置 .env 文件中的 ZHIPU_API_KEY
    - 部分功能需要安装 GPT-SoVITS 进行语音合成
    - 手机操作功能需要连接 ADB 或 HDC 设备

版本历史：
    - v1.3.5: 当前版本，使用 LangChain 重构
"""

import logging

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# ==================== 配置导出 ====================
# 导出配置常量，这些不会触发循环导入

from yuntai.core.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    MAX_HISTORY_LENGTH, MAX_CYCLE_TIMES, MAX_RETRY_TIMES, WAIT_INTERVAL,
    CONNECTION_CONFIG_FILE
)

# ==================== 管理器类导出 ====================
# 导出核心管理器类，用于外部调用

from yuntai.services.connection_manager import ConnectionManager
from yuntai.services.file_manager import FileManager
from yuntai.core.agent_executor import AgentExecutor
from yuntai.core.utils import Utils

# ZHIPU_CLIENT 需要在主文件中初始化
# 这是一个全局变量，用于存储智谱 AI 客户端实例
ZHIPU_CLIENT = None

# ==================== TTS 工具函数导出 ====================
# 导出 TTS 相关的工具函数

from yuntai.core.utils import (
    load_synthesized_files,
    get_current_tts_status,
    cleanup_tts_resources
)

# ==================== 时间工具导出 ====================
# 导出时间工具类

from yuntai.tools import TimeTool

# ==================== LangChain 重构模块导出 ====================
# 导出 LangChain 重构后的模块

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


# ==================== 延迟导入机制 ====================
# 以下模块使用延迟导入，避免循环依赖
# 当访问这些属性时才会真正导入对应的模块

def __getattr__(name: str):
    """
    延迟导入机制，避免循环依赖
    
    当访问模块中未直接定义的属性时，此函数会被调用，
    实现按需导入，避免启动时加载所有模块。
    
    Args:
        name: 请求的属性名称
        
    Returns:
        对应的模块或类
        
    Raises:
        AttributeError: 当请求的属性不存在时抛出
        
    使用示例：
        >>> from yuntai import MainApp  # 此时才会导入 MainApp
    """
    # GUI 相关模块延迟导入
    if name == 'GUIView':
        from yuntai.gui.gui_view import GUIView
        logger.debug("延迟导入 GUIView")
        return GUIView
    elif name == 'GUIController':
        from yuntai.gui.gui_controller import GUIController
        logger.debug("延迟导入 GUIController")
        return GUIController
    # 任务管理器延迟导入
    elif name == 'TaskManager':
        from yuntai.services.task_manager import TaskManager
        logger.debug("延迟导入 TaskManager")
        return TaskManager
    # 主应用延迟导入
    elif name == 'MainApp':
        from yuntai.core.main_app import MainApp
        logger.debug("延迟导入 MainApp")
        return MainApp
    # 多模态处理器延迟导入
    elif name == 'MultimodalProcessor':
        from yuntai.processors.multimodal_processor import MultimodalProcessor
        logger.debug("延迟导入 MultimodalProcessor")
        return MultimodalProcessor
    # 媒体生成器延迟导入
    elif name == 'MediaGenerator':
        from yuntai.processors.media_generator import MediaGenerator
        logger.debug("延迟导入 MediaGenerator")
        return MediaGenerator
    # 图像预览窗口延迟导入
    elif name == 'ImagePreviewWindow':
        from yuntai.views.dynamic import ImagePreviewWindow
        logger.debug("延迟导入 ImagePreviewWindow")
        return ImagePreviewWindow
    # 视频预览窗口延迟导入
    elif name == 'VideoPreviewWindow':
        from yuntai.views.dynamic import VideoPreviewWindow
        logger.debug("延迟导入 VideoPreviewWindow")
        return VideoPreviewWindow
    # 音频处理器延迟导入
    elif name == 'AudioProcessor':
        from yuntai.processors.audio_processor import AudioProcessor
        logger.debug("延迟导入 AudioProcessor")
        return AudioProcessor
    
    # 属性不存在时抛出异常
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ==================== 模块公开接口 ====================
# 定义模块的公开接口，用于 from yuntai import * 时导出的内容

__all__ = [
    # 原来的配置常量
    'SHORTCUTS', 'ZHIPU_API_KEY', 'ZHIPU_CLIENT',
    'CONVERSATION_HISTORY_FILE', 'RECORD_LOGS_DIR', 'FOREVER_MEMORY_FILE',
    'MAX_HISTORY_LENGTH', 'MAX_CYCLE_TIMES', 'MAX_RETRY_TIMES', 'WAIT_INTERVAL',
    'CONNECTION_CONFIG_FILE',

    # 原来的管理器类
    'ConnectionManager', 'FileManager', 'AgentExecutor', 'Utils',

    # 重构模块 - GUI 相关
    "GUIView",
    "GUIController",
    "TaskManager",
    "MainApp",

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

    # Agent 类
    "JudgementAgent",
    "ChatAgent",
    "PhoneAgent",

    # Chain 类
    "TaskChain",
    "ReplyChain",

    # 记忆管理
    "ConversationMemoryManager",

    # 提示词常量
    "TASK_JUDGEMENT_PROMPT",
    "TASK_TYPE_FREE_CHAT",
    "TASK_TYPE_BASIC_OPERATION",
    "TASK_TYPE_SINGLE_REPLY",
    "TASK_TYPE_CONTINUOUS_REPLY",
    "TASK_TYPE_COMPLEX_OPERATION",
    "CHAT_SYSTEM_PROMPT",
]

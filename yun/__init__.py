"""
yun - Phone Agent 重构模块包
"""

from .gui_view import GUIView
from .gui_controller import GUIController
from .task_manager import TaskManager
from .main_app import MainApp
from .agent_core import TerminableContinuousReplyManager
from .output_capture import SimpleOutputCapture
from .multimodal_processor import MultimodalProcessor
from .multimodal_other import MultimodalOther, ImagePreviewWindow, VideoPreviewWindow
from .audio_processor import AudioProcessor
from .utils import (
    load_synthesized_files,
    get_current_tts_status,
    cleanup_tts_resources
)

# 导出配置
from .config import (
    # 基础路径
    PROJECT_ROOT,
    CURRENT_DIR,

    # GPT-SoVITS 配置
    GPT_SOVITS_ROOT,
    GPT_MODEL_DIR,
    SOVITS_MODEL_DIR,
    REF_AUDIO_ROOT,
    REF_TEXT_ROOT,
    BERT_MODEL_PATH,
    HUBERT_MODEL_PATH,
    TTS_OUTPUT_DIR,

    # 手机投屏
    SCRCPY_PATH,

    # 文件系统
    CONVERSATION_HISTORY_FILE,
    RECORD_LOGS_DIR,
    FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE,

    # AI 配置
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_MODEL,
    ZHIPU_CHAT_MODEL,
    ZHIPU_MULTIMODAL_MODEL,

    # 文件上传配置
    MAX_FILE_SIZE,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_FILE_EXTENSIONS,

    # 系统配置
    MAX_HISTORY_LENGTH,
    MAX_CYCLE_TIMES,
    MAX_RETRY_TIMES,
    WAIT_INTERVAL,

    # 快捷键
    SHORTCUTS,

    # TTS 配置
    TTS_REF_LANGUAGE,
    TTS_TARGET_LANGUAGE,
    TTS_TOP_P,
    TTS_TEMPERATURE,
    TTS_SPEED,
    TTS_MAX_SEGMENT_LENGTH,
    TTS_MIN_TEXT_LENGTH,
    TTS_ENABLE_PARALLEL,

    # 音频处理配置
    FFMPEG_PATH,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_DEVICE,
    WHISPER_CONVERT_TO_SIMPLIFIED,

    # GUI 主题
    ThemeColors,

    # 终端颜色
    Color,

    # 工具函数
    validate_config,
    print_config_summary,

)

__version__ = "1.2.4"
__author__ = "Phone Agent Team"

__all__ = [
    # 主类
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

    # 配置
    "PROJECT_ROOT",
    "CURRENT_DIR",
    "GPT_SOVITS_ROOT",
    "GPT_MODEL_DIR",
    "SOVITS_MODEL_DIR",
    "REF_AUDIO_ROOT",
    "REF_TEXT_ROOT",
    "BERT_MODEL_PATH",
    "HUBERT_MODEL_PATH",
    "TTS_OUTPUT_DIR",
    "SCRCPY_PATH",
    "CONVERSATION_HISTORY_FILE",
    "RECORD_LOGS_DIR",
    "FOREVER_MEMORY_FILE",
    "CONNECTION_CONFIG_FILE",
    "ZHIPU_API_KEY",
    "ZHIPU_API_BASE_URL",
    "ZHIPU_MODEL",
    "ZHIPU_CHAT_MODEL",
    "ZHIPU_MULTIMODAL_MODEL",
    "MAX_FILE_SIZE",
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_VIDEO_EXTENSIONS",
    "ALLOWED_AUDIO_EXTENSIONS",
    "ALLOWED_FILE_EXTENSIONS",
    "MAX_HISTORY_LENGTH",
    "MAX_CYCLE_TIMES",
    "MAX_RETRY_TIMES",
    "WAIT_INTERVAL",
    "SHORTCUTS",
    "TTS_REF_LANGUAGE",
    "TTS_TARGET_LANGUAGE",
    "TTS_TOP_P",
    "TTS_TEMPERATURE",
    "TTS_SPEED",
    "TTS_MAX_SEGMENT_LENGTH",
    "TTS_MIN_TEXT_LENGTH",
    "TTS_ENABLE_PARALLEL",
    "ThemeColors",
    "Color",
    "validate_config",
    "print_config_summary",

    # 多模态处理器
    "MultimodalProcessor",
    "MultimodalOther",
    "ImagePreviewWindow",
    "VideoPreviewWindow",

    # 音频处理
    "AudioProcessor",
]


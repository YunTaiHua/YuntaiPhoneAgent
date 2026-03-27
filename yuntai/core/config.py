"""
配置管理模块
支持通过.env文件进行环境变量配置
使用 pathlib 进行跨平台路径处理
"""

import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# 应用版本号，统一放在配置中，方便统一更新
APP_VERSION = "1.3.5"

# 加载环境变量
load_dotenv()

# ==================== 基础路径配置 ====================

# 项目根目录（根据当前文件位置动态计算）
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 临时文件目录（YuntaiPhoneAgent/temp）
PROJECT_ROOT_ABS = PROJECT_ROOT.parent
TEMP_DIR = PROJECT_ROOT_ABS / "temp"

# ==================== GPT-SoVITS 配置 ====================
# GPT-SoVITS 相关的路径配置，用于语音合成功能

# GPT-SoVITS 根目录 - 通过环境变量配置
GPT_SOVITS_ROOT = os.getenv('GPT_SOVITS_ROOT')
if GPT_SOVITS_ROOT:
    GPT_SOVITS_ROOT = Path(GPT_SOVITS_ROOT)

# GPT-SoVITS 模型路径
GPT_MODEL_DIR = GPT_SOVITS_ROOT / "GPT_weights_v2Pro" if GPT_SOVITS_ROOT else None
SOVITS_MODEL_DIR = GPT_SOVITS_ROOT / "SoVITS_weights_v2Pro" if GPT_SOVITS_ROOT else None

# 参考音频和文本路径
REF_AUDIO_ROOT = GPT_SOVITS_ROOT / "参考音频" if GPT_SOVITS_ROOT else None
#参考音频 .wav 和对应的文本 .txt 存放在同一目录下
REF_TEXT_ROOT = GPT_SOVITS_ROOT / "参考音频" if GPT_SOVITS_ROOT else None

# 预训练模型路径
BERT_MODEL_PATH = GPT_SOVITS_ROOT / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large" if GPT_SOVITS_ROOT else None
HUBERT_MODEL_PATH = GPT_SOVITS_ROOT / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base" if GPT_SOVITS_ROOT else None

# TTS 输出目录
TTS_OUTPUT_DIR = TEMP_DIR / "tts_output_audio"

# ==================== 手机投屏配置 ====================
# 手机投屏功能相关配置，使用scrcpy工具

# Scrcpy 可执行文件路径 - 通过环境变量配置
SCRCPY_PATH = os.getenv('SCRCPY_PATH')
if SCRCPY_PATH:
    SCRCPY_PATH = Path(SCRCPY_PATH)

# ==================== AI 配置 ====================
# 智谱AI相关配置，用于多模态AI功能

# 智谱AI API 密钥 - 通过环境变量配置，提高安全性
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
if ZHIPU_API_KEY is None:
    raise ValueError("ZHIPU_API_KEY 环境变量未设置，请在 .env 文件中配置")

# 智谱AI客户端 - 将在主文件中初始化
ZHIPU_CLIENT = None

# API 端点
ZHIPU_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# 模型名称
ZHIPU_MODEL = "autoglm-phone"
ZHIPU_CHAT_MODEL = "glm-4.6v-flash"
ZHIPU_JUDGEMENT_MODEL = "glm-4.6v-flash"
ZHIPU_MULTIMODAL_MODEL = "glm-4.6v-flash"
ZHIPU_IMAGE_MODEL = "cogview-3-flash"
ZHIPU_VIDEO_MODEL = "cogvideox-flash"

# 文件上传配置
MAX_FILE_SIZE = 100 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']
ALLOWED_FILE_EXTENSIONS = ['.txt', '.py', '.csv', '.xls', '.xlsx', '.docx', '.pdf', '.ppt', '.pptx', '.html', '.js', '.htm', '.rss', '.atom', '.json', '.xml', '.java', '.ipynb']

# ==================== 音频处理配置 ====================
# 音频处理相关配置，包括Whisper语音识别

# FFmpeg 可执行文件路径 - 通过环境变量配置
FFMPEG_PATH = os.getenv('FFMPEG_PATH')
if FFMPEG_PATH:
    FFMPEG_PATH = Path(FFMPEG_PATH)

WHISPER_MODEL = "small"
WHISPER_LANGUAGE = "zh"
WHISPER_DEVICE = "cuda"

# 繁简转换配置
WHISPER_CONVERT_TO_SIMPLIFIED = True

# ==================== 文件配置 ====================
# 各种数据文件的路径配置

# 对话历史记录文件
CONVERSATION_HISTORY_FILE = TEMP_DIR / "conversation_history.json"

# 记录日志目录
RECORD_LOGS_DIR = TEMP_DIR / "record_logs"

# 永久记忆文件 - 通过环境变量配置，支持自定义路径
FOREVER_MEMORY_FILE = os.getenv('FOREVER_MEMORY_FILE')
if FOREVER_MEMORY_FILE:
    FOREVER_MEMORY_FILE = Path(FOREVER_MEMORY_FILE)

# 连接配置文件
CONNECTION_CONFIG_FILE = TEMP_DIR / "connection_config.json"

# ==================== 设备类型配置 ====================
# 设备类型常量
DEVICE_TYPE_ANDROID = "android"
DEVICE_TYPE_HARMONY = "harmony"

# 默认设备类型
DEFAULT_DEVICE_TYPE = os.getenv('PHONE_AGENT_DEVICE_TYPE', DEVICE_TYPE_ANDROID)

# ==================== 系统配置 ====================
# 系统运行时的各种参数配置

# 历史记录长度
MAX_HISTORY_LENGTH = 50

# 循环次数
MAX_CYCLE_TIMES = 30

# 重试次数
MAX_RETRY_TIMES = 3

# 等待间隔（秒）
WAIT_INTERVAL = 1

# ==================== TTS 配置 ====================

# TTS 默认语言
TTS_REF_LANGUAGE = "中文"
TTS_TARGET_LANGUAGE = "中文"

# TTS 合成参数
TTS_TOP_P = 1.0
TTS_TEMPERATURE = 1.0
TTS_SPEED = 1.0

# 分段合成配置
TTS_MAX_SEGMENT_LENGTH = 500
TTS_MIN_TEXT_LENGTH = 100
TTS_ENABLE_PARALLEL = True

# ==================== 手机操作配置 ====================
PHONE_AGENT_MAX_STEPS = 100
PHONE_AGENT_LANG = "cn"

PHONE_SUCCESS_KEYWORDS = [
    "已成功发送消息", "消息已成功发送", "发送了消息",
    "发送成功", "发送了", "已发送",
    "点击了发送", "发送按钮", "点击发送按钮"
]

# ==================== 消息处理配置 ====================
SIMILARITY_THRESHOLD = 0.6
SIMILARITY_CHECK_NEW_THRESHOLD = 0.5
PARSE_MAX_TOKENS = 2000
REPLY_MAX_TOKENS = 500
REPLY_TEMPERATURE = 0.7
REPLY_HISTORY_LIMIT = 5
MIN_MESSAGE_LENGTH = 2

# ==================== 聊天 Agent 配置 ====================
RECENT_CHATS_LIMIT = 5
TTS_MIN_REPLY_LENGTH = 5
TTS_SPEAK_DELAY_REPLY = 0.5
TTS_SPEAK_DELAY_TASK = 0.3
HISTORY_CONTEXT_LIMIT = 10

# ==================== 工具函数配置 ====================
ADB_CHECK_TIMEOUT = 10
HDC_CHECK_TIMEOUT = 5
API_CHECK_TIMEOUT = 30.0
API_CHECK_MAX_TOKENS = 5

# ==================== 媒体生成配置 ====================
MEDIA_CHUNK_SIZE = 8192
MEDIA_TIMEOUT = 30
MAX_IMAGE_COUNT = 2
INITIAL_DELAY_TEXT = 10
INITIAL_DELAY_IMAGE = 30
MAX_ATTEMPTS = 100
CHECK_INTERVAL = 10
DOWNLOAD_TIMEOUT = 30

IMAGE_SIZES = [
    "1280x1280",
    "1024x1024",
    "1024x768",
    "768x1024",
    "1920x1080",
    "1080x1920"
]

VIDEO_SIZES = [
    "1920x1080",
    "1080x1920",
    "1280x720",
    "720x1280",
    "1024x1024",
    "3840x2160"
]

VIDEO_FPS = [30, 60]

# ==================== GUI 主题配置 ====================
# 图形用户界面主题颜色配置
# ThemeColors 将在文件末尾延迟导入，避免循环依赖

# ==================== 快捷键配置 ====================
# 快捷键映射配置，用于快速启动应用

# 快捷键字典 - 键为单字符快捷键，值为对应的应用名称
SHORTCUTS = {
    'w': '打开微信',
    'q': '打开QQ',
    'd': '打开抖音',
    'k': '打开快手',
    't': '打开淘宝',
    'm': '打开QQ音乐'
}

# ==================== 验证配置 ====================

def validate_config():
    """
    验证配置文件有效性

    检查所有必要的路径和配置是否存在且有效。
    如果发现配置问题，会输出警告信息。

    Returns:
        bool: 配置验证是否通过
    """
    errors = []

    if GPT_SOVITS_ROOT and not GPT_SOVITS_ROOT.exists():
        errors.append(f"GPT-SoVITS 根目录不存在: {GPT_SOVITS_ROOT}")

    if SCRCPY_PATH and not SCRCPY_PATH.exists():
        errors.append(f"Scrcpy 路径不存在: {SCRCPY_PATH}")

    if GPT_MODEL_DIR and not GPT_MODEL_DIR.exists():
        errors.append(f"GPT 模型目录不存在: {GPT_MODEL_DIR}")

    if SOVITS_MODEL_DIR and not SOVITS_MODEL_DIR.exists():
        errors.append(f"SoVITS 模型目录不存在: {SOVITS_MODEL_DIR}")

    if REF_AUDIO_ROOT and not REF_AUDIO_ROOT.exists():
        errors.append(f"参考音频目录不存在: {REF_AUDIO_ROOT}")

    if not ZHIPU_API_KEY or len(ZHIPU_API_KEY) < 10:
        errors.append("智谱AI API 密钥无效或为空")

    if errors:
        print("⚠️ 配置验证警告:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ 配置验证通过")
    return True


def print_config_summary() -> None:
    """
    打印当前配置摘要

    显示所有重要的配置路径和参数，便于用户检查配置是否正确。
    通常在程序启动时调用。
    """
    summary = f"""
📋 配置摘要:
────────────────────────────────────
• 项目根目录: {PROJECT_ROOT}
• GPT-SoVITS 根目录: {GPT_SOVITS_ROOT}
• GPT 模型目录: {GPT_MODEL_DIR}
• SoVITS 模型目录: {SOVITS_MODEL_DIR}
• 参考音频目录: {REF_AUDIO_ROOT}
• TTS 输出目录: {TTS_OUTPUT_DIR}
• Scrcpy 路径: {SCRCPY_PATH}
• 对话历史文件: {CONVERSATION_HISTORY_FILE}
• 永久记忆文件: {FOREVER_MEMORY_FILE}
• API 模型: {ZHIPU_MODEL} | {ZHIPU_CHAT_MODEL}
────────────────────────────────────
"""
    print(summary)


def check_required_env_vars() -> None:
    """检查必需的环境变量是否已设置"""
    required_vars = ['ZHIPU_API_KEY']
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"必需的环境变量 {var} 未设置，请在 .env 文件中配置")


if __name__ == "__main__":
    check_required_env_vars()
    validate_config()
    print_config_summary()


def _get_theme_colors() -> type:
    """延迟获取 ThemeColors 类"""
    from yuntai.gui.styles import ThemeColors as _ThemeColors
    return _ThemeColors

class _ThemeColorsProxy:
    """ThemeColors 的代理类，实现延迟导入"""
    _real_class = None
    
    def __getattr__(self, name) -> Any:
        if self._real_class is None:
            self._real_class = _get_theme_colors()
        return getattr(self._real_class, name)

ThemeColors = _ThemeColorsProxy()

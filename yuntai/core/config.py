"""
配置管理模块
支持通过.env文件进行环境变量配置
使用 pathlib 进行跨平台路径处理
"""

import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

APP_VERSION = "1.3.4"

load_dotenv()

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

PROJECT_ROOT_ABS = PROJECT_ROOT.parent
TEMP_DIR = PROJECT_ROOT_ABS / "temp"

GPT_SOVITS_ROOT = os.getenv('GPT_SOVITS_ROOT')
if GPT_SOVITS_ROOT:
    GPT_SOVITS_ROOT = Path(GPT_SOVITS_ROOT)

GPT_MODEL_DIR = GPT_SOVITS_ROOT / "GPT_weights_v2Pro" if GPT_SOVITS_ROOT else None
SOVITS_MODEL_DIR = GPT_SOVITS_ROOT / "SoVITS_weights_v2Pro" if GPT_SOVITS_ROOT else None

REF_AUDIO_ROOT = GPT_SOVITS_ROOT / "参考音频" if GPT_SOVITS_ROOT else None
REF_TEXT_ROOT = GPT_SOVITS_ROOT / "参考音频" if GPT_SOVITS_ROOT else None

BERT_MODEL_PATH = GPT_SOVITS_ROOT / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large" if GPT_SOVITS_ROOT else None
HUBERT_MODEL_PATH = GPT_SOVITS_ROOT / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base" if GPT_SOVITS_ROOT else None

TTS_OUTPUT_DIR = TEMP_DIR / "tts_output_audio"

SCRCPY_PATH = os.getenv('SCRCPY_PATH')
if SCRCPY_PATH:
    SCRCPY_PATH = Path(SCRCPY_PATH)

ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
assert ZHIPU_API_KEY is not None, "ZHIPU_API_KEY 环境变量未设置"

ZHIPU_CLIENT = None

ZHIPU_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

ZHIPU_MODEL = "autoglm-phone"
ZHIPU_CHAT_MODEL = "glm-4.6v-flash"
ZHIPU_JUDGEMENT_MODEL = "glm-4.6v-flash"
ZHIPU_MULTIMODAL_MODEL = "glm-4.6v-flash"
ZHIPU_IMAGE_MODEL = "cogview-3-flash"
ZHIPU_VIDEO_MODEL = "cogvideox-flash"

MAX_FILE_SIZE = 100 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']
ALLOWED_FILE_EXTENSIONS = ['.txt', '.py', '.csv', '.xls', '.xlsx', '.docx', '.pdf', '.ppt', '.pptx', '.html', '.js', '.htm', '.rss', '.atom', '.json', '.xml', '.java', '.ipynb']

FFMPEG_PATH = os.getenv('FFMPEG_PATH')
if FFMPEG_PATH:
    FFMPEG_PATH = Path(FFMPEG_PATH)

WHISPER_MODEL = "small"
WHISPER_LANGUAGE = "zh"
WHISPER_DEVICE = "cuda"

WHISPER_CONVERT_TO_SIMPLIFIED = True

CONVERSATION_HISTORY_FILE = TEMP_DIR / "conversation_history.json"

RECORD_LOGS_DIR = TEMP_DIR / "record_logs"

FOREVER_MEMORY_FILE = os.getenv('FOREVER_MEMORY_FILE')
if FOREVER_MEMORY_FILE:
    FOREVER_MEMORY_FILE = Path(FOREVER_MEMORY_FILE)

CONNECTION_CONFIG_FILE = TEMP_DIR / "connection_config.json"

DEVICE_TYPE_ANDROID = "android"
DEVICE_TYPE_HARMONY = "harmony"

DEFAULT_DEVICE_TYPE = os.getenv('PHONE_AGENT_DEVICE_TYPE', DEVICE_TYPE_ANDROID)

MAX_HISTORY_LENGTH = 50

MAX_CYCLE_TIMES = 30

MAX_RETRY_TIMES = 3

WAIT_INTERVAL = 1

TTS_REF_LANGUAGE = "中文"
TTS_TARGET_LANGUAGE = "中文"

TTS_TOP_P = 1.0
TTS_TEMPERATURE = 1.0
TTS_SPEED = 1.0

TTS_MAX_SEGMENT_LENGTH = 500
TTS_MIN_TEXT_LENGTH = 100
TTS_ENABLE_PARALLEL = True

SHORTCUTS = {
    'w': '打开微信',
    'q': '打开QQ',
    'd': '打开抖音',
    'k': '打开快手',
    't': '打开淘宝',
    'm': '打开QQ音乐'
}


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

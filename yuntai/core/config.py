"""
配置模块
========

集中管理所有配置项，使用 python-dotenv 从 .env 文件加载环境变量。
所有配置项都有默认值，确保在没有 .env 文件时也能正常运行。

配置分类:
    - 智谱 AI 配置: API 密钥、模型名称、API 地址
    - 设备连接配置: ADB/HDC 路径、连接超时
    - TTS 配置: GPT-SoVITS 模型路径、输出目录
    - 文件路径配置: 项目根目录、临时目录
    - 相似度配置: 阈值设置
    - 多模态配置: 文件大小限制、允许的扩展名

使用示例:
    >>> from yuntai.core.config import ZHIPU_API_KEY, PROJECT_ROOT
    >>> print(ZHIPU_API_KEY)
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 加载 .env 环境变量文件
# 确保在任何配置访问之前执行，以便 API 密钥等敏感信息能够正确加载
load_dotenv()

# 应用版本号，统一放在配置中，方便统一更新
# 当版本更新时，只需修改此变量即可
APP_VERSION = "1.3.5"

# ==================== 基础路径配置 ====================
# 使用 Path 对象进行跨平台路径处理，支持 Windows/Linux/macOS

# 项目根目录（根据当前文件位置动态计算）
# 原理：通过 __file__ 获取当前文件路径，resolve() 转换为绝对路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

# 临时文件目录（YuntaiPhoneAgent/temp）
# 用于存储运行时生成的临时文件，如对话历史、录音文件等
PROJECT_ROOT_ABS = PROJECT_ROOT.parent
TEMP_DIR = PROJECT_ROOT_ABS / "temp"

# ==================== GPT-SoVITS 配置 ====================
# GPT-SoVITS 相关的路径配置，用于语音合成功能
# GPT-SoVITS 是一款高效的文本转语音模型，支持中英文合成

# GPT-SoVITS 根目录 - 通过环境变量配置
# 环境变量格式：GPT_SOVITS_ROOT=/path/to/gpt-sovits
GPT_SOVITS_ROOT = os.getenv('GPT_SOVITS_ROOT')
if GPT_SOVITS_ROOT:
    GPT_SOVITS_ROOT = Path(GPT_SOVITS_ROOT)

# GPT-SoVITS 模型路径
# GPT_weights_v2Pro: GPT 模型权重目录，用于文本编码
# SoVITS_weights_v2Pro: SoVITS 模型权重目录，用于音频生成
GPT_MODEL_DIR = GPT_SOVITS_ROOT / "GPT_weights_v2Pro" if GPT_SOVITS_ROOT else None
SOVITS_MODEL_DIR = GPT_SOVITS_ROOT / "SoVITS_weights_v2Pro" if GPT_SOVITS_ROOT else None

# 参考音频和文本路径
# 参考音频 .wav 和对应的文本 .txt 存放在同一目录下
# 系统会自动匹配同名 .txt 文件作为参考文本
REF_AUDIO_ROOT = GPT_SOVITS_ROOT / "参考音频" if GPT_SOVITS_ROOT else None
REF_TEXT_ROOT = GPT_SOVITS_ROOT / "参考音频" if GPT_SOVITS_ROOT else None

# 预训练模型路径
# chinese-roberta-wwm-ext-large: 中文 BERT 模型，用于文本特征提取
# chinese-hubert-base: 中文 HuBERT 模型，用于音频特征提取
BERT_MODEL_PATH = GPT_SOVITS_ROOT / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large" if GPT_SOVITS_ROOT else None
HUBERT_MODEL_PATH = GPT_SOVITS_ROOT / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base" if GPT_SOVITS_ROOT else None

# TTS 输出目录
# 合成后的音频文件将保存在此目录下
TTS_OUTPUT_DIR = TEMP_DIR / "tts_output_audio"

# ==================== 手机投屏配置 ====================
# 手机投屏功能相关配置，使用 scrcpy 工具实现电脑控制手机
# scrcpy 是一款开源的手机投屏工具，支持 Windows/Linux/macOS

# Scrcpy 可执行文件路径 - 通过环境变量配置
# 环境变量格式：SCRCPY_PATH=/path/to/scrcpy.exe
SCRCPY_PATH = os.getenv('SCRCPY_PATH')
if SCRCPY_PATH:
    SCRCPY_PATH = Path(SCRCPY_PATH)

# ==================== AI 配置 ====================
# 智谱 AI 相关配置，用于多模态 AI 功能
# 智谱 AI 提供 GLM 系列大模型，支持文本、图像、视频等多种模态

# 智谱AI API 密钥 - 通过环境变量配置，提高安全性
# 密钥不会硬编码在代码中，支持多环境配置
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
if ZHIPU_API_KEY is None:
    raise ValueError("ZHIPU_API_KEY 环境变量未设置，请在 .env 文件中配置")

# 智谱AI客户端 - 将在主文件中初始化
ZHIPU_CLIENT = None

# API 端点 - 智谱 AI API 的基础 URL
ZHIPU_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# 模型名称
# autoglm-phone: 手机自动化任务专用模型
# glm-4.6v-flash: 多模态理解模型，支持图像、视频分析
# cogview-3-flash: 图像生成模型
# cogvideox-flash: 视频生成模型
ZHIPU_MODEL = "autoglm-phone"
ZHIPU_CHAT_MODEL = "glm-4.6v-flash"
ZHIPU_JUDGEMENT_MODEL = "glm-4.6v-flash"
ZHIPU_MULTIMODAL_MODEL = "glm-4.6v-flash"
ZHIPU_IMAGE_MODEL = "cogview-3-flash"
ZHIPU_VIDEO_MODEL = "cogvideox-flash"

# 文件上传配置
# 限制上传文件的大小和类型，保证系统安全稳定运行
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']
ALLOWED_FILE_EXTENSIONS = [
    '.txt', '.py', '.csv', '.xls', '.xlsx', '.docx', '.pdf', '.ppt', '.pptx',
    '.html', '.js', '.csv', '.htm', '.rss', '.atom', '.json', '.xml', '.java', '.ipynb'
]

# ==================== 音频处理配置 ====================
# 音频处理相关配置，包括 Whisper 语音识别和 FFmpeg 音视频处理

# FFmpeg 可执行文件路径 - 通过环境变量配置
# FFmpeg 是强大的音视频处理工具，用于提取音频、格式转换等
FFMPEG_PATH = os.getenv('FFMPEG_PATH')
if FFMPEG_PATH:
    FFMPEG_PATH = Path(FFMPEG_PATH)

# Whisper 语音识别配置
WHISPER_MODEL = "small"  # 模型大小：tiny/base/small/medium/large，越大越准确但越慢
WHISPER_LANGUAGE = "zh"  # 识别语言：zh=中文
WHISPER_DEVICE = "cuda"  # 运行设备：cuda=GPU，cpu=CPU

# 繁简转换配置
# 将繁体中文转换为简体中文，保持输出一致性
WHISPER_CONVERT_TO_SIMPLIFIED = True

# ==================== 文件配置 ====================
# 各种数据文件的路径配置，用于持久化存储对话和配置信息

# 对话历史记录文件
# 存储聊天记录，包括自由聊天和应用聊天的历史
CONVERSATION_HISTORY_FILE = TEMP_DIR / "conversation_history.json"

# 记录日志目录
# 存储详细的聊天记录日志，用于问题排查和数据分析
RECORD_LOGS_DIR = TEMP_DIR / "record_logs"

# 永久记忆文件 - 通过环境变量配置，支持自定义路径
# 用于存储需要长期保留的记忆信息，不受对话历史限制
FOREVER_MEMORY_FILE = os.getenv('FOREVER_MEMORY_FILE')
if FOREVER_MEMORY_FILE:
    FOREVER_MEMORY_FILE = Path(FOREVER_MEMORY_FILE)

# 连接配置文件
# 存储设备连接信息，如 USB 设备 ID 或无线连接 IP
CONNECTION_CONFIG_FILE = TEMP_DIR / "connection_config.json"

# ==================== 设备类型配置 ====================
# 设备类型常量，用于区分不同类型的手机设备

DEVICE_TYPE_ANDROID = "android"  # Android 设备，使用 ADB 进行调试
DEVICE_TYPE_HARMONY = "harmony"  # HarmonyOS 设备，使用 HDC 进行调试

# 默认设备类型 - 可通过环境变量覆盖
# 环境变量格式：PHONE_AGENT_DEVICE_TYPE=harmony
DEFAULT_DEVICE_TYPE = os.getenv('PHONE_AGENT_DEVICE_TYPE', DEVICE_TYPE_ANDROID)

# ==================== 系统配置 ====================
# 系统运行时的各种参数配置，用于控制程序行为

# 历史记录长度
# 限制保存的对话历史数量，防止文件过大
MAX_HISTORY_LENGTH = 50

# 循环次数
# 单次任务执行的最大循环次数，防止无限循环
MAX_CYCLE_TIMES = 30

# 重试次数
# 网络请求或操作失败时的最大重试次数
MAX_RETRY_TIMES = 3

# 等待间隔（秒）
# 循环任务中每次等待的时间间隔
WAIT_INTERVAL = 1

# ==================== TTS 配置 ====================
# TTS 语音合成相关配置，控制合成效果和性能

# TTS 默认语言
TTS_REF_LANGUAGE = "中文"  # 参考音频的语言
TTS_TARGET_LANGUAGE = "中文"  # 目标合成语言

# TTS 合成参数
# 影响合成音频的特性
TTS_TOP_P = 1.0  # 采样多样性参数，范围 0-1，越低越保守
TTS_TEMPERATURE = 1.0  # 温度参数，越高越有创造性但可能不稳定
TTS_SPEED = 1.0  # 语速倍数，1.0 为正常速度

# 分段合成配置
# 当文本过长时，系统会自动分段合成以提高质量
TTS_MAX_SEGMENT_LENGTH = 500  # 单段最大字符数
TTS_MIN_TEXT_LENGTH = 100  # 触发分段合成的最小字符数
TTS_ENABLE_PARALLEL = True  # 是否启用并行分段合成

# ==================== 手机操作配置 ====================
# 手机自动化操作相关配置

PHONE_AGENT_MAX_STEPS = 100  # 单次任务最大步数
PHONE_AGENT_LANG = "cn"  # 操作界面语言：cn=中文

# 消息发送成功的关键字列表
# 系统通过检测屏幕文本来判断消息是否发送成功
PHONE_SUCCESS_KEYWORDS = [
    "已成功发送消息", "消息已成功发送", "发送了消息",
    "发送成功", "发送了", "已发送",
    "点击了发送", "发送按钮", "点击发送按钮"
]

# ==================== 消息处理配置 ====================
# 消息解析和回复生成相关配置

SIMILARITY_THRESHOLD = 0.6  # 消息相似度阈值，用于判断是否为同一条消息
SIMILARITY_CHECK_NEW_THRESHOLD = 0.5  # 新消息检测阈值
PARSE_MAX_TOKENS = 2000  # 消息解析最大 token 数
REPLY_MAX_TOKENS = 500  # 回复生成最大 token 数
REPLY_TEMPERATURE = 0.7  # 回复生成温度参数
REPLY_HISTORY_LIMIT = 5  # 用于生成回复的历史消息条数
MIN_MESSAGE_LENGTH = 2  # 最小消息长度，短于此长度的消息将被忽略

# ==================== 聊天 Agent 配置 ====================
# 聊天功能相关配置

RECENT_CHATS_LIMIT = 5  # 最近聊天记录显示数量
TTS_MIN_REPLY_LENGTH = 5  # 触发 TTS 播报的最小回复长度
TTS_SPEAK_DELAY_REPLY = 0.5  # 回复播报延迟（秒）
TTS_SPEAK_DELAY_TASK = 0.3  # 任务播报延迟（秒）
HISTORY_CONTEXT_LIMIT = 10  # 历史上下文限制

# ==================== 工具函数配置 ====================
# 各种工具函数的超时和参数配置

ADB_CHECK_TIMEOUT = 10  # ADB 环境检查超时（秒）
HDC_CHECK_TIMEOUT = 5  # HDC 环境检查超时（秒）
API_CHECK_TIMEOUT = 30.0  # API 检查超时（秒）
API_CHECK_MAX_TOKENS = 5  # API 检查最大 token 数

# ==================== 连接管理配置 ====================
# 设备检测和连接相关超时配置

DEVICE_DETECT_TIMEOUT: int = 10  # 设备检测超时（秒）
DEVICE_CONNECT_TIMEOUT: int = 15  # 设备连接超时（秒）

# 设备ID安全限制
# 防止超长设备 ID 导致的安全问题
MAX_DEVICE_ID_LENGTH: int = 100

# 无线调试默认端口
# Android 无线调试默认使用 5555 端口
DEFAULT_WIRELESS_PORT: str = "5555"

# ==================== PhoneAgent 缓存配置 ====================
# PhoneAgent 实例缓存最大数量，用于优化聊天记录提取性能
# 当缓存超过此限制时，自动清理最旧的条目
PHONE_AGENT_CACHE_MAX_SIZE: int = 10

# ==================== 媒体生成配置 ====================
# 图像和视频生成相关配置

MEDIA_CHUNK_SIZE = 8192  # 媒体下载分块大小（字节）
MEDIA_TIMEOUT = 30  # 媒体下载超时（秒）
MAX_IMAGE_COUNT = 2  # 单次生成最大图片数
INITIAL_DELAY_TEXT = 10  # 文字生成视频初始延迟（秒）
INITIAL_DELAY_IMAGE = 30  # 图片生成视频初始延迟（秒）
MAX_ATTEMPTS = 100  # 视频生成状态检查最大次数
CHECK_INTERVAL = 10  # 视频生成状态检查间隔（秒）
DOWNLOAD_TIMEOUT = 30  # 视频下载超时（秒）

# 支持的图像尺寸列表
IMAGE_SIZES = [
    "1280x1280",  # 正方形
    "1024x1024",
    "1024x768",   # 横版 4:3
    "768x1024",   # 竖版 3:4
    "1920x1080",  # 全高清横版
    "1080x1920"   # 全高清竖版
]

# 支持的视频尺寸列表
VIDEO_SIZES = [
    "1920x1080",  # 全高清横版
    "1080x1920",  # 全高清竖版
    "1280x720",   # HD 横版
    "720x1280",   # HD 竖版
    "1024x1024",  # 正方形视频
    "3840x2160"  # 4K 超高清
]

# 支持的视频帧率列表
VIDEO_FPS = [30, 60]  # 30fps 或 60fps

# ==================== 快捷键配置 ====================
# 快捷键映射配置，用于快速启动应用

# 快捷键字典 - 键为单字符快捷键，值为对应的应用名称
# 使用单字符便于在输入框中快速触发
SHORTCUTS = {
    'w': '打开微信',
    'q': '打开QQ',
    'd': '打开抖音',
    'k': '打开快手',
    't': '打开淘宝',
    'm': '打开QQ音乐'
}

# ==================== 验证配置 ====================


def validate_config() -> bool:
    """
    验证配置文件有效性

    检查所有必要的路径和配置是否存在且有效。
    如果发现配置问题，会输出警告信息但不会阻止程序启动。

    Returns:
        bool: 配置验证是否通过（True 表示所有检查项通过）

    Note:
        此函数执行的是警告级别验证，即使部分配置缺失也不会抛出异常。
        关键配置（如 API 密钥）应在初始化时单独验证。
    """
    errors = []

    # 检查 GPT-SoVITS 相关路径
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

    # API 密钥验证
    if not ZHIPU_API_KEY or len(ZHIPU_API_KEY) < 10:
        errors.append("智谱AI API 密钥无效或为空")

    # 输出验证结果
    if errors:
        print("⚠️  配置验证警告:")
        for error in errors:
            print(f"  - {error}")
        logger.warning("配置验证失败，共 %d 项问题", len(errors))
        return False

    logger.debug("配置验证通过，所有检查项正常")
    return True


def print_config_summary() -> None:
    """
    打印当前配置摘要

    显示所有重要的配置路径和参数，便于用户检查配置是否正确。
    通常在程序启动时调用。

    Note:
        此函数输出到控制台，用于用户交互界面。
        日志记录由调用方自行处理。
    """
    # 构建配置摘要字符串
    # 使用多行格式，便于阅读
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
    logger.debug("配置摘要已打印")


def check_required_env_vars() -> None:
    """
    检查必需的环境变量是否已设置

    检查所有程序运行所必需的环境变量。如果发现未设置，
    会抛出 ValueError 异常阻止程序启动。

    Raises:
        ValueError: 当必需的环境变量未设置时抛出

    Note:
        此函数应在程序入口处尽早调用，
        确保所有依赖配置在初始化前已正确设置。
    """
    required_vars = ['ZHIPU_API_KEY']
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)

    if missing_vars:
        error_msg = f"必需的环境变量 {', '.join(missing_vars)} 未设置，请在 .env 文件中配置"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("必需环境变量检查通过")


if __name__ == "__main__":
    # 当直接运行 config.py 时，执行配置检查
    check_required_env_vars()
    validate_config()
    print_config_summary()

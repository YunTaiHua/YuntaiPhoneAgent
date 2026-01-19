"""
统一配置文件 - 重构版
集中管理所有路径和配置参数
支持通过.env文件进行环境变量配置，提高安全性
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 基础路径配置 ====================

# 项目根目录（根据当前文件位置动态计算）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(CURRENT_DIR))

# ==================== GPT-SoVITS 配置 ====================
# GPT-SoVITS 相关的路径配置，用于语音合成功能

# GPT-SoVITS 根目录 - 通过环境变量配置
GPT_SOVITS_ROOT = os.getenv('GPT_SOVITS_ROOT')

# GPT-SoVITS 模型路径
GPT_MODEL_DIR = os.path.join(GPT_SOVITS_ROOT, "GPT_weights_v2Pro")
SOVITS_MODEL_DIR = os.path.join(GPT_SOVITS_ROOT, "SoVITS_weights_v2Pro")

# 参考音频和文本路径
REF_AUDIO_ROOT = os.path.join(GPT_SOVITS_ROOT, "参考音频")
REF_TEXT_ROOT = os.path.join(GPT_SOVITS_ROOT, "参考音频")  # 通常与音频同一目录

# 预训练模型路径
BERT_MODEL_PATH = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS", "pretrained_models",
                               "chinese-roberta-wwm-ext-large")
HUBERT_MODEL_PATH = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS", "pretrained_models",
                                 "chinese-hubert-base")

# TTS 输出目录
TTS_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tts_output_audio")

# ==================== 手机投屏配置 ====================
# 手机投屏功能相关配置，使用scrcpy工具

# Scrcpy 可执行文件路径 - 通过环境变量配置
SCRCPY_PATH = os.getenv('SCRCPY_PATH')

# ==================== 文件系统配置 ====================

# 对话历史文件
CONVERSATION_HISTORY_FILE = os.path.join(PROJECT_ROOT, "conversation_history.json")

# 记录日志目录
RECORD_LOGS_DIR = os.path.join(PROJECT_ROOT, "record_logs")

# 永久记忆文件
FOREVER_MEMORY_FILE = os.path.join(PROJECT_ROOT, "forever.txt")

# 连接配置文件
CONNECTION_CONFIG_FILE = os.path.join(PROJECT_ROOT, "connection_config.json")

# ==================== AI 配置 ====================
# 智谱AI相关配置，用于多模态AI功能

# 智谱AI API 密钥 - 通过环境变量配置，增强安全性
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
assert ZHIPU_API_KEY is not None, "ZHIPU_API_KEY 环境变量未设置"

# API 端点
ZHIPU_API_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

# 模型名称
ZHIPU_MODEL = "autoglm-phone"
ZHIPU_CHAT_MODEL = "glm-4.6v-flash"
ZHIPU_MULTIMODAL_MODEL = "glm-4.6v-flash"
ZHIPU_IMAGE_MODEL = "cogview-3-flash"
ZHIPU_VIDEO_MODEL = "cogvideox-flash"

# 文件上传配置
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB（支持更大的视频/音频文件）
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
ALLOWED_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
ALLOWED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']
ALLOWED_FILE_EXTENSIONS = ['.txt', '.py', '.csv', '.xls', '.xlsx', '.docx', '.pdf', '.ppt', '.pptx', '.html', '.js']

# ==================== 音频处理配置 ====================
# 音频处理相关配置，包括Whisper语音识别

# FFmpeg 可执行文件路径 - 通过环境变量配置
FFMPEG_PATH = os.getenv('FFMPEG_PATH')

# Whisper 配置
WHISPER_MODEL = "small"  # 可选: tiny, base, small, medium, large
WHISPER_LANGUAGE = "zh"  # 默认语言，None表示自动检测
WHISPER_DEVICE = "cpu"  # 可选: cpu, cuda

# 繁简转换配置
WHISPER_CONVERT_TO_SIMPLIFIED = True  # 是否将繁体转换为简体
# 会自动尝试使用 opencc 或 zhconv

# ==================== 系统配置 ====================

# 历史记录长度
MAX_HISTORY_LENGTH = 50

# 循环次数
MAX_CYCLE_TIMES = 30

# 重试次数
MAX_RETRY_TIMES = 3

# 等待间隔（秒）
WAIT_INTERVAL = 1

# ==================== 快捷键配置 ====================

SHORTCUTS = {
    'w': '打开微信',
    'q': '打开QQ',
    'd': '打开抖音',
    'k': '打开快手',
    't': '打开淘宝',
    'm': '打开QQ音乐'
}

# ==================== TTS 配置 ====================

# TTS 默认语言
TTS_REF_LANGUAGE = "中文"
TTS_TARGET_LANGUAGE = "中文"

# TTS 合成参数
TTS_TOP_P = 1.0
TTS_TEMPERATURE = 1.0
TTS_SPEED = 1.0

# 分段合成配置
TTS_MAX_SEGMENT_LENGTH = 500  # 单个片段最大长度（字符）
TTS_MIN_TEXT_LENGTH = 100     # 启用分段的最小文本长度
TTS_ENABLE_PARALLEL = True    # 启用并行合成


# ==================== GUI 主题配置 ====================
# 图形用户界面主题颜色配置

class ThemeColors:
    """
    GUI 主题颜色类
    定义了整个应用程序的颜色方案
    """
    # 主色调 - 用于主要按钮和强调元素
    PRIMARY = "#4361ee"

    # 次要色调 - 用于辅助元素
    SECONDARY = "#7209b7"

    # 强调色 - 用于突出显示
    ACCENT = "#f72585"

    # 成功状态色 - 用于成功提示
    SUCCESS = "#4cc9f0"

    # 警告状态色 - 用于警告提示
    WARNING = "#f8961e"

    # 危险状态色 - 用于错误提示
    DANGER = "#e63946"

    # 深色背景 - 主背景色
    BG_DARK = "#121212"

    # 卡片背景 - 组件背景色
    BG_CARD = "#1e1e1e"

    # 悬停背景 - 鼠标悬停时的背景色
    BG_HOVER = "#2d2d2d"

    # 主要文本色 - 普通文本
    TEXT_PRIMARY = "#ffffff"

    # 次要文本色 - 辅助文本
    TEXT_SECONDARY = "#b0b0b0"

    # 禁用文本色 - 不可用状态文本
    TEXT_DISABLED = "#666666"





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

    # 检查 GPT-SoVITS 目录 - TTS功能必需
    if not os.path.exists(GPT_SOVITS_ROOT):
        errors.append(f"GPT-SoVITS 根目录不存在: {GPT_SOVITS_ROOT}")

    # 检查 Scrcpy 可执行文件 - 手机投屏功能必需
    if not os.path.exists(SCRCPY_PATH):
        errors.append(f"Scrcpy 路径不存在: {SCRCPY_PATH}")

    # 检查 GPT 模型目录 - TTS模型文件必需
    if not os.path.exists(GPT_MODEL_DIR):
        errors.append(f"GPT 模型目录不存在: {GPT_MODEL_DIR}")

    # 检查 SoVITS 模型目录 - TTS模型文件必需
    if not os.path.exists(SOVITS_MODEL_DIR):
        errors.append(f"SoVITS 模型目录不存在: {SOVITS_MODEL_DIR}")

    # 检查参考音频目录 - TTS训练音频必需
    if not os.path.exists(REF_AUDIO_ROOT):
        errors.append(f"参考音频目录不存在: {REF_AUDIO_ROOT}")

    # 检查 API 密钥 - AI功能必需
    if not ZHIPU_API_KEY or len(ZHIPU_API_KEY) < 10:
        errors.append("智谱AI API 密钥无效或为空")

    if errors:
        print("⚠️ 配置验证警告:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ 配置验证通过")
    return True


# ==================== 配置信息 ====================

def print_config_summary():
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
• API 模型: {ZHIPU_MODEL} / {ZHIPU_CHAT_MODEL}
────────────────────────────────────
"""
    print(summary)


# 配置加载后的检查
def check_required_env_vars():
    """检查必需的环境变量是否已设置"""
    required_vars = ['ZHIPU_API_KEY']
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"必需的环境变量 {var} 未设置，请在 .env 文件中配置")

# 自动验证配置
if __name__ == "__main__":
    check_required_env_vars()
    validate_config()
    print_config_summary()
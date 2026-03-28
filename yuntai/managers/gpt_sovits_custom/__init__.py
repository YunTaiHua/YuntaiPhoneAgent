"""
GPT-SoVITS 自定义模块
=====================

本模块封装了 GPT-SoVITS 语音合成系统的核心功能，提供文本转语音(TTS)能力。

主要功能:
    - get_tts_wav: 文本转语音合成函数
    - change_gpt_weights: 切换 GPT 模型权重
    - change_sovits_weights: 切换 SoVITS 模型权重
    - I18nAuto: 国际化自动翻译工具

模块特点:
    - 移除了所有冗余的 print 输出，使用标准 logging
    - 移除了 tqdm 进度条，减少依赖
    - 使用环境变量配置路径，便于部署

使用示例:
    >>> from yuntai.managers.gpt_sovits_custom import get_tts_wav
    >>> # 合成语音
    >>> for sr, audio in get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language):
    ...     pass  # 处理音频数据

注意事项:
    - 本模块依赖 PyTorch 和相关深度学习库
    - 需要配置 GPT_SOVITS_ROOT 环境变量
    - 首次使用需要下载预训练模型
"""
import logging

logger = logging.getLogger(__name__)

try:
    from .inference_webui import get_tts_wav, change_gpt_weights, change_sovits_weights, I18nAuto
    logger.debug("GPT-SoVITS 模块导入成功")
except ImportError as e:
    logger.warning(f"GPT-SoVITS 模块导入失败: {e}，相关功能将不可用")
    get_tts_wav = None
    change_gpt_weights = None
    change_sovits_weights = None
    I18nAuto = None

__all__ = ['get_tts_wav', 'change_gpt_weights', 'change_sovits_weights', 'I18nAuto']

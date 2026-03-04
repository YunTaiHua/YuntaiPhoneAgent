"""
GPT-SoVITS 自定义模块
- 移除了所有冗余的print输出
- 移除了tqdm进度条
- 使用环境变量配置路径
"""

from .inference_webui import get_tts_wav, change_gpt_weights, change_sovits_weights, I18nAuto

__all__ = ['get_tts_wav', 'change_gpt_weights', 'change_sovits_weights', 'I18nAuto']

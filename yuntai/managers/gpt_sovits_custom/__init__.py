"""
GPT-SoVITS 自定义模块
- 移除了所有冗余的print输出
- 移除了tqdm进度条
- 使用环境变量配置路径
"""

# 使用 try-except 导入，避免导入失败影响主程序运行
try:
    from .inference_webui import get_tts_wav, change_gpt_weights, change_sovits_weights, I18nAuto
except ImportError as e:
    import logging
    logging.warning(f"GPT-SoVITS 模块导入失败: {e}，相关功能将不可用")
    get_tts_wav = None
    change_gpt_weights = None
    change_sovits_weights = None
    I18nAuto = None

__all__ = ['get_tts_wav', 'change_gpt_weights', 'change_sovits_weights', 'I18nAuto']

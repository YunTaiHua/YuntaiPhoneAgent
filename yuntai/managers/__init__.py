"""
TTS 管理器模块
==============

本模块提供 TTS（文本转语音）相关的管理器，负责语音合成的各个环节。

模块包含以下管理器：
    - TTSDatabaseManager: TTS 数据库管理器，负责文件扫描和模型管理
    - TTSTextProcessor: TTS 文本处理器，负责文本清洗和分段
    - TTSEngine: TTS 引擎，负责模型加载和核心合成
    - TTSAudioManager: TTS 音频管理器，负责音频播放和管理

使用示例：
    >>> from yuntai.managers import TTSEngine, TTSDatabaseManager
    >>> 
    >>> # 创建数据库管理器
    >>> db_manager = TTSDatabaseManager(config)
    >>> db_manager.init_tts_files_database()
    >>> 
    >>> # 创建引擎并合成
    >>> engine = TTSEngine(config, db_manager, text_processor)
    >>> success, audio_path = engine.synthesize_text("你好", ref_audio, ref_text)
"""
from .tts_database import TTSDatabaseManager
from .tts_text import TTSTextProcessor
from .tts_engine import TTSEngine
from .tts_audio import TTSAudioPlayer

# 模块公开接口
__all__ = [
    'TTSDatabaseManager',
    'TTSTextProcessor',
    'TTSEngine',
    'TTSAudioPlayer',
]

"""
处理器模块
==========

本模块提供多种数据处理功能，包括音频、图像、视频和多模态处理。

主要组件:
    - AudioProcessor: 音频处理器，支持 Whisper 语音识别
    - MediaGenerator: 媒体生成器，支持图像和视频生成
    - MultimodalProcessor: 多模态处理器，支持多种文件类型处理

功能特点:
    - 使用 FFmpeg 进行音频提取和处理
    - 使用 Whisper 进行语音转文字
    - 集成智谱 AI 的图像和视频生成模型
    - 支持繁简中文转换
"""
import logging

logger = logging.getLogger(__name__)

from .audio_processor import AudioProcessor
from .media_generator import MediaGenerator
from .multimodal_processor import MultimodalProcessor

__all__ = [
    "AudioProcessor",
    "MediaGenerator",
    "MultimodalProcessor",
]

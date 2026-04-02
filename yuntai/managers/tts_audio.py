"""
TTS音频播放器模块
=================

负责音频播放、合并、以及 PyAudio 封装，使用 pathlib 进行跨平台路径处理。

主要功能:
    - play_audio_file: 播放指定的音频文件
    - stop_current_audio_playback: 停止当前正在播放的音频
    - merge_audio_segments: 合并多个音频文件
    - cleanup: 清理音频播放器资源

使用示例:
    >>> from yuntai.managers import TTSAudioPlayer
    >>> player = TTSAudioPlayer(default_tts_config)
    >>> player.play_audio_file("output.wav")
"""
from __future__ import annotations

import datetime
import logging
import re
import threading
import traceback
from pathlib import Path
from typing import Any

import pyaudio
import wave

logger = logging.getLogger(__name__)


class TTSAudioPlayer:
    """
    TTS 音频播放器
    
    负责音频播放、合并以及 PyAudio 封装。
    
    Attributes:
        default_tts_config: 默认 TTS 配置
        audio_player: PyAudio 实例
        audio_play_lock: 音频播放锁
        is_playing_audio: 是否正在播放音频
        is_playing_audio_lock: 播放状态锁
        tts_segments: TTS 音频片段列表
        tts_segments_lock: 音频片段锁
        can_merge_audio: 是否支持音频合并
        
    Args:
        default_tts_config: 默认 TTS 配置字典
    """

    def __init__(self, default_tts_config: dict[str, Any]) -> None:
        """
        初始化音频播放器

        Args:
            default_tts_config: 默认 TTS 配置
        """
        self.default_tts_config: dict[str, Any] = default_tts_config

        self.audio_player: pyaudio.PyAudio | None = None
        self.audio_play_lock: threading.Lock = threading.Lock()

        self.is_playing_audio: bool = False
        self.is_playing_audio_lock: threading.Lock = threading.Lock()

        self.tts_segments: list[Any] = []
        self.tts_segments_lock: threading.Lock = threading.Lock()

        self.can_merge_audio: bool = self._check_merge_dependencies()

        self._init_audio_player()
        logger.debug("TTSAudioPlayer 初始化完成")

    def _check_merge_dependencies(self) -> bool:
        """
        检查音频合并所需的依赖
        
        Returns:
            如果 numpy 和 soundfile 都已安装返回 True
        """
        try:
            import numpy
            import soundfile
            logger.debug("音频合并依赖检查通过")
            return True
        except ImportError:
            logger.warning("音频合并功能需要额外依赖: pip install numpy soundfile")
            logger.warning("音频合并依赖缺失")
            return False

    def _init_audio_player(self) -> None:
        """初始化音频播放器"""
        try:
            self.audio_player = pyaudio.PyAudio()
            logger.debug("PyAudio 初始化成功")
        except Exception as e:
            logger.error("初始化音频播放失败: %s", str(e))
            logger.error("PyAudio 初始化失败: %s", str(e))
            self.audio_player = None

    def play_audio_file(self, audio_path: str) -> None:
        """
        播放指定的音频文件
        
        Args:
            audio_path: 音频文件路径
        """
        if not self.audio_player:
            logger.warning("音频播放器未初始化")
            return

        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                logger.debug("跳过播放请求：已有音频正在播放")
                return
            self.is_playing_audio = True

        audio_file = Path(audio_path)
        if not audio_file.exists():
            logger.warning("音频文件不存在: %s", audio_path)
            with self.is_playing_audio_lock:
                self.is_playing_audio = False
            return

        try:
            logger.debug("开始播放音频: %s", audio_path)
            wf: wave.Wave_read = wave.open(str(audio_file), 'rb')

            stream = self.audio_player.open(
                format=self.audio_player.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            chunk: int = 1024
            data: bytes = wf.readframes(chunk)

            while data:
                with self.is_playing_audio_lock:
                    if not self.is_playing_audio:
                        break
                stream.write(data)
                data = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
            wf.close()
            logger.debug("音频播放完成: %s", audio_path)

        except Exception as e:
            logger.error("播放失败: %s", str(e))
            logger.exception("音频播放失败: %s", str(e))
        finally:
            with self.is_playing_audio_lock:
                self.is_playing_audio = False

    def stop_current_audio_playback(self) -> bool:
        """
        停止当前正在播放的音频
        
        Returns:
            如果有音频正在播放并成功停止返回 True，否则返回 False
        """
        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                self.is_playing_audio = False
                logger.info("正在停止音频播放")
                logger.debug("停止音频播放")
                return True
            else:
                return False

    def merge_audio_segments(self, audio_files: list[str]) -> str | None:
        """
        合并多个音频文件
        
        Args:
            audio_files: 音频文件路径列表
            
        Returns:
            合并后的音频文件路径，如果失败返回 None
        """
        if not audio_files:
            return None

        if len(audio_files) == 1:
            return audio_files[0]

        try:
            import numpy as np
            import soundfile as sf

            all_audio_data: list[Any] = []
            all_sample_rates: list[int] = []

            for i, audio_file in enumerate(audio_files):
                audio_path = Path(audio_file)
                if audio_path.exists():
                    data, samplerate = sf.read(str(audio_path))
                    all_audio_data.append(data)
                    all_sample_rates.append(samplerate)
                else:
                    logger.warning("合并时文件不存在: %s", audio_file)

            if not all_audio_data:
                return None

            if len(set(all_sample_rates)) > 1:
                logger.warning("采样率不一致，使用第一个文件的采样率: %s", all_sample_rates[0])
                logger.warning("采样率不一致: %s", all_sample_rates)

            target_samplerate: int = all_sample_rates[0]

            if len(all_audio_data[0].shape) == 2:
                merged_data = np.vstack(all_audio_data)
            else:
                merged_data = np.concatenate(all_audio_data)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            first_audio_file = audio_files[0]
            first_audio_name = Path(first_audio_file).name

            match = re.match(r'(.+)_\d{8}_\d{6}', first_audio_name)
            if match:
                ref_audio_base = match.group(1)
            else:
                ref_audio_base = "tts_merged"

            output_path = Path(self.default_tts_config["output_path"])
            output_wav = output_path / f"{ref_audio_base}_merged_{timestamp}.wav"

            sf.write(str(output_wav), merged_data, target_samplerate)
            logger.debug("音频合并完成: %s", output_wav)

            return str(output_wav)

        except ImportError as e:
            logger.error("音频合并需要soundfile和numpy库: %s", str(e))
            logger.error("请安装: pip install soundfile numpy")
            logger.error("音频合并依赖缺失: %s", str(e))
            return audio_files[0]

        except Exception as e:
            logger.error("音频合并失败: %s", str(e))
            logger.exception("音频合并失败: %s", str(e))
            return audio_files[0]

    def cleanup(self) -> None:
        """清理音频播放器资源"""
        logger.info("清理音频播放器资源...")

        self.stop_current_audio_playback()

        if self.audio_player:
            try:
                self.audio_player.terminate()
            except OSError as e:
                logger.debug("终止音频播放器失败: %s", str(e))

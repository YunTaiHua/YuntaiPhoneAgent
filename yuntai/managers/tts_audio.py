"""
TTS音频播放器 - 负责音频播放、合并、以及PyAudio封装
使用 pathlib 进行跨平台路径处理
"""

from __future__ import annotations

import logging
import threading
import traceback
import re
import datetime
from typing import Any

from pathlib import Path
import pyaudio
import wave

logger = logging.getLogger(__name__)


class TTSAudioPlayer:
    """TTS音频播放器"""

    def __init__(self, default_tts_config: dict[str, Any]) -> None:
        """
        初始化音频播放器

        Args:
            default_tts_config: 默认TTS配置
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

    def _check_merge_dependencies(self) -> bool:
        """检查音频合并所需的依赖"""
        try:
            import numpy
            import soundfile
            return True
        except ImportError:
            print("⚠️ 音频合并功能需要额外依赖: pip install numpy soundfile")
            return False

    def _init_audio_player(self) -> None:
        """初始化音频播放器"""
        try:
            self.audio_player = pyaudio.PyAudio()
            print("✅ 音频播放器初始化成功")
        except Exception as e:
            print(f"❌ 初始化音频播放失败: {e}")
            self.audio_player = None

    def play_audio_file(self, audio_path: str) -> None:
        """播放指定的音频文件"""
        if not self.audio_player:
            print("❌ 音频播放器未初始化")
            return

        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                print("⚠️ 已有音频正在播放，跳过本次播放请求")
                return
            self.is_playing_audio = True

        audio_file = Path(audio_path)
        if not audio_file.exists():
            print(f"❌ 音频文件不存在：{audio_path}")
            with self.is_playing_audio_lock:
                self.is_playing_audio = False
            return

        try:
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

        except Exception as e:
            print(f"❌ 播放失败：{e}")
            traceback.print_exc()
        finally:
            with self.is_playing_audio_lock:
                self.is_playing_audio = False

    def stop_current_audio_playback(self) -> bool:
        """停止当前正在播放的音频"""
        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                self.is_playing_audio = False
                print("⏹️ 正在停止音频播放...")
                return True
            else:
                return False

    def merge_audio_segments(self, audio_files: list[str]) -> str | None:
        """
        合并多个音频文件

        Args:
            audio_files: 音频文件路径列表

        Returns:
            合并后的音频文件路径，如果失败返回None
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
                    print(f"⚠️  文件不存在: {audio_file}")

            if not all_audio_data:
                return None

            if len(set(all_sample_rates)) > 1:
                print(f"⚠️  采样率不一致，使用第一个文件的采样率: {all_sample_rates[0]}")

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

            return str(output_wav)

        except ImportError as e:
            print(f"❌ 音频合并需要soundfile和numpy库: {e}")
            print("💡 请安装: pip install soundfile numpy")
            return audio_files[0]

        except Exception as e:
            print(f"❌ 音频合并失败: {e}")
            import traceback
            traceback.print_exc()
            return audio_files[0]

    def cleanup(self) -> None:
        """清理音频播放器资源"""
        logger.info("清理音频播放器资源...")

        self.stop_current_audio_playback()

        if self.audio_player:
            try:
                self.audio_player.terminate()
            except OSError as e:
                logger.debug(f"终止音频播放器失败: {e}")

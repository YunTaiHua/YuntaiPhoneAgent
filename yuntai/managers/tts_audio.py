"""
TTS音频播放器 - 负责音频播放、合并、以及PyAudio封装
"""

import os
import threading
import traceback
from typing import List, Optional
import pyaudio
import wave
import datetime


class TTSAudioPlayer:
    """TTS音频播放器"""

    def __init__(self, default_tts_config: dict):
        """
        初始化音频播放器

        Args:
            default_tts_config: 默认TTS配置
        """
        self.default_tts_config = default_tts_config

        # 音频播放器
        self.audio_player = None
        self.audio_play_lock = threading.Lock()

        # 播放状态
        self.is_playing_audio = False
        self.is_playing_audio_lock = threading.Lock()

        # 分段合成相关
        self.tts_segments = []
        self.tts_segments_lock = threading.Lock()

        # 检查音频合并依赖
        self.can_merge_audio = self._check_merge_dependencies()

        # 初始化音频播放器
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

    def _init_audio_player(self):
        """初始化音频播放器"""
        try:
            self.audio_player = pyaudio.PyAudio()
            print("✅ 音频播放器初始化成功")
        except Exception as e:
            print(f"❌ 初始化音频播放失败: {e}")
            self.audio_player = None

    def play_audio_file(self, audio_path: str):
        """播放指定的音频文件"""
        if not self.audio_player:
            print("❌ 音频播放器未初始化")
            return

        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                print("⚠️ 已有音频正在播放，跳过本次播放请求")
                return
            self.is_playing_audio = True

        if not os.path.exists(audio_path):
            print(f"❌ 音频文件不存在：{audio_path}")
            with self.is_playing_audio_lock:
                self.is_playing_audio = False
            return

        try:
            # 打开音频文件
            wf = wave.open(audio_path, 'rb')

            # 创建音频流
            stream = self.audio_player.open(
                format=self.audio_player.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            # 分块播放音频（检查播放状态）
            chunk = 1024
            data = wf.readframes(chunk)

            while data:
                with self.is_playing_audio_lock:
                    if not self.is_playing_audio:
                        break
                stream.write(data)
                data = wf.readframes(chunk)

            # 清理资源
            stream.stop_stream()
            stream.close()
            wf.close()

        except Exception as e:
            print(f"❌ 播放失败：{e}")
            traceback.print_exc()
        finally:
            # 释放播放锁
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

    def merge_audio_segments(self, audio_files: List[str]) -> Optional[str]:
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
            return audio_files[0]  # 只有一个文件，不需要合并

        try:
            import numpy as np
            import soundfile as sf

            # print(f"🔊 开始合并 {len(audio_files)} 个音频文件...")

            # 读取所有音频数据
            all_audio_data = []
            all_sample_rates = []

            for i, audio_file in enumerate(audio_files):
                if os.path.exists(audio_file):
                    data, samplerate = sf.read(audio_file)
                    all_audio_data.append(data)
                    all_sample_rates.append(samplerate)
                else:
                    print(f"⚠️  文件不存在: {audio_file}")

            if not all_audio_data:
                return None

            # 检查采样率是否一致
            if len(set(all_sample_rates)) > 1:
                print(f"⚠️  采样率不一致，使用第一个文件的采样率: {all_sample_rates[0]}")

            target_samplerate = all_sample_rates[0]

            # 合并音频数据
            # 对于立体声音频，需要特殊处理
            if len(all_audio_data[0].shape) == 2:  # 立体声
                merged_data = np.vstack(all_audio_data)
            else:  # 单声道
                merged_data = np.concatenate(all_audio_data)

            # 保存合并后的音频 - 使用与普通合成一致的格式
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # 从第一个音频文件名中提取参考音频名称
            first_audio_file = audio_files[0]
            first_audio_name = os.path.basename(first_audio_file)

            # 提取参考音频名称（去掉时间戳部分）
            # 格式如: "ref_audio_name_20250119_123456.wav"
            import re
            match = re.match(r'(.+)_\d{8}_\d{6}', first_audio_name)
            if match:
                ref_audio_base = match.group(1)
            else:
                # 如果无法解析，使用默认名称
                ref_audio_base = "tts_merged"

            output_wav = os.path.join(
                self.default_tts_config["output_path"],
                f"{ref_audio_base}_merged_{timestamp}.wav"
            )

            sf.write(output_wav, merged_data, target_samplerate)

            return output_wav

        except ImportError as e:
            print(f"❌ 音频合并需要soundfile和numpy库: {e}")
            print("💡 请安装: pip install soundfile numpy")
            # 返回第一个文件作为备选
            return audio_files[0]

        except Exception as e:
            print(f"❌ 音频合并失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回第一个文件作为备选
            return audio_files[0]

    def cleanup(self):
        """清理音频播放器资源"""
        print("🧹 清理音频播放器资源...")

        # 停止音频播放
        self.stop_current_audio_playback()

        # 清理音频播放器
        if self.audio_player:
            try:
                self.audio_player.terminate()
            except:
                pass

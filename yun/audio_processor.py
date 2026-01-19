"""
音频处理器模块
使用 FFmpeg 和 Whisper 处理音频
支持从视频中提取音频和单独处理音频文件
支持繁简中文转换
"""

import os
import subprocess
import tempfile
from typing import Optional, Tuple
import threading
import time

from .config import (
    FFMPEG_PATH,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_DEVICE,
    WHISPER_CONVERT_TO_SIMPLIFIED
)


class AudioProcessor:
    """音频处理器类"""

    def __init__(self, ffmpeg_path: str = None):
        """
        初始化音频处理器

        Args:
            ffmpeg_path: FFmpeg 可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        self.whisper_model = None
        self.whisper_lock = threading.Lock()
        self.model_loaded = False

        # 临时文件目录
        self.temp_dir = tempfile.gettempdir()

        # 繁简转换器
        self.text_converter = None

    def _convert_to_simplified_chinese(self, text: str) -> str:
        """
        将繁体中文转换为简体中文

        Args:
            text: 待转换的文本

        Returns:
            转换后的简体中文文本
        """
        if not WHISPER_CONVERT_TO_SIMPLIFIED or not text:
            return text

        try:
            # 延迟加载转换器
            if self.text_converter is None:
                # 尝试使用 opencc
                try:
                    import opencc
                    # 繁体转简体
                    self.text_converter = opencc.OpenCC('t2s.json')
                    #print("\n✅ 使用 OpenCC 进行繁简转换")
                    return self.text_converter.convert(text)
                except ImportError:
                    print("\n⚠️  OpenCC 未安装，尝试使用 zhconv")

                # 尝试使用 zhconv
                try:
                    from zhconv import convert
                    self.text_converter = convert
                    #print("\n✅ 使用 zhconv 进行繁简转换")
                    return self.text_converter(text, 'zh-cn')
                except ImportError:
                    print("\n⚠️  zhconv 未安装，跳过繁简转换")
                    self.text_converter = lambda x: x

            # 执行转换
            if hasattr(self.text_converter, 'convert'):
                # OpenCC 格式
                return self.text_converter.convert(text)
            else:
                # zhconv 格式
                return self.text_converter(text, 'zh-cn')

        except Exception as e:
            print(f"⚠️  繁简转换失败: {e}")
            return text

    def check_ffmpeg(self) -> Tuple[bool, str]:
        """
        检查 FFmpeg 是否可用

        Returns:
            (是否可用, 错误信息)
        """
        try:
            if not self.ffmpeg_path or not os.path.exists(self.ffmpeg_path):
                return False, f"FFmpeg 路径不存在: {self.ffmpeg_path}"

            # 测试 FFmpeg 是否可执行
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=5,
                text=True
            )

            if result.returncode == 0:
                return True, ""
            else:
                return False, f"FFmpeg 执行失败: {result.stderr}"

        except Exception as e:
            return False, f"FFmpeg 检查失败: {str(e)}"

    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> Tuple[bool, str]:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径（可选）

        Returns:
            (是否成功, 音频文件路径或错误信息)
        """
        try:
            # 检查 FFmpeg
            ffmpeg_ok, error_msg = self.check_ffmpeg()
            if not ffmpeg_ok:
                return False, error_msg

            # 检查视频文件
            if not os.path.exists(video_path):
                return False, f"视频文件不存在: {video_path}"

            # 生成输出路径
            if not output_path:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(self.temp_dir, f"{video_name}_audio.wav")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 使用 FFmpeg 提取音频
            print(f"\n🎵 正在从视频中提取音频: {os.path.basename(video_path)}")

            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vn",  # 不要视频流
                "-acodec", "pcm_s16le",  # 使用 PCM 16-bit 编码（Whisper 推荐格式）
                "-ar", "16000",  # 采样率 16kHz（Whisper 推荐）
                "-ac", "1",  # 单声道
                "-y",  # 覆盖已存在文件
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                print(f"\n✅ 音频提取成功: {output_path}")
                return True, output_path
            else:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                return False, f"音频提取失败: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, "音频提取超时（超过5分钟）"
        except Exception as e:
            return False, f"音频提取异常: {str(e)}"

    def load_whisper_model(self, model_size: str = "small", device: str = "cpu") -> Tuple[bool, str]:
        """
        加载 Whisper 模型（延迟加载）

        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
            device: 运行设备 (cpu, cuda)

        Returns:
            (是否成功, 错误信息)
        """
        try:
            with self.whisper_lock:
                if self.model_loaded:
                    return True, ""

                #print(f"\n🔄 正在加载 Whisper 模型 ({model_size})...")

                # 导入 Whisper（延迟加载）
                import whisper

                # 加载模型
                self.whisper_model = whisper.load_model(model_size, device=device)

                self.model_loaded = True
                #print(f"\n✅ Whisper 模型加载成功: {model_size}")

                return True, ""

        except ImportError:
            return False, "Whisper 库未安装，请运行: pip install openai-whisper"
        except Exception as e:
            return False, f"Whisper 模型加载失败: {str(e)}"

    def transcribe_audio(self, audio_path: str, language: str = None) -> Tuple[bool, str]:
        """
        转录音频为文本

        Args:
            audio_path: 音频文件路径
            language: 语言代码（如 "zh", "en"），None 表示自动检测

        Returns:
            (是否成功, 转录文本或错误信息)
        """
        try:
            # 检查音频文件
            if not os.path.exists(audio_path):
                return False, f"音频文件不存在: {audio_path}"

            # 确保模型已加载
            if not self.model_loaded:
                model_ok, error_msg = self.load_whisper_model()
                if not model_ok:
                    return False, error_msg

            print(f"\n🎙️正在转录音频: {os.path.basename(audio_path)}")

            # 转录音频
            result = self.whisper_model.transcribe(
                audio_path,
                language=language,
                fp16=False  # CPU 模式不使用 FP16
            )

            transcription_text = result["text"].strip()

            # 繁简转换
            transcription_text = self._convert_to_simplified_chinese(transcription_text)

            if transcription_text:
                #print(f"\n✅ 音频转录成功，文本长度: {len(transcription_text)} 字符")
                return True, transcription_text
            else:
                return False, "音频转录结果为空"

        except Exception as e:
            return False, f"音频转录失败: {str(e)}"

    def process_video_with_audio(self, video_path: str, prompt: str = None,
                                language: str = "zh") -> Tuple[bool, dict]:
        """
        处理视频并提取音频转录

        Args:
            video_path: 视频文件路径
            prompt: 用户提示词
            language: 音频语言代码

        Returns:
            (是否成功, 包含视频和音频信息的字典)
        """
        try:
            # 检查视频文件
            if not os.path.exists(video_path):
                return False, {"error": f"视频文件不存在: {video_path}"}

            # 1. 提取音频
            extract_ok, audio_path = self.extract_audio_from_video(video_path)
            if not extract_ok:
                return False, {"error": f"音频提取失败: {audio_path}"}

            # 2. 转录音频
            transcribe_ok, transcription = self.transcribe_audio(audio_path, language)
            if not transcribe_ok:
                return False, {"error": f"音频转录失败: {transcription}"}

            # 3. 返回完整信息
            result = {
                "video_path": video_path,
                "audio_path": audio_path,
                "audio_transcription": transcription,
                "audio_language": language,
                "has_audio": True,
                "prompt": prompt
            }

            print(f"\n✅ 视频+音频处理完成")
            #print(f"\n📝 音频内容: {transcription[:100]}..." if len(transcription) > 100 else f"📝 音频内容: {transcription}")

            return True, result

        except Exception as e:
            return False, {"error": f"视频+音频处理失败: {str(e)}"}

    def process_audio_only(self, audio_path: str, prompt: str = None,
                          language: str = "zh") -> Tuple[bool, dict]:
        """
        单独处理音频文件

        Args:
            audio_path: 音频文件路径
            prompt: 用户提示词
            language: 音频语言代码

        Returns:
            (是否成功, 包含音频信息的字典)
        """
        try:
            # 检查音频文件
            if not os.path.exists(audio_path):
                return False, {"error": f"音频文件不存在: {audio_path}"}

            # 1. 转录音频
            transcribe_ok, transcription = self.transcribe_audio(audio_path, language)
            if not transcribe_ok:
                return False, {"error": f"音频转录失败: {transcription}"}

            # 2. 返回完整信息
            result = {
                "audio_path": audio_path,
                "audio_transcription": transcription,
                "audio_language": language,
                "prompt": prompt
            }

            print(f"\n✅ 音频处理完成")
            #print(f"\n📝 音频内容: {transcription[:100]}..." if len(transcription) > 100 else f"📝 音频内容: {transcription}")

            return True, result

        except Exception as e:
            return False, {"error": f"音频处理失败: {str(e)}"}

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """
        清理旧的临时音频文件

        Args:
            older_than_hours: 清理多少小时前的文件
        """
        try:
            import time as time_module
            current_time = time_module.time()

            # 查找临时目录中的音频文件
            temp_audio_files = [
                f for f in os.listdir(self.temp_dir)
                if f.endswith('_audio.wav') or f.endswith('_extracted.wav')
            ]

            deleted_count = 0
            for filename in temp_audio_files:
                filepath = os.path.join(self.temp_dir, filename)

                # 检查文件年龄
                file_time = os.path.getmtime(filepath)
                age_hours = (current_time - file_time) / 3600

                if age_hours > older_than_hours:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"\n🗑️清理临时文件: {filename}")
                    except Exception as e:
                        print(f"\n⚠️清理失败 {filename}: {e}")

            if deleted_count > 0:
                print(f"\n✅清理了 {deleted_count} 个临时音频文件")

        except Exception as e:
            print(f"\n⚠️ 清理临时文件失败: {e}")

"""
音频处理器模块
使用 FFmpeg 和 Whisper 处理音频
支持从视频中提取音频和单独处理音频文件
支持繁简中文转换
使用 pathlib 进行跨平台路径处理
"""

import subprocess
import tempfile
import threading
import time
from pathlib import Path

from yuntai.core.config import (
    FFMPEG_PATH,
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_DEVICE,
    WHISPER_CONVERT_TO_SIMPLIFIED
)


class AudioProcessor:
    """音频处理器类"""

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        """
        初始化音频处理器

        Args:
            ffmpeg_path: FFmpeg 可执行文件路径
        """
        self.ffmpeg_path = Path(ffmpeg_path) if ffmpeg_path else (Path(FFMPEG_PATH) if FFMPEG_PATH else None)
        self.whisper_model = None
        self.whisper_lock = threading.Lock()
        self.model_loaded = False

        self.temp_dir = Path(tempfile.gettempdir())

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
            if self.text_converter is None:
                try:
                    import opencc
                    self.text_converter = opencc.OpenCC('t2s.json')
                    return self.text_converter.convert(text)
                except ImportError:
                    print("\n⚠️  OpenCC 未安装，尝试使用 zhconv")

                try:
                    from zhconv import convert
                    self.text_converter = convert
                    return self.text_converter(text, 'zh-cn')
                except ImportError:
                    print("\n⚠️  zhconv 未安装，跳过繁简转换")
                    self.text_converter = lambda x: x

            if hasattr(self.text_converter, 'convert'):
                return self.text_converter.convert(text)
            else:
                return self.text_converter(text, 'zh-cn')

        except Exception as e:
            print(f"⚠️  繁简转换失败: {e}")
            return text

    def check_ffmpeg(self) -> tuple[bool, str]:
        """
        检查 FFmpeg 是否可用

        Returns:
            (是否可用, 错误信息)
        """
        try:
            if not self.ffmpeg_path or not self.ffmpeg_path.exists():
                return False, f"FFmpeg 路径不存在: {self.ffmpeg_path}"

            result = subprocess.run(
                [str(self.ffmpeg_path), "-version"],
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

    def extract_audio_from_video(self, video_path: str, output_path: str | None = None) -> tuple[bool, str]:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径（可选）

        Returns:
            (是否成功, 音频文件路径或错误信息)
        """
        try:
            ffmpeg_ok, error_msg = self.check_ffmpeg()
            if not ffmpeg_ok:
                return False, error_msg

            video_file = Path(video_path)
            if not video_file.exists():
                return False, f"视频文件不存在: {video_path}"

            if not output_path:
                video_name = video_file.stem
                output_path = self.temp_dir / f"{video_name}_audio.wav"
            else:
                output_path = Path(output_path)

            output_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"🎵 正在从视频中提取音频: {video_file.name}")

            cmd = [
                str(self.ffmpeg_path),
                "-i", str(video_file),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                "-y",
                str(output_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300
            )

            if result.returncode == 0:
                print(f"✅ 音频提取成功: {output_path}")
                return True, str(output_path)
            else:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                return False, f"音频提取失败: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, "音频提取超时（超过5分钟）"
        except Exception as e:
            return False, f"音频提取异常: {str(e)}"

    def load_whisper_model(self, model_size: str = "small", device: str = "cpu") -> tuple[bool, str]:
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

                import whisper

                self.whisper_model = whisper.load_model(model_size, device=device)

                self.model_loaded = True

                return True, ""

        except ImportError:
            return False, "Whisper 库未安装，请运行: pip install openai-whisper"
        except Exception as e:
            return False, f"Whisper 模型加载失败: {str(e)}"

    def transcribe_audio(self, audio_path: str, language: str | None = None) -> tuple[bool, str]:
        """
        转录音频为文本

        Args:
            audio_path: 音频文件路径
            language: 语言代码（如 "zh", "en"），None 表示自动检测

        Returns:
            (是否成功, 转录文本或错误信息)
        """
        try:
            audio_file = Path(audio_path)
            if not audio_file.exists():
                return False, f"音频文件不存在: {audio_path}"

            if not self.model_loaded:
                model_ok, error_msg = self.load_whisper_model()
                if not model_ok:
                    return False, error_msg

            print(f"🎙️正在转录音频: {audio_file.name}")

            result = self.whisper_model.transcribe(
                audio_path,
                language=language,
                fp16=False
            )

            transcription_text = result["text"].strip()

            transcription_text = self._convert_to_simplified_chinese(transcription_text)

            if transcription_text:
                return True, transcription_text
            else:
                return False, "音频转录结果为空"

        except Exception as e:
            return False, f"音频转录失败: {str(e)}"

    def process_video_with_audio(self, video_path: str, prompt: str | None = None,
                                language: str = "zh") -> tuple[bool, dict]:
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
            video_file = Path(video_path)
            if not video_file.exists():
                return False, {"error": f"视频文件不存在: {video_path}"}

            extract_ok, audio_path = self.extract_audio_from_video(video_path)
            if not extract_ok:
                return False, {"error": f"音频提取失败: {audio_path}"}

            transcribe_ok, transcription = self.transcribe_audio(audio_path, language)
            if not transcribe_ok:
                return False, {"error": f"音频转录失败: {transcription}"}

            result = {
                "video_path": video_path,
                "audio_path": audio_path,
                "audio_transcription": transcription,
                "audio_language": language,
                "has_audio": True,
                "prompt": prompt
            }

            print(f"✅ 视频+音频处理完成")

            return True, result

        except Exception as e:
            return False, {"error": f"视频+音频处理失败: {str(e)}"}

    def process_audio_only(self, audio_path: str, prompt: str | None = None,
                          language: str = "zh") -> tuple[bool, dict]:
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
            audio_file = Path(audio_path)
            if not audio_file.exists():
                return False, {"error": f"音频文件不存在: {audio_path}"}

            transcribe_ok, transcription = self.transcribe_audio(audio_path, language)
            if not transcribe_ok:
                return False, {"error": f"音频转录失败: {transcription}"}

            result = {
                "audio_path": audio_path,
                "audio_transcription": transcription,
                "audio_language": language,
                "prompt": prompt
            }

            print(f"✅ 音频处理完成")

            return True, result

        except Exception as e:
            return False, {"error": f"音频处理失败: {str(e)}"}

    def cleanup_temp_files(self, older_than_hours: int = 24) -> None:
        """
        清理旧的临时音频文件

        Args:
            older_than_hours: 清理多少小时前的文件
        """
        try:
            import time as time_module
            current_time = time_module.time()

            temp_audio_files = [
                f for f in self.temp_dir.iterdir()
                if f.is_file() and (f.name.endswith('_audio.wav') or f.name.endswith('_extracted.wav'))
            ]

            deleted_count = 0
            for filepath in temp_audio_files:
                file_time = filepath.stat().st_mtime
                age_hours = (current_time - file_time) / 3600

                if age_hours > older_than_hours:
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        print(f"🗑️清理临时文件: {filepath.name}")
                    except Exception as e:
                        print(f"⚠️清理失败 {filepath.name}: {e}")

            if deleted_count > 0:
                print(f"✅清理了 {deleted_count} 个临时音频文件")

        except Exception as e:
            print(f"⚠️ 清理临时文件失败: {e}")

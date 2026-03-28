"""
多模态处理器模块
================

使用 zhipuai 库处理多模态输入，支持图像、视频、音频、文件上传和处理。
使用 ZHIPU_MULTIMODAL_MODEL 模型，支持 FFmpeg 和 Whisper 进行音频处理。

主要功能:
    - 图像、视频、音频处理
    - 文档解析（使用 markitdown）
    - Base64 文件编码
    - 多模态消息准备

使用示例:
    >>> from yuntai.processors import MultimodalProcessor
    >>> processor = MultimodalProcessor()
    >>> success, text, audio_result = processor.process_with_files(
    ...     "描述这张图片",
    ...     ["image.jpg"]
    ... )
"""
from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING

from zhipuai import ZhipuAI

from yuntai.core.config import (
    ZHIPU_API_KEY, ZHIPU_MULTIMODAL_MODEL, MAX_FILE_SIZE,
    FFMPEG_PATH, WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE,
    ALLOWED_AUDIO_EXTENSIONS
)

if TYPE_CHECKING:
    from yuntai.processors.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class MultimodalProcessor:
    """
    多模态处理器类
    
    使用 zhipuai 库处理多模态输入，支持音频处理。
    
    Attributes:
        api_key: 智谱 API 密钥
        model: 多模态模型名称
        client: ZhipuAI 客户端实例
        allowed_image_extensions: 允许的图像扩展名
        allowed_video_extensions: 允许的视频扩展名
        allowed_file_extensions: 允许的文件扩展名
        allowed_audio_extensions: 允许的音频扩展名
        max_file_size: 最大文件大小
        audio_processor: 音频处理器实例（延迟初始化）
        
    Args:
        api_key: 智谱 API 密钥，可选
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        初始化多模态处理器

        Args:
            api_key: 智谱API密钥，如果为None则使用配置中的密钥
        """
        self.api_key: str = api_key or ZHIPU_API_KEY
        self.model: str = ZHIPU_MULTIMODAL_MODEL

        self.client: ZhipuAI = ZhipuAI(api_key=self.api_key)

        from yuntai.core.config import (
            ALLOWED_IMAGE_EXTENSIONS,
            ALLOWED_VIDEO_EXTENSIONS,
            ALLOWED_FILE_EXTENSIONS,
            MAX_FILE_SIZE
        )
        self.allowed_image_extensions: tuple[str, ...] = ALLOWED_IMAGE_EXTENSIONS
        self.allowed_video_extensions: tuple[str, ...] = ALLOWED_VIDEO_EXTENSIONS
        self.allowed_file_extensions: tuple[str, ...] = ALLOWED_FILE_EXTENSIONS
        self.allowed_audio_extensions: tuple[str, ...] = ALLOWED_AUDIO_EXTENSIONS
        self.max_file_size: int = MAX_FILE_SIZE

        self.audio_processor: AudioProcessor | None = None
        logger.debug(f"MultimodalProcessor 初始化完成, model={self.model}")

    def get_audio_processor(self) -> AudioProcessor:
        """
        延迟初始化音频处理器
        
        Returns:
            AudioProcessor 实例
        """
        if self.audio_processor is None:
            from yuntai.processors.audio_processor import AudioProcessor
            self.audio_processor = AudioProcessor(ffmpeg_path=FFMPEG_PATH)
            logger.debug("音频处理器延迟初始化完成")
        return self.audio_processor

    def parse_document_to_text(self, file_path: str) -> str | None:
        """
        使用 markitdown 解析文档为文本
        
        支持所有 markitdown 支持的格式。
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            解析后的文本内容，失败返回 None
        """
        try:
            from markitdown import MarkItDown

            if not hasattr(self, '_markitdown'):
                self._markitdown = MarkItDown()

            result = self._markitdown.convert(file_path)
            text_content = result.text_content

            if len(text_content) > 10000:
                text_content = text_content[:10000] + "\n\n[文件内容过长，已截断]"

            logger.debug(f"文档解析成功: {file_path}")
            return text_content

        except Exception as e:
            logger.warning(f"markitdown 解析文档失败 {file_path}: {e}")
            return None

    def encode_file_to_base64(self, file_path: str) -> str | None:
        """
        将文件编码为 base64

        Args:
            file_path: 文件路径

        Returns:
            base64 编码的字符串，失败返回 None
        """
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                logger.warning(f"文件太大: {file_path} ({file_size / 1024 / 1024:.2f}MB)")
                return None

            with open(file_path, 'rb') as file:
                file_content = file.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
                return base64_content
        except Exception as e:
            logger.error(f"编码文件失败 {file_path}: {e}")
            return None

    def get_file_type(self, file_path: str) -> tuple[str, str]:
        """
        获取文件类型和 MIME 类型

        Args:
            file_path: 文件路径

        Returns:
            元组 (文件类型, MIME类型)
        """
        ext = Path(file_path).suffix.lower()

        if ext in self.allowed_audio_extensions:
            mime_type = mimetypes.guess_type(file_path)[0] or "audio/mpeg"
            return "audio", mime_type

        if ext in self.allowed_image_extensions:
            mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
            return "image", mime_type

        elif ext in self.allowed_video_extensions:
            mime_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
            return "video", mime_type

        elif ext in ['.txt', '.py', '.csv', '.xls', '.xlsx', '.docx', '.pdf', '.ppt', '.pptx', '.html', '.js', '.htm', '.rss', '.atom', '.json', '.xml', '.java', '.ipynb']:
            return "text", "text/plain"

        else:
            return "file", "application/octet-stream"

    def prepare_multimodal_messages(
            self,
            text: str,
            file_paths: list[str] | None = None,
            history: list[dict] | None = None
    ) -> tuple[list[dict], dict | None]:
        """
        准备多模态消息
        
        根据官方文档格式准备消息，支持音频处理和视频音频同步处理。

        Args:
            text: 用户输入的文本
            file_paths: 文件路径列表
            history: 历史对话记录

        Returns:
            元组 (消息列表, 音频处理结果字典)
        """
        messages = []

        if history:
            messages.extend(history)

        current_message = {
            "role": "user",
            "content": []
        }

        audio_result = None

        if file_paths:
            for file_path in file_paths:
                base64_content = self.encode_file_to_base64(file_path)
                if base64_content:
                    file_type, mime_type = self.get_file_type(file_path)
                    file_name = Path(file_path).name

                    print(f"📄 准备文件: {file_name} (类型: {file_type})")
                    logger.debug(f"准备文件: {file_name}, 类型: {file_type}")

                    if file_type == "video":
                        processor = self.get_audio_processor()
                        success, result = processor.process_video_with_audio(file_path, text, WHISPER_LANGUAGE)

                        if success:
                            audio_result = result

                            video_block = {
                                "type": "video_url",
                                "video_url": {
                                    "url": base64_content
                                }
                            }
                            current_message["content"].append(video_block)

                            audio_transcription = result.get("audio_transcription", "")
                            if audio_transcription:
                                audio_text = f"[视频中的音频内容]\n{audio_transcription}"
                                current_message["content"].append({
                                    "type": "text",
                                    "text": audio_text
                                })
                                print(f"✅ 已添加视频+音频内容")
                        else:
                            logger.warning(f"音频处理失败，仅使用视频: {result.get('error', 'unknown error')}")
                            current_message["content"].append({
                                "type": "video_url",
                                "video_url": {
                                    "url": base64_content
                                }
                            })

                    elif file_type == "audio":
                        processor = self.get_audio_processor()
                        success, result = processor.process_audio_only(file_path, text, WHISPER_LANGUAGE)

                        if success:
                            audio_result = result
                            audio_transcription = result.get("audio_transcription", "")

                            if audio_transcription:
                                audio_text = f"[音频内容]\n{audio_transcription}"
                                current_message["content"].append({
                                    "type": "text",
                                    "text": audio_text
                                })
                        else:
                            logger.warning(f"音频处理失败: {result.get('error', 'unknown error')}")
                            current_message["content"].append({
                                "type": "text",
                                "text": f"[音频处理失败: {result.get('error', 'unknown error')}]"
                            })

                    elif file_type == "image":
                        content_block = {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_content
                            }
                        }
                        current_message["content"].append(content_block)

                    elif file_type == "text":
                        text_content = self.parse_document_to_text(file_path)
                        if text_content is None:
                            content_block = {
                                "type": "file_url",
                                "file_url": {
                                    "url": base64_content,
                                    "file_name": file_name
                                }
                            }
                        else:
                            content_block = {
                                "type": "text",
                                "text": f"[文件内容: {file_name}]\n{text_content}"
                            }
                        current_message["content"].append(content_block)

                    else:
                        content_block = {
                            "type": "file_url",
                            "file_url": {
                                "url": base64_content,
                                "file_name": file_name
                            }
                        }
                        current_message["content"].append(content_block)

        if text:
            current_message["content"].append({
                "type": "text",
                "text": text
            })

        messages.append(current_message)
        return messages, audio_result

    def process_with_files(
            self,
            text: str,
            file_paths: list[str] | None = None,
            history: list[dict] | None = None,
            temperature: float = 0.7,
            max_tokens: int = 2000
    ) -> tuple[bool, str, dict | None]:
        """
        使用多模态模型处理多模态输入
        
        支持视频音频同步处理和单独音频处理。

        Args:
            text: 用户输入的文本
            file_paths: 文件路径列表
            history: 历史对话记录
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            元组 (是否成功, 响应文本, 音频处理结果)
        """
        try:
            valid_file_paths = []
            file_types = []

            for file_path in file_paths:
                if self.is_file_supported(file_path):
                    path = Path(file_path)
                    file_size = path.stat().st_size
                    if file_size <= self.max_file_size:
                        valid_file_paths.append(file_path)
                        file_type, _ = self.get_file_type(file_path)
                        file_types.append(file_type)
                    else:
                        size_mb = file_size / 1024 / 1024
                        max_mb = self.max_file_size / 1024 / 1024
                        print(f"⚠️  文件太大，跳过: {path.name} ({size_mb:.1f}MB > {max_mb:.1f}MB)")
                        logger.warning(f"文件太大，跳过: {path.name} ({size_mb:.1f}MB > {max_mb:.1f}MB)")
                else:
                    print(f"⚠️  不支持的文件类型，跳过: {Path(file_path).name}")
                    logger.warning(f"不支持的文件类型，跳过: {Path(file_path).name}")

            if not valid_file_paths:
                return False, "没有有效的支持文件", None

            print(f"📄 有效文件: {len(valid_file_paths)} 个")
            print(f"📊 文件类型分布: {', '.join(set(file_types))}")
            logger.info(f"处理文件: {len(valid_file_paths)} 个, 类型: {set(file_types)}")

            messages, audio_result = self.prepare_multimodal_messages(text, valid_file_paths, history)

            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    max_tokens=max_tokens,
                    thinking={
                        "type": "disabled"
                    }
                )

                response_text = ""
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            response_text += content
                            print(content, end="", flush=True)
                print()

                if audio_result and self.audio_processor:
                    audio_processor = self.get_audio_processor()
                    audio_processor.cleanup_temp_files(older_than_hours=1)

                logger.debug(f"多模态处理完成, response_length={len(response_text)}")
                return True, response_text, audio_result

            except Exception as api_error:
                error_msg = str(api_error)
                print(f"❌ API调用失败: {error_msg}")
                logger.error(f"API调用失败: {api_error}")

                if "Invalid" in error_msg or "不支持" in error_msg:
                    file_summary = []
                    for i, (file_path, file_type) in enumerate(zip(valid_file_paths, file_types)):
                        file_name = Path(file_path).name
                        file_summary.append(f"{file_name} ({file_type})")

                    error_msg += f"\n处理的文件: {', '.join(file_summary[:3])}"
                    if len(file_summary) > 3:
                        error_msg += f" 等{len(file_summary)}个文件"

                return False, f"API调用失败: {error_msg}", audio_result

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"❌ {error_msg}")
            logger.error(f"多模态处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False, error_msg, None

    def is_file_supported(self, file_path: str) -> bool:
        """
        检查文件是否支持

        Args:
            file_path: 文件路径

        Returns:
            文件支持返回 True，否则返回 False
        """
        path = Path(file_path)
        if not path.exists():
            return False

        ext = path.suffix.lower()
        allowed_extensions = (
                self.allowed_image_extensions +
                self.allowed_audio_extensions +
                self.allowed_video_extensions +
                self.allowed_file_extensions
        )

        return ext in allowed_extensions

    def check_file_size(self, file_path: str) -> tuple[bool, str]:
        """
        检查文件大小是否超过限制

        Args:
            file_path: 文件路径

        Returns:
            元组 (是否通过, 错误信息)
        """
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                size_mb = file_size / 1024 / 1024
                max_mb = self.max_file_size / 1024 / 1024
                return False, f"{size_mb:.1f}MB > {max_mb:.1f}MB限制"
            return True, ""
        except Exception as e:
            return False, f"检查失败: {str(e)}"

    def test_api_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接成功返回 True，否则返回 False
        """
        try:
            print("🔄 测试API连接...")
            logger.info("测试 API 连接")

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": "你好"}]}
                ],
                stream=True,
                max_tokens=10
            )

            response_text = ""
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    if chunk.choices[0].delta.content is not None:
                        response_text += chunk.choices[0].delta.content

            if response_text:
                print("✅ API连接正常")
                logger.debug("API 连接测试成功")
                return True
            else:
                print("❌ API返回空响应")
                logger.warning("API 返回空响应")
                return False

        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
            logger.error(f"API 连接测试失败: {e}")
            return False

"""
多模态处理器模块 - 使用zhipuai库的正确调用方式
支持图像、视频、音频、文件上传和处理
使用ZHIPU_MULTIMODAL_MODEL模型
支持 FFmpeg 和 Whisper 进行音频处理
"""

import os
import base64
import mimetypes
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from zhipuai import ZhipuAI

# 第三方库（解析文档专用，按需求导入）
# 使用 markitdown 统一处理文档转换

from yuntai.core.config import (
    ZHIPU_API_KEY, ZHIPU_MULTIMODAL_MODEL, MAX_FILE_SIZE,
    FFMPEG_PATH, WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE,
    ALLOWED_AUDIO_EXTENSIONS
)


class MultimodalProcessor:
    """多模态处理器类（使用zhipuai库的正确调用方式，支持音频处理）"""

    def __init__(self, api_key: str = None):
        """
        初始化多模态处理器

        Args:
            api_key: 智谱API密钥，如果为None则使用配置中的密钥
        """
        self.api_key = api_key or ZHIPU_API_KEY
        self.model = ZHIPU_MULTIMODAL_MODEL

        # 初始化zhipuai客户端
        self.client = ZhipuAI(api_key=self.api_key)

        # 支持的扩展名
        from yuntai.core.config import (
            ALLOWED_IMAGE_EXTENSIONS,
            ALLOWED_VIDEO_EXTENSIONS,
            ALLOWED_FILE_EXTENSIONS,
            MAX_FILE_SIZE
        )
        self.allowed_image_extensions = ALLOWED_IMAGE_EXTENSIONS
        self.allowed_video_extensions = ALLOWED_VIDEO_EXTENSIONS
        self.allowed_file_extensions = ALLOWED_FILE_EXTENSIONS
        self.allowed_audio_extensions = ALLOWED_AUDIO_EXTENSIONS
        self.max_file_size = MAX_FILE_SIZE

        # 音频处理器（延迟初始化）
        self.audio_processor = None

    def get_audio_processor(self):
        """延迟初始化音频处理器"""
        if self.audio_processor is None:
            from yuntai.processors.audio_processor import AudioProcessor
            self.audio_processor = AudioProcessor(ffmpeg_path=FFMPEG_PATH)
        return self.audio_processor

    def parse_document_to_text(self, file_path: str) -> Optional[str]:
        """
        使用 markitdown 解析文档为文本
        支持所有 markitdown 支持的格式
        """
        try:
            from markitdown import MarkItDown

            # 初始化 markitdown (可以复用实例)
            if not hasattr(self, '_markitdown'):
                self._markitdown = MarkItDown()

            # 使用 markitdown 转换
            result = self._markitdown.convert(file_path)
            text_content = result.text_content

            # 截断过长内容（避免token超限）
            if len(text_content) > 10000:
                text_content = text_content[:10000] + "\n\n[文件内容过长，已截断]"

            return text_content

        except Exception as e:
            print(f"❌ markitdown 解析文档失败 {file_path}: {e}")
            return None

    def encode_file_to_base64(self, file_path: str) -> Optional[str]:
        """
        将文件编码为base64（根据官方文档要求）

        Args:
            file_path: 文件路径

        Returns:
            base64编码的字符串，如果失败返回None
        """
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                print(f"❌ 文件太大: {file_path} ({file_size / 1024 / 1024:.2f}MB)")
                return None

            with open(file_path, 'rb') as file:
                file_content = file.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
                return base64_content
        except Exception as e:
            print(f"❌ 编码文件失败 {file_path}: {e}")
            return None

    def get_file_type(self, file_path: str) -> Tuple[str, str]:
        """
        获取文件类型和MIME类型

        Args:
            file_path: 文件路径

        Returns:
            (文件类型, MIME类型)
        """
        ext = Path(file_path).suffix.lower()

        # 音频类型
        if ext in self.allowed_audio_extensions:
            mime_type = mimetypes.guess_type(file_path)[0] or "audio/mpeg"
            return "audio", mime_type

        # 图片类型
        if ext in self.allowed_image_extensions:
            mime_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
            return "image", mime_type

        # 视频类型
        elif ext in self.allowed_video_extensions:
            mime_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
            return "video", mime_type

        # 可解析的文档类型（统一归为text）
        elif ext in ['.txt', '.py', '.csv', '.xls', '.xlsx', '.docx', '.pdf', '.ppt', '.pptx', '.html', '.js', '.htm', '.rss', '.atom', '.json', '.xml', '.java', '.ipynb']:
            return "text", "text/plain"



        # 文本文件类型
        #elif ext in ['.txt', '.py']:
            #return "text", "text/plain"

        # CSV文件
        #elif ext == '.csv':
            #return "csv", "text/csv"

        # Excel文件
        #elif ext in ['.xls', '.xlsx']:
            #return "excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Word文档
        #elif ext in ['.doc', '.docx']:
            #return "document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        # PDF文件
        #elif ext == '.pdf':
            #return "pdf", "application/pdf"

        # PPT文件
        #elif ext in ['.ppt', '.pptx']:
            #return "presentation", "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        else:
            return "file", "application/octet-stream"

    def prepare_multimodal_messages(
            self,
            text: str,
            file_paths: List[str] = None,
            history: List[Dict] = None
    ) -> Tuple[List[Dict], Optional[Dict]]:
        """
        准备多模态消息（根据官方文档格式）
        支持音频处理和视频音频同步处理

        Args:
            text: 用户输入的文本
            file_paths: 文件路径列表
            history: 历史对话记录

        Returns:
            (消息列表, 音频处理结果字典)
        """
        messages = []

        # 添加历史对话
        if history:
            messages.extend(history)

        # 构建当前消息
        current_message = {
            "role": "user",
            "content": []
        }

        # 音频处理结果
        audio_result = None

        # 添加文件内容（在文本前面，这是关键！）
        if file_paths:
            for file_path in file_paths:
                base64_content = self.encode_file_to_base64(file_path)
                if base64_content:
                    file_type, mime_type = self.get_file_type(file_path)
                    file_name = Path(file_path).name

                    print(f"📄 准备文件: {file_name} (类型: {file_type})")

                    # 特殊处理：视频文件需要提取音频
                    if file_type == "video":
                        # 处理视频+音频
                        processor = self.get_audio_processor()
                        success, result = processor.process_video_with_audio(file_path, text, WHISPER_LANGUAGE)

                        if success:
                            audio_result = result

                            # 添加视频内容块
                            video_block = {
                                "type": "video_url",
                                "video_url": {
                                    "url": base64_content
                                }
                            }
                            current_message["content"].append(video_block)

                            # 添加音频转录文本
                            audio_transcription = result.get("audio_transcription", "")
                            if audio_transcription:
                                audio_text = f"[视频中的音频内容]\n{audio_transcription}"
                                current_message["content"].append({
                                    "type": "text",
                                    "text": audio_text
                                })
                                print(f"✅ 已添加视频+音频内容")
                        else:
                            print(f"⚠️ 音频处理失败，仅使用视频: {result.get('error', 'unknown error')}")
                            # 仅添加视频内容
                            current_message["content"].append({
                                "type": "video_url",
                                "video_url": {
                                    "url": base64_content
                                }
                            })

                    # 特殊处理：音频文件
                    elif file_type == "audio":
                        # 处理音频文件
                        processor = self.get_audio_processor()
                        success, result = processor.process_audio_only(file_path, text, WHISPER_LANGUAGE)

                        if success:
                            audio_result = result
                            audio_transcription = result.get("audio_transcription", "")

                            # 添加音频转录文本
                            if audio_transcription:
                                audio_text = f"[音频内容]\n{audio_transcription}"
                                current_message["content"].append({
                                    "type": "text",
                                    "text": audio_text
                                })
                                #print(f"✅ 已添加音频转录内容")
                        else:
                            print(f"⚠️ 音频处理失败: {result.get('error', 'unknown error')}")
                            # 添加错误信息
                            current_message["content"].append({
                                "type": "text",
                                "text": f"[音频处理失败: {result.get('error', 'unknown error')}]"
                            })

                    # 图片类型
                    elif file_type == "image":
                        content_block = {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_content  # 直接使用base64，不需要data:前缀
                            }
                        }
                        current_message["content"].append(content_block)

                    # 文本文件类型
                    elif file_type == "text":
                        # 调用新增的解析方法
                        text_content = self.parse_document_to_text(file_path)
                        if text_content is None:
                            # 解析失败时降级为file_url
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
                        # 其他文件类型使用file_url
                        content_block = {
                            "type": "file_url",
                            "file_url": {
                                "url": base64_content,
                                "file_name": file_name
                            }
                        }
                        current_message["content"].append(content_block)

        # 添加用户文本内容（在所有文件后面）
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
            file_paths: List[str] = None,
            history: List[Dict] = None,
            temperature: float = 0.7,
            max_tokens: int = 2000
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        使用ZHIPU_MULTIMODAL_MODEL处理多模态输入（使用官方推荐的调用方式）
        支持视频音频同步处理和单独音频处理

        Args:
            text: 用户输入的文本
            file_paths: 文件路径列表
            history: 历史对话记录
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            (success, response_text, audio_result)
        """
        try:
            # 验证文件
            valid_file_paths = []
            file_types = []

            for file_path in file_paths:
                if self.is_file_supported(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size <= self.max_file_size:
                        valid_file_paths.append(file_path)
                        file_type, _ = self.get_file_type(file_path)
                        file_types.append(file_type)
                    else:
                        size_mb = file_size / 1024 / 1024
                        max_mb = self.max_file_size / 1024 / 1024
                        print(f"⚠️  文件太大，跳过: {os.path.basename(file_path)} ({size_mb:.1f}MB > {max_mb:.1f}MB)")
                else:
                    print(f"⚠️  不支持的文件类型，跳过: {os.path.basename(file_path)}")

            if not valid_file_paths:
                return False, "没有有效的支持文件", None

            #print(f"🔄 正在准备消息...")
            print(f"📄 有效文件: {len(valid_file_paths)} 个")
            print(f"📊 文件类型分布: {', '.join(set(file_types))}")

            # 准备消息（返回消息和音频处理结果）
            messages, audio_result = self.prepare_multimodal_messages(text, valid_file_paths, history)

            # 调试：打印消息结构（前100个字符）
            import json
            messages_str = json.dumps(messages, ensure_ascii=False)
            #print(f"📨 消息结构预览: {messages_str[:200]}...")

            #print(f"🔄 发送请求到ZHIPU_MULTIMODAL_MODEL...")

            try:
                # 使用zhipuai库的正确调用方式（流式输出）
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    max_tokens=max_tokens,
                    thinking={
                        "type": "disabled"  # 根据需要启用或禁用
                    }
                )

                # 解析流式响应
                response_text = ""
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            response_text += content
                            print(content, end="", flush=True)
                print()  # 换行
                #print(f"\n✅ 收到响应，长度: {len(response_text)} 字符")

                # 如果有音频处理结果，清理临时文件
                if audio_result and self.audio_processor:
                    audio_processor = self.get_audio_processor()
                    audio_processor.cleanup_temp_files(older_than_hours=1)

                return True, response_text, audio_result

            except Exception as api_error:
                # 处理API特定错误
                error_msg = str(api_error)
                print(f"❌ API调用失败: {error_msg}")

                # 尝试解析错误信息
                if "Invalid" in error_msg or "不支持" in error_msg:
                    # 可能是文件格式问题
                    file_summary = []
                    for i, (file_path, file_type) in enumerate(zip(valid_file_paths, file_types)):
                        file_name = os.path.basename(file_path)
                        file_summary.append(f"{file_name} ({file_type})")

                    error_msg += f"\n处理的文件: {', '.join(file_summary[:3])}"
                    if len(file_summary) > 3:
                        error_msg += f" 等{len(file_summary)}个文件"

                return False, f"API调用失败: {error_msg}", audio_result

        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg, None

    def is_file_supported(self, file_path: str) -> bool:
        """
        检查文件是否支持

        Args:
            file_path: 文件路径

        Returns:
            True如果文件支持，False如果不支持
        """
        if not os.path.exists(file_path):
            return False

        ext = Path(file_path).suffix.lower()
        allowed_extensions = (
                self.allowed_image_extensions +
                self.allowed_audio_extensions +
                self.allowed_video_extensions +
                self.allowed_file_extensions
        )

        return ext in allowed_extensions

    def check_file_size(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件大小是否超过限制

        Args:
            file_path: 文件路径

        Returns:
            (是否通过, 错误信息)
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                size_mb = file_size / 1024 / 1024
                max_mb = self.max_file_size / 1024 / 1024
                return False, f"{size_mb:.1f}MB > {max_mb:.1f}MB限制"
            return True, ""
        except Exception as e:
            return False, f"检查失败: {str(e)}"

    def test_api_connection(self) -> bool:
        """测试API连接"""
        try:
            print("🔄 测试API连接...")

            # 简单的文本测试（流式输出）
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
                return True
            else:
                print("❌ API返回空响应")
                return False

        except Exception as e:
            print(f"❌ API连接测试失败: {e}")
            return False

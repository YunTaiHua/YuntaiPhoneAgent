"""
multimodal_other.py - 多模态其他功能模块
集成ZHIPU_IMAGE_MODEL和ZHIPU_VIDEO_MODEL功能
"""

import os
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
import json
import time
import threading
from typing import Optional, List, Dict, Any
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import webbrowser
from PIL import Image, ImageTk

# 从统一配置导入
from yuntai.core.config import (
    ThemeColors,
    PROJECT_ROOT,
    TEMP_DIR,
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_IMAGE_MODEL,
    ZHIPU_VIDEO_MODEL
)

logger = logging.getLogger(__name__)

# 常量定义
CHUNK_SIZE = 8192
TIMEOUT = 30
MAX_IMAGE_COUNT = 2
INITIAL_DELAY_TEXT = 10
INITIAL_DELAY_IMAGE = 30
MAX_ATTEMPTS = 100
CHECK_INTERVAL = 10
DOWNLOAD_TIMEOUT = 30


class MultimodalOther:
    """多模态其他功能类：处理图像和视频生成"""

    def __init__(self, api_key: Optional[str] = None, project_root: Optional[str] = None):
        """
        初始化多模态其他功能

        Args:
            api_key: 智谱AI API密钥（可选，从配置获取）
            project_root: 项目根目录（可选，从配置获取）
        """
        self.api_key = api_key or ZHIPU_API_KEY
        self.project_root = project_root or PROJECT_ROOT

        # 创建输出目录
        self.image_output_dir = os.path.join(TEMP_DIR, "images")
        self.video_output_dir = os.path.join(TEMP_DIR, "videos")

        os.makedirs(self.image_output_dir, exist_ok=True)
        os.makedirs(self.video_output_dir, exist_ok=True)

        # API端点
        self.image_api_url = f"{ZHIPU_API_BASE_URL}/images/generations"
        self.video_api_url = f"{ZHIPU_API_BASE_URL}/videos/generations"
        self.async_result_url = f"{ZHIPU_API_BASE_URL}/async-result"

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 支持的图像尺寸
        self.image_sizes = [
            "1280x1280",
            "1024x1024",
            "1024x768",
            "768x1024",
            "1920x1080",
            "1080x1920"
        ]

        # 支持的视频尺寸
        self.video_sizes = [
            "1920x1080",
            "1080x1920",
            "1280x720",
            "720x1280",
            "1024x1024",
            "3840x2160"
        ]

        # 支持的视频帧率
        self.video_fps = [30, 60]

    def generate_image(self, prompt: str, size: str = "1280x1280",
                       quality: str = "standard") -> Dict[str, Any]:
        """
        使用ZHIPU_IMAGE_MODEL生成图像

        Args:
            prompt: 图像描述
            size: 图像尺寸
            quality: 图像质量 (standard/hd)

        Returns:
            包含生成结果的字典
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": ZHIPU_IMAGE_MODEL,
                "prompt": prompt,
                "size": size,
                "quality": quality
            }

            response = requests.post(self.image_api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result,
                    "message": "图像生成成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"API请求失败: {response.status_code} - {response.text}"
                }

        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"图像生成失败: {e}")
            return {
                "success": False,
                "message": f"图像生成失败: {str(e)}"
            }
        except Exception as e:
            logger.exception(f"图像生成未知错误: {e}")
            return {
                "success": False,
                "message": f"图像生成未知错误: {str(e)}"
            }

    def download_image(self, image_url: str, filename: str = None) -> str:
        """
        下载生成的图像

        Args:
            image_url: 图像URL
            filename: 保存文件名（可选）

        Returns:
            下载的文件路径
        """
        try:
            if not filename:
                # 从URL提取文件名
                filename = f"image_{int(time.time())}.png"
            else:
                if not filename.endswith('.png'):
                    filename += '.png'

            file_path = os.path.join(self.image_output_dir, filename)

            response = requests.get(image_url)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return file_path
            else:
                raise Exception(f"下载失败: {response.status_code}")

        except Exception as e:
            raise Exception(f"下载图像失败: {str(e)}")

    # 更新 multimodal_other.py 中的 generate_video 方法

    def generate_video(self, prompt: str, image_urls: List[str] = None,
                       size: str = "1920x1080", fps: int = 30,
                       quality: str = "quality", with_audio: bool = True) -> Dict[str, Any]:
        """
        使用ZHIPU_VIDEO_MODEL生成视频

        Args:
            prompt: 视频描述
            image_urls: 图片URL列表（支持0-2张）
            size: 视频尺寸
            fps: 帧率
            quality: 质量 (speed/quality)
            with_audio: 是否生成音效

        Returns:
            包含生成结果的字典
        """
        try:
            # 验证图片URL
            if image_urls:
                # 验证图片数量
                if len(image_urls) > 2:
                    return {
                        "success": False,
                        "message": "最多支持2张图片"
                    }

                # 验证图片URL格式
                valid_urls = []
                for url in image_urls:
                    url = url.strip()
                    if not url:
                        continue

                    # 检查URL格式
                    if not (url.startswith("http://") or url.startswith("https://")):
                        logger.warning(f"图片URL格式不正确: {url}")
                        continue

                    valid_urls.append(url)

                if len(image_urls) != len(valid_urls):
                    logger.warning(f"过滤了 {len(image_urls) - len(valid_urls)} 个无效URL")

                image_urls = valid_urls

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 基础请求体
            payload = {
                "model": ZHIPU_VIDEO_MODEL,
                "prompt": prompt,
                "quality": quality,
                "with_audio": with_audio,
                "size": size,
                "fps": fps
            }

            # 根据图片数量使用不同的字段名
            if image_urls:
                image_count = len(image_urls)

                if image_count == 1:
                    # 单张图片：使用image_url字段（字符串）
                    payload["image_url"] = image_urls[0]
                    #print(f"🖼️ 单图生成：使用 image_url 字段")

                elif image_count == 2:
                    # 两张图片：使用image_urls字段（列表）
                    payload["image_urls"] = image_urls  # 注意这里是 image_urls（复数）
                    #print(f"🖼️ 双图生成：使用 image_urls 字段")

                else:
                    return {
                        "success": False,
                        "message": "需要1-2张有效图片"
                    }

            logger.info(f"发送视频生成请求: 模型 {ZHIPU_VIDEO_MODEL}")

            if image_urls:
                pass
            else:
                pass

            response = requests.post(self.video_api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()

                # 提取任务ID
                task_id = result.get("id") or result.get("request_id")

                if not task_id:
                    return {
                        "success": False,
                        "message": "无法获取任务ID",
                        "raw_response": result
                    }

                task_status = result.get("task_status", "PROCESSING")

                # 如果立即失败，提取错误信息
                if task_status == "FAIL":
                    error_info = result.get("error", {})
                    error_msg = error_info.get("message", "未知错误")
                    error_code = error_info.get("code", "未知错误码")

                    return {
                        "success": False,
                        "message": f"任务失败: {error_msg} (错误码: {error_code})",
                        "task_id": task_id,
                        "task_status": task_status,
                        "error_code": error_code
                    }

                return {
                    "success": True,
                    "data": result,
                    "task_id": task_id,
                    "task_status": task_status,
                    "message": "视频生成任务已提交"
                }
            else:
                error_msg = f"API请求失败: {response.status_code}"
                print(f"❌ {error_msg}")
                print(f"错误响应: {response.text}")

                # 尝试解析错误信息
                try:
                    error_data = json.loads(response.text)
                    error_info = error_data.get("error", {})
                    detail_msg = error_info.get("message", response.text[:200])
                    return {
                        "success": False,
                        "message": f"{error_msg}: {detail_msg}",
                        "response_text": response.text
                    }
                except:
                    return {
                        "success": False,
                        "message": error_msg,
                        "response_text": response.text
                    }

        except Exception as e:
            error_msg = f"视频生成失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": error_msg
            }

    def check_video_result(self, task_id: str) -> Dict[str, Any]:
        """
        检查视频生成结果

        Args:
            task_id: 任务ID

        Returns:
            包含视频结果的字典
        """
        try:
            # 使用原来的查询端点
            url = f"{self.async_result_url}/{task_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                result = response.json()

                task_status = result.get("task_status", "UNKNOWN")

                if task_status == "SUCCESS":
                    video_result = result.get("video_result", [{}])
                    if video_result and len(video_result) > 0:
                        cover_url = video_result[0].get("cover_image_url")
                        video_url = video_result[0].get("url")

                        return {
                            "success": True,
                            "status": task_status,
                            "cover_url": cover_url,
                            "video_url": video_url,
                            "data": result,
                            "message": "视频生成成功"
                        }
                    else:
                        return {
                            "success": False,
                            "status": task_status,
                            "message": "视频结果格式错误"
                        }

                elif task_status == "PROCESSING":
                    return {
                        "success": False,
                        "status": task_status,
                        "message": "视频生成中，请稍候..."
                    }
                elif task_status == "FAIL":
                    error_info = result.get("error", {})
                    error_msg = error_info.get("message", "未知错误")
                    return {
                        "success": False,
                        "status": task_status,
                        "message": f"视频生成失败: {error_msg}"
                    }
                else:
                    return {
                        "success": False,
                        "status": task_status,
                        "message": f"未知状态: {task_status}"
                    }
            else:
                error_msg = f"查询失败: {response.status_code} - {response.text}"
                return {
                    "success": False,
                    "message": error_msg
                }

        except Exception as e:
            error_msg = f"查询视频结果失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": error_msg
            }

    def download_video(self, video_url: str, cover_url: str = None,
                       filename: str = None) -> Dict[str, str]:
        """
        下载生成的视频

        Args:
            video_url: 视频URL
            cover_url: 封面URL（可选）
            filename: 保存文件名（可选）

        Returns:
            包含文件路径的字典
        """
        try:
            if not filename:
                filename = f"cogvideox_{int(time.time())}"

            # 下载视频
            video_filename = f"{filename}.mp4"
            video_path = os.path.join(self.video_output_dir, video_filename)

            video_response = requests.get(video_url, stream=True, timeout=TIMEOUT)

            if video_response.status_code == 200:
                total_size = int(video_response.headers.get('content-length', 0))

                with open(video_path, 'wb') as f:
                    downloaded = 0
                    for chunk in video_response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                # 下载封面（如果提供）
                cover_path = None
                if cover_url:
                    try:
                        cover_filename = f"{filename}_cover.png"
                        cover_path = os.path.join(self.video_output_dir, cover_filename)

                        cover_response = requests.get(cover_url, timeout=30)

                        if cover_response.status_code == 200:
                            with open(cover_path, 'wb') as f:
                                f.write(cover_response.content)
                    except Exception as cover_error:
                        pass

                return {
                    "success": True,
                    "video_path": video_path,
                    "cover_path": cover_path,
                    "message": "下载完成",
                    "video_size": os.path.getsize(video_path) / (1024 * 1024)  # MB
                }
            else:
                error_msg = f"视频下载失败: {video_response.status_code}"
                return {
                    "success": False,
                    "message": error_msg
                }

        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            return {
                "success": False,
                "message": error_msg
            }

    def wait_for_video_completion(self, task_id: str,
                                   image_count: int = 0,  # 新增：图片数量
                                   interval: int = 10,
                                   max_attempts: int = 100,
                                   callback=None) -> Dict[str, Any]:
        """
        等待视频生成完成

        Args:
            task_id: 任务ID
            image_count: 图片数量（0=文字，1=单图，2=双图）
            interval: 检查间隔（秒）
            max_attempts: 最大尝试次数
            callback: 回调函数，格式为 callback(event_type, attempt, task_id, status, interval)

        Returns:
            最终的视频结果
        """
        # 调用回调传递初始信息
        if callback:
            callback("START", task_id, image_count, interval, max_attempts)

        # 根据图片数量设置首次查询延迟
        initial_delay = 30 if image_count >= 1 else 10  # 双图和单图30秒，文字10秒

        # 首次查询前等待
        if initial_delay > 0:
            if callback:
                callback("WAIT", initial_delay, task_id, "PROCESSING", interval)
            time.sleep(initial_delay)

        for attempt in range(1, max_attempts + 1):
            # 调用回调传递轮询信息
            result = self.check_video_result(task_id)
            status = result.get("status", "UNKNOWN")

            if callback:
                callback("CHECK", attempt, task_id, status, interval)

            if result.get("success") and result.get("status") == "SUCCESS":
                if callback:
                    callback("SUCCESS", attempt, task_id, status, interval)
                return result
            elif result.get("status") == "FAIL":
                if callback:
                    callback("FAIL", attempt, task_id, status, interval)
                return result
            elif attempt < max_attempts:
                if callback:
                    callback("WAIT", interval, task_id, status, interval)
                time.sleep(interval)
            else:
                if callback:
                    callback("TIMEOUT", attempt, task_id, status, interval)

        return {
            "success": False,
            "message": "视频生成超时",
            "task_id": task_id
        }


class ImagePreviewWindow:
    """图像预览窗口"""

    def __init__(self, parent, image_path: str, title: str = "图像预览"):
        """
        初始化图像预览窗口

        Args:
            parent: 父窗口
            image_path: 图像路径
            title: 窗口标题
        """
        self.window = ctk.CTkToplevel(parent)
        self.window.title(title)
        self.window.geometry("800x600")

        # 设置窗口置顶
        self.window.attributes('-topmost', True)

        # 设置窗口图标
        try:
            self.window.iconbitmap(default="icon.ico")
        except:
            pass

        # 绑定窗口焦点事件，失去焦点时取消置顶
        self.window.bind("<FocusOut>", lambda e: self.window.attributes('-topmost', False))
        self.window.bind("<FocusIn>", lambda e: self.window.attributes('-topmost', True))

        # 创建主框架
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text=title,
            font=("Microsoft YaHei", 18, "bold")
        )
        title_label.pack(pady=(10, 5))

        # 图像显示区域
        image_frame = ctk.CTkFrame(main_frame)
        image_frame.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            # 使用PIL加载和显示图片
            pil_image = Image.open(image_path)

            # 调整图片大小以适应窗口
            max_width = 700
            max_height = 400
            pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # 转换为Tkinter兼容的格式
            tk_image = ImageTk.PhotoImage(pil_image)

            # 创建标签显示图片
            image_label = tk.Label(image_frame, image=tk_image, bg=ThemeColors.BG_CARD)
            image_label.image = tk_image  # 保持引用
            image_label.pack(fill="both", expand=True)

        except Exception as e:
            error_label = ctk.CTkLabel(
                image_frame,
                text=f"无法加载图像: {str(e)}\n文件路径: {image_path}",
                font=("Microsoft YaHei", 14),
                text_color=ThemeColors.DANGER
            )
            error_label.pack(expand=True)

        # 信息区域
        info_frame = ctk.CTkFrame(main_frame, height=50)
        info_frame.pack(fill="x", padx=10, pady=(5, 10))

        # 文件信息
        file_name = os.path.basename(image_path)
        file_size = os.path.getsize(image_path) / 1024  # KB
        file_info = f"文件: {file_name} ({file_size:.1f} KB)"
        info_label = ctk.CTkLabel(
            info_frame,
            text=file_info,
            font=("Microsoft YaHei", 12)
        )
        info_label.pack(side="left", padx=10)

        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 打开文件夹按钮
        open_folder_btn = ctk.CTkButton(
            button_frame,
            text="打开所在文件夹",
            font=("Microsoft YaHei", 12),
            height=35,
            command=lambda: self.open_file_location(image_path)
        )
        open_folder_btn.pack(side="left", padx=5)

        # 查看原图按钮
        view_original_btn = ctk.CTkButton(
            button_frame,
            text="查看原图",
            font=("Microsoft YaHei", 12),
            height=35,
            command=lambda: self.view_original_image(image_path)
        )
        view_original_btn.pack(side="left", padx=5)

        # 关闭按钮
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            font=("Microsoft YaHei", 12),
            height=35,
            fg_color=ThemeColors.SECONDARY,
            command=self.window.destroy
        )
        close_btn.pack(side="right", padx=5)

    def view_original_image(self, image_path: str):
        """用默认程序打开原图"""
        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                os.startfile(image_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", image_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", image_path])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"无法打开图像: {str(e)}")

    def open_file_location(self, file_path: str):
        """打开文件所在文件夹"""
        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{file_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")


# 更新 multimodal_other.py 中的 VideoPreviewWindow 类

class VideoPreviewWindow:
    """视频预览窗口"""

    def __init__(self, parent, video_path: str, cover_path: str = None,
                 title: str = "视频预览"):
        """
        初始化视频预览窗口

        Args:
            parent: 父窗口
            video_path: 视频路径
            cover_path: 封面路径（可选）
            title: 窗口标题
        """
        self.window = ctk.CTkToplevel(parent)
        self.window.title(title)
        self.window.geometry("900x700")

        # 设置窗口置顶
        self.window.attributes('-topmost', True)

        # 设置窗口图标
        try:
            self.window.iconbitmap(default="icon.ico")
        except:
            pass

        # 绑定窗口焦点事件
        self.window.bind("<FocusOut>", lambda e: self.window.attributes('-topmost', False))
        self.window.bind("<FocusIn>", lambda e: self.window.attributes('-topmost', True))

        # 创建主框架
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text=title,
            font=("Microsoft YaHei", 18, "bold")
        )
        title_label.pack(pady=(10, 5))

        # 视频/封面显示区域
        media_frame = ctk.CTkFrame(main_frame)
        media_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 尝试显示视频封面或占位符
        try:
            if cover_path and os.path.exists(cover_path):
                try:
                    # 使用PIL加载封面
                    pil_image = Image.open(cover_path)

                    # 调整大小
                    max_width = 800
                    max_height = 450
                    pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # 转换为Tkinter格式
                    tk_image = ImageTk.PhotoImage(pil_image)

                    # 创建标签显示封面
                    cover_label = tk.Label(media_frame, image=tk_image, bg=ThemeColors.BG_CARD)
                    cover_label.image = tk_image
                    cover_label.pack(fill="both", expand=True)

                    # 添加播放按钮图标
                    play_label = tk.Label(
                        media_frame,
                        text="▶",
                        font=("Arial", 48, "bold"),
                        fg="white",
                        bg=ThemeColors.BG_CARD
                    )
                    play_label.place(relx=0.5, rely=0.5, anchor="center")

                except Exception as img_error:
                    # 如果封面加载失败，显示占位符
                    print(f"封面加载失败: {img_error}")
                    self._show_video_placeholder(media_frame, "🎬 视频封面")

            else:
                # 显示视频占位符
                self._show_video_placeholder(media_frame, "🎬 视频预览")

        except Exception as e:
            self._show_video_placeholder(media_frame, f"无法加载预览: {str(e)[:50]}")

        # 信息区域
        info_frame = ctk.CTkFrame(main_frame, height=50)
        info_frame.pack(fill="x", padx=10, pady=(5, 10))

        # 文件信息
        video_name = os.path.basename(video_path)
        video_size = os.path.getsize(video_path) / (1024 * 1024)  # MB

        file_info = f"视频: {video_name} ({video_size:.1f} MB)"
        if cover_path and os.path.exists(cover_path):
            cover_size = os.path.getsize(cover_path) / 1024  # KB
            file_info += f" | 封面: {os.path.basename(cover_path)} ({cover_size:.1f} KB)"

        info_label = ctk.CTkLabel(
            info_frame,
            text=file_info,
            font=("Microsoft YaHei", 12)
        )
        info_label.pack(side="left", padx=10)

        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 播放视频按钮
        play_btn = ctk.CTkButton(
            button_frame,
            text="播放视频",
            font=("Microsoft YaHei", 12),
            height=35,
            command=lambda: self.play_video(video_path)
        )
        play_btn.pack(side="left", padx=5)

        # 打开文件夹按钮
        open_folder_btn = ctk.CTkButton(
            button_frame,
            text="打开所在文件夹",
            font=("Microsoft YaHei", 12),
            height=35,
            command=lambda: self.open_file_location(video_path)
        )
        open_folder_btn.pack(side="left", padx=5)

        # 关闭按钮
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            font=("Microsoft YaHei", 12),
            height=35,
            fg_color=ThemeColors.SECONDARY,
            command=self.window.destroy
        )
        close_btn.pack(side="right", padx=5)

    def _show_video_placeholder(self, parent, text: str):
        """显示视频占位符"""
        placeholder = ctk.CTkLabel(
            parent,
            text=text,
            font=("Microsoft YaHei", 24),
            text_color=ThemeColors.TEXT_SECONDARY
        )
        placeholder.pack(expand=True)

    def play_video(self, video_path: str):
        """播放视频"""
        try:
            import platform
            import subprocess

            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", video_path])

            # 视频播放成功后自动关闭预览窗口
            self.window.destroy()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"无法播放视频: {str(e)}")

    def open_file_location(self, file_path: str):
        """打开文件所在文件夹"""
        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{file_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
"""
media_generator.py - 媒体生成器模块
集成ZHIPU_IMAGE_MODEL和ZHIPU_VIDEO_MODEL功能
使用 pathlib 进行跨平台路径处理
"""

import logging
from concurrent.futures import ThreadPoolExecutor

import requests
import json
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

from yuntai.core.config import (
    PROJECT_ROOT,
    TEMP_DIR,
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_IMAGE_MODEL,
    ZHIPU_VIDEO_MODEL
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192
TIMEOUT = 30
MAX_IMAGE_COUNT = 2
INITIAL_DELAY_TEXT = 10
INITIAL_DELAY_IMAGE = 30
MAX_ATTEMPTS = 100
CHECK_INTERVAL = 10
DOWNLOAD_TIMEOUT = 30


class MediaGenerator:
    """媒体生成器类：处理图像和视频生成"""

    def __init__(self, api_key: Optional[str] = None, project_root: Optional[Path] = None):
        """
        初始化媒体生成器

        Args:
            api_key: 智谱AI API密钥（可选，从配置获取）
            project_root: 项目根目录（可选，从配置获取）
        """
        self.api_key = api_key or ZHIPU_API_KEY
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT

        self.image_output_dir = TEMP_DIR / "images"
        self.video_output_dir = TEMP_DIR / "videos"

        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        self.video_output_dir.mkdir(parents=True, exist_ok=True)

        self.image_api_url = f"{ZHIPU_API_BASE_URL}/images/generations"
        self.video_api_url = f"{ZHIPU_API_BASE_URL}/videos/generations"
        self.async_result_url = f"{ZHIPU_API_BASE_URL}/async-result"

        self.executor = ThreadPoolExecutor(max_workers=2)

        self.image_sizes = [
            "1280x1280",
            "1024x1024",
            "1024x768",
            "768x1024",
            "1920x1080",
            "1080x1920"
        ]

        self.video_sizes = [
            "1920x1080",
            "1080x1920",
            "1280x720",
            "720x1280",
            "1024x1024",
            "3840x2160"
        ]

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
                filename = f"image_{int(time.time())}.png"
            else:
                if not filename.endswith('.png'):
                    filename += '.png'

            file_path = self.image_output_dir / filename

            response = requests.get(image_url)
            if response.status_code == 200:
                file_path.write_bytes(response.content)
                return str(file_path)
            else:
                raise Exception(f"下载失败: {response.status_code}")

        except Exception as e:
            raise Exception(f"下载图像失败: {str(e)}")

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
            if image_urls:
                if len(image_urls) > 2:
                    return {
                        "success": False,
                        "message": "最多支持2张图片"
                    }

                valid_urls = []
                for url in image_urls:
                    url = url.strip()
                    if not url:
                        continue

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

            payload = {
                "model": ZHIPU_VIDEO_MODEL,
                "prompt": prompt,
                "quality": quality,
                "with_audio": with_audio,
                "size": size,
                "fps": fps
            }

            if image_urls:
                image_count = len(image_urls)

                if image_count == 1:
                    payload["image_url"] = image_urls[0]

                elif image_count == 2:
                    payload["image_urls"] = image_urls

                else:
                    return {
                        "success": False,
                        "message": "需要1-2张有效图片"
                    }

            logger.info(f"发送视频生成请求: 模型 {ZHIPU_VIDEO_MODEL}")

            response = requests.post(self.video_api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()

                task_id = result.get("id") or result.get("request_id")

                if not task_id:
                    return {
                        "success": False,
                        "message": "无法获取任务ID",
                        "raw_response": result
                    }

                task_status = result.get("task_status", "PROCESSING")

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

            video_filename = f"{filename}.mp4"
            video_path = self.video_output_dir / video_filename

            video_response = requests.get(video_url, stream=True, timeout=TIMEOUT)

            if video_response.status_code == 200:
                total_size = int(video_response.headers.get('content-length', 0))

                with open(video_path, 'wb') as f:
                    downloaded = 0
                    for chunk in video_response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                cover_path = None
                if cover_url:
                    try:
                        cover_filename = f"{filename}_cover.png"
                        cover_path = self.video_output_dir / cover_filename

                        cover_response = requests.get(cover_url, timeout=30)

                        if cover_response.status_code == 200:
                            cover_path.write_bytes(cover_response.content)
                    except Exception as cover_error:
                        pass

                return {
                    "success": True,
                    "video_path": str(video_path),
                    "cover_path": str(cover_path) if cover_path else None,
                    "message": "下载完成",
                    "video_size": video_path.stat().st_size / (1024 * 1024)
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
                                   image_count: int = 0,
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
        if callback:
            callback("START", 0, task_id, "PROCESSING", interval)

        initial_delay = 30 if image_count >= 1 else 10

        if initial_delay > 0:
            if callback:
                callback("WAIT", 0, task_id, "PROCESSING", initial_delay)
            time.sleep(initial_delay)

        for attempt in range(1, max_attempts + 1):
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
                    callback("WAIT", attempt, task_id, status, interval)
                time.sleep(interval)
            else:
                if callback:
                    callback("TIMEOUT", attempt, task_id, status, interval)

        return {
            "success": False,
            "message": "视频生成超时",
            "task_id": task_id
        }

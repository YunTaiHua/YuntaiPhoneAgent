"""
media_handler.py - 媒体生成处理（图像/视频）
"""

import os
import time
import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controller import WebController


async def handle_generate_image(websocket, data: dict, controller: "WebController"):
    """处理图像生成"""
    prompt = data.get("prompt", "").strip()
    size = data.get("size", "1280x1280")
    quality = data.get("quality", "standard")

    if not prompt:
        await controller.send_toast("请输入图像描述", "warning")
        return

    await controller.send_toast("正在生成图像...", "info")

    def generate_thread():
        try:
            from yuntai.processors.media_generator import MediaGenerator

            generator = MediaGenerator()

            # 发送日志
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(controller.ws_manager.broadcast({
                "type": "image_log",
                "message": "🔄 正在生成图像...\n"
            }))
            loop.close()

            # 使用正确的参数调用generate_image（size是字符串，不是width/height）
            result = generator.generate_image(
                prompt=prompt,
                size=size,
                quality=quality
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if result and result.get("success"):
                    # 从结果中获取图像URL
                    image_data = result.get("data", {})
                    image_url = image_data.get("data", [{}])[0].get("url", "") if image_data else ""

                    if image_url:
                        # 下载图像到本地
                        filename = f"cogview_{int(time.time())}.png"
                        try:
                            image_path = generator.download_image(image_url, filename.replace('.png', ''))

                            # 构建可访问的URL
                            image_filename = os.path.basename(image_path) if image_path else filename
                            image_url_for_web = f"/api/images/{image_filename}"

                            loop.run_until_complete(controller.ws_manager.broadcast({
                                "type": "image_log",
                                "message": f"✅ 图像生成成功！\n📁 保存路径: {image_path}\n📐 图像尺寸: {size}\n✨ 生成质量: {quality}\n"
                            }))

                            loop.run_until_complete(controller.ws_manager.broadcast({
                                "type": "image_generated",
                                "image_path": image_url_for_web
                            }))

                            loop.run_until_complete(controller.send_toast("图像生成成功", "success"))
                        except Exception as download_error:
                            loop.run_until_complete(controller.ws_manager.broadcast({
                                "type": "image_log",
                                "message": f"❌ 图像下载失败: {download_error}\n"
                            }))
                            loop.run_until_complete(controller.send_toast("图像下载失败", "error"))
                    else:
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "image_log",
                            "message": "❌ 图像生成失败：未获取到图像URL\n"
                        }))
                        loop.run_until_complete(controller.send_toast("图像生成失败：未获取到图像URL", "error"))
                else:
                    error_msg = result.get("message", "未知错误") if result else "生成失败"
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "image_log",
                        "message": f"❌ 图像生成失败: {error_msg}\n"
                    }))
                    loop.run_until_complete(controller.send_toast(f"图像生成失败: {error_msg}", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "image_log",
                    "message": f"❌ 生成错误: {str(e)}\n"
                }))
                loop.run_until_complete(controller.send_toast(f"生成错误: {str(e)}", "error"))
            finally:
                loop.close()

    threading.Thread(target=generate_thread, daemon=True).start()


async def handle_generate_video(websocket, data: dict, controller: "WebController"):
    """处理视频生成"""
    prompt = data.get("prompt", "").strip()
    image_urls = data.get("image_urls", [])
    size = data.get("size", "1920x1080")
    fps = int(data.get("fps", "30"))
    quality = data.get("quality", "quality")
    with_audio = data.get("with_audio", True)

    if not prompt:
        await controller.send_toast("请输入视频描述", "warning")
        return

    await controller.send_toast("正在生成视频...", "info")

    def generate_thread():
        try:
            from yuntai.processors.media_generator import MediaGenerator

            generator = MediaGenerator()

            # 发送日志
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(controller.ws_manager.broadcast({
                "type": "video_log",
                "message": "🔄 正在提交视频生成任务...\n"
            }))
            loop.close()

            # 使用正确的参数调用generate_video
            result = generator.generate_video(
                prompt=prompt,
                image_urls=image_urls if image_urls else None,
                size=size,
                fps=fps,
                quality=quality,
                with_audio=with_audio
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if result and result.get("success"):
                    task_id = result.get("task_id")
                    task_status = result.get("task_status", "UNKNOWN")

                    if task_status == "FAIL":
                        error_msg = result.get('message', '未知错误')
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"❌ 视频生成立即失败\n错误信息: {error_msg}\n"
                        }))
                        loop.run_until_complete(controller.send_toast(f"视频生成失败: {error_msg[:30]}", "error"))
                    else:
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"✅ 视频生成任务已提交！\n📐 视频尺寸: {size}\n⏳ 请耐心等待结果...\n"
                        }))
                        loop.run_until_complete(controller.send_toast("视频生成任务已提交", "success"))

                        # 开始轮询检查结果
                        if task_id:
                            start_video_result_polling(controller, task_id, len(image_urls))
                else:
                    error_msg = result.get("message", "未知错误") if result else "生成失败"
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "video_log",
                        "message": f"❌ 视频生成失败: {error_msg}\n"
                    }))
                    loop.run_until_complete(controller.send_toast(f"视频生成失败: {error_msg}", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "video_log",
                    "message": f"❌ 生成错误: {str(e)}\n"
                }))
                loop.run_until_complete(controller.send_toast(f"生成错误: {str(e)}", "error"))
            finally:
                loop.close()

    threading.Thread(target=generate_thread, daemon=True).start()


def start_video_result_polling(controller, task_id: str, image_count: int = 0):
    """开始轮询检查视频生成结果"""

    def polling_thread():
        try:
            from yuntai.processors.media_generator import MediaGenerator
            generator = MediaGenerator()

            def polling_callback(event_type, attempt, task_id, status, interval):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if event_type == "START":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": "🎬 视频生成任务已提交\n" + "-" * 50 + "\n"
                        }))
                    elif event_type == "WAIT":
                        wait_text = f"⏳ 等待检查...\n" if attempt > 1 else f"⏰ 首次检查在{interval}秒后开始\n"
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": wait_text
                        }))
                    elif event_type == "CHECK":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"📊 第{attempt}次检查: 任务ID={task_id}, 状态={status}\n"
                        }))
                    elif event_type == "SUCCESS":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"🎉 第{attempt}次检查成功！\n" + "-" * 50 + "\n"
                        }))
                    elif event_type == "FAIL":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"❌ 第{attempt}次检查失败: {status}\n" + "-" * 50 + "\n"
                        }))
                    elif event_type == "TIMEOUT":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"⚠️ 达到最大尝试次数，停止轮询\n" + "-" * 50 + "\n"
                        }))
                finally:
                    loop.close()

            result = generator.wait_for_video_completion(
                task_id,
                image_count=image_count,
                interval=10,
                max_attempts=100,
                callback=polling_callback
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if result["success"] and result["status"] == "SUCCESS":
                    cover_url = result.get("cover_url")
                    video_url = result.get("video_url")

                    filename = f"cogvideox_{int(time.time())}"
                    download_result = generator.download_video(video_url, cover_url, filename)

                    if download_result["success"]:
                        video_path = download_result["video_path"]

                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"\n✅ 视频生成完成！\n📁 视频保存路径: {video_path}\n💾 视频大小: {download_result.get('video_size', 0):.1f} MB\n"
                        }))

                        # 构建正确的视频URL
                        video_filename = os.path.basename(video_path)
                        video_url = f"/api/videos/{video_filename}"

                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_generated",
                            "video_path": video_url
                        }))

                        loop.run_until_complete(controller.send_toast("视频生成完成", "success"))
                    else:
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"\n❌ 视频下载失败: {download_result['message']}\n"
                        }))

                elif result.get("status") == "FAIL":
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "video_log",
                        "message": f"\n❌ 视频生成失败\n错误信息: {result.get('message', '未知错误')}\n"
                    }))

                else:
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "video_log",
                        "message": f"\n⚠️ 视频生成超时\n"
                    }))
            finally:
                loop.close()

        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "video_log",
                    "message": f"\n❌ 轮询检查出错: {str(e)}\n"
                }))
            finally:
                loop.close()

    threading.Thread(target=polling_thread, daemon=True).start()

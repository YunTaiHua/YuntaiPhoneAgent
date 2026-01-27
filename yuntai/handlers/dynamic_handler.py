import os
import threading
import time
import traceback
import customtkinter as ctk
import tkinter as tk  # 添加这个导入
from yuntai.gui_view import ThemeColors
from yuntai.multimodal_other import MultimodalOther  # 修复：从 yuntai 包导入
from yuntai.config import ZHIPU_API_KEY, PROJECT_ROOT   # 修复：从 yuntai 包导入


class DynamicHandler:
    """动态功能处理器 (图像/视频生成)"""

    def __init__(self, controller):
        self.controller = controller
        self.root = controller.root
        self.view = controller.view
        self.task_manager = controller.task_manager

    def show_panel(self):
        """显示动态功能页面"""
        try:
            self.view.create_dynamic_page()
            self._bind_events()

            if not hasattr(self.controller, 'multimodal_other'):
                # 修复导入路径
                self.controller.multimodal_other = MultimodalOther(ZHIPU_API_KEY, PROJECT_ROOT)

            self.controller.show_toast("动态功能页面已加载", "success")

        except Exception as e:
            print(f"❌ 加载动态功能页面失败: {e}")
            self.controller.show_toast(f"加载动态功能页面失败: {str(e)}", "error")
            traceback.print_exc()

    def _bind_events(self):
        """绑定动态功能页面事件"""
        generate_image_btn = self.view.get_component("generate_image_btn")
        if generate_image_btn:
            generate_image_btn.configure(command=self.generate_image)

        image_prompt_text = self.view.get_component("image_prompt_text")
        if image_prompt_text:
            image_prompt_text.bind("<Return>", lambda e: self._handle_image_generation_enter(e))

        preview_image_btn = self.view.get_component("preview_image_btn")
        if preview_image_btn:
            preview_image_btn.configure(command=self.preview_latest_image)

        generate_video_btn = self.view.get_component("generate_video_btn")
        if generate_video_btn:
            generate_video_btn.configure(command=self.generate_video)

        video_prompt_text = self.view.get_component("video_prompt_text")
        if video_prompt_text:
            video_prompt_text.bind("<Return>", lambda e: self._handle_video_generation_enter(e))

        preview_video_btn = self.view.get_component("preview_video_btn")
        if preview_video_btn:
            preview_video_btn.configure(command=self.preview_latest_video)

    def _handle_image_generation_enter(self, event):
        """处理图像生成文本框的回车事件"""
        modifiers = event.state
        ctrl_pressed = (modifiers & 0x0004) != 0  # Control 键
        shift_pressed = (modifiers & 0x0001) != 0  # Shift 键

        if ctrl_pressed or shift_pressed:
            # Ctrl+Enter 或 Shift+Enter：换行
            widget = event.widget
            widget.insert(tk.INSERT, "\n")
            return "break"
        else:
            # 普通的 Enter：生成图像
            self.generate_image()
            return "break"

    def _handle_video_generation_enter(self, event):
        """处理视频生成文本框的回车事件"""
        modifiers = event.state
        ctrl_pressed = (modifiers & 0x0004) != 0  # Control 键
        shift_pressed = (modifiers & 0x0001) != 0  # Shift 键

        if ctrl_pressed or shift_pressed:
            # Ctrl+Enter 或 Shift+Enter：换行
            widget = event.widget
            widget.insert(tk.INSERT, "\n")
            return "break"
        else:
            # 普通的 Enter：生成视频
            self.generate_video()
            return "break"

    def generate_image(self):
        """生成图像"""
        try:
            # 首先检查页面是否已创建
            if not self.view.get_component("dynamic_tabview"):
                self.controller.show_toast("请先进入动态功能页面", "warning")
                return

            # 获取所有需要的UI组件
            components = {}
            component_names = [
                "image_prompt_text", "image_size_var", "image_quality_var", "image_log_text"
            ]

            # 检查所有组件是否存在
            missing_components = []
            for name in component_names:
                component = self.view.get_component(name)
                if component:
                    components[name] = component
                else:
                    missing_components.append(name)

            if missing_components:
                error_msg = f"缺少UI组件: {', '.join(missing_components)}"
                print(f"❌ {error_msg}")
                self.controller.show_toast("UI组件未正确初始化，请刷新页面", "error")
                return

            prompt = components["image_prompt_text"].get("1.0", "end-1c").strip()
            if not prompt:
                self.controller.show_toast("请输入图像描述", "warning")
                return

            size = components["image_size_var"].get()
            quality = components["image_quality_var"].get()

            # 清空日志
            log_text = components["image_log_text"]
            log_text.configure(state="normal")
            log_text.delete("1.0", tk.END)
            log_text.insert("end", "🔄 正在生成图像...\n")
            log_text.configure(state="disabled")

            def generate_thread():
                try:
                    # 确保多模态处理器已初始化
                    if not hasattr(self.controller, 'multimodal_other'):
                        # 修复导入路径
                        self.controller.multimodal_other = MultimodalOther(ZHIPU_API_KEY, PROJECT_ROOT)

                    # 调用图像生成API
                    result = self.controller.multimodal_other.generate_image(prompt, size, quality)

                    def update_ui():
                        log_text.configure(state="normal")

                        if result["success"]:
                            image_data = result["data"]
                            image_url = image_data["data"][0]["url"]

                            try:
                                # 下载图像
                                filename = f"cogview_{int(time.time())}"
                                image_path = self.controller.multimodal_other.download_image(image_url, filename)

                                log_text.insert("end", f"✅ 图像生成成功！\n")
                                log_text.insert("end", f"📁 保存路径: {image_path}\n")
                                log_text.insert("end", f"🖼️ 图像尺寸: {size}\n")
                                log_text.insert("end", f"⚡ 生成质量: {quality}\n")

                                self.controller.show_toast("图像生成成功", "success")

                                # 存储最近生成的图像路径
                                self.controller.latest_image_path = image_path

                            except Exception as download_error:
                                log_text.insert("end", f"❌ 图像下载失败: {download_error}\n")
                                self.controller.show_toast("图像下载失败", "error")

                        else:
                            log_text.insert("end", f"❌ 图像生成失败: {result['message']}\n")
                            self.controller.show_toast("图像生成失败", "error")

                        log_text.configure(state="disabled")
                        log_text.see("end")

                    self.root.after(0, update_ui)

                except Exception as e:
                    def show_error():
                        log_text.configure(state="normal")
                        log_text.insert("end", f"❌ 图像生成出错: {str(e)}\n")
                        log_text.configure(state="disabled")
                        log_text.see("end")
                        self.controller.show_toast(f"图像生成出错: {str(e)[:30]}", "error")

                    self.root.after(0, show_error)

            # 在新线程中生成图像
            threading.Thread(target=generate_thread, daemon=True).start()

        except Exception as e:
            self.controller.show_toast(f"图像生成失败: {str(e)}", "error")

    def generate_video(self):
        """生成视频"""
        try:
            # 首先检查页面是否已创建
            if not self.view.get_component("dynamic_tabview"):
                self.controller.show_toast("请先进入动态功能页面", "warning")
                return

            # 获取所有需要的UI组件
            components = {}
            component_names = [
                "video_prompt_text",
                "image_url1_entry",
                "image_url2_entry",
                "video_size_var",
                "video_fps_var",
                "video_quality_var",
                "video_audio_check",
                "video_log_text",
            ]

            # 检查所有组件是否存在
            missing_components = []
            for name in component_names:
                component = self.view.get_component(name)
                if component:
                    components[name] = component
                else:
                    missing_components.append(name)

            if missing_components:
                error_msg = f"缺少UI组件: {', '.join(missing_components)}"
                print(f"❌ {error_msg}")
                self.controller.show_toast("UI组件未正确初始化，请刷新页面", "error")
                return

            prompt = components["video_prompt_text"].get("1.0", "end-1c").strip()
            if not prompt:
                self.controller.show_toast("请输入视频描述", "warning")
                return

            # 收集图片URL
            image_urls = []
            url1 = components["image_url1_entry"].get().strip()
            url2 = components["image_url2_entry"].get().strip()

            if url1:
                image_urls.append(url1)
            if url2:
                image_urls.append(url2)

            size = components["video_size_var"].get()

            # 处理帧率
            try:
                fps = int(components["video_fps_var"].get())
            except:
                fps = 30  # 默认值

            quality = components["video_quality_var"].get()
            with_audio = components["video_audio_check"].get()

            # 清空日志
            log_text = components["video_log_text"]
            log_text.configure(state="normal")
            log_text.delete("1.0", tk.END)
            log_text.insert("end", "🔄 正在提交视频生成任务...\n")
            log_text.configure(state="disabled")

            def generate_thread():
                try:
                    # 确保多模态处理器已初始化
                    if not hasattr(self.controller, 'multimodal_other'):
                        # 修复导入路径
                        self.controller.multimodal_other = MultimodalOther(ZHIPU_API_KEY, PROJECT_ROOT)

                    print(f"\n🎬 开始视频生成:")
                    print(f"  描述: {prompt}")
                    print(f"  图片数量: {len(image_urls)}")
                    print(f"  尺寸: {size}")
                    print(f"  帧率: {fps}")
                    print(f"  质量: {quality}")
                    print(f"  音效: {with_audio}")

                    # 调用视频生成API
                    result = self.controller.multimodal_other.generate_video(
                        prompt, image_urls, size, fps, quality, with_audio
                    )

                    # 在GUI线程中更新UI
                    def update_ui():
                        log_text.configure(state="normal")

                        if result["success"]:
                            task_id = result.get("task_id")
                            task_status = result.get("task_status", "UNKNOWN")

                            # 如果任务立即失败
                            if task_status == "FAIL":
                                error_msg = result.get('message', '未知错误')
                                log_text.insert("end", f"❌ 视频生成立即失败\n")
                                log_text.insert("end", f"错误信息: {error_msg}\n")

                                # 提供可能的解决方案
                                if "image" in error_msg.lower():
                                    log_text.insert("end", f"💡 可能的原因:\n")
                                    log_text.insert("end", f"  1. 图片URL不可访问\n")
                                    log_text.insert("end", f"  2. 图片格式不支持\n")
                                    log_text.insert("end", f"  3. 图片尺寸不匹配（双图时）\n")
                                    log_text.insert("end", f"  4. 图片过大或过小\n")

                                self.controller.show_toast(f"视频生成失败: {error_msg[:30]}", "error")

                            else:
                                # 正常提交成功
                                log_text.insert("end", f"✅ 视频生成任务已提交！\n")
                                log_text.insert("end", f"📋 任务ID: {task_id}\n")
                                log_text.insert("end", f"📊 初始状态: {task_status}\n")

                                if image_urls:
                                    if len(image_urls) == 1:
                                        log_text.insert("end", f"🖼️ 单图生成视频\n")
                                    elif len(image_urls) == 2:
                                        log_text.insert("end", f"🖼️ 双图生成视频（首尾帧）\n")
                                    log_text.insert("end", f"  使用图片: {len(image_urls)}张\n")
                                else:
                                    log_text.insert("end", f"📝 文字生成视频\n")

                                log_text.insert("end", f"📏 视频尺寸: {size}\n")
                                log_text.insert("end", f"🎞️ 帧率: {fps} FPS\n")
                                log_text.insert("end", f"🎵 音效: {'开启' if with_audio else '关闭'}\n")

                                # 根据图片数量设置不同的首次延迟提示
                                image_count = len(image_urls)
                                if image_count == 0:
                                    log_text.insert("end", f"⏰ 文字生成视频，首次状态检查将在10秒后开始\n")
                                else:
                                    log_text.insert("end", f"⏰ 图片生成视频，首次状态检查将在30秒后开始\n")

                                log_text.insert("end", f"🔁 后续每10秒自动检查一次\n")
                                log_text.insert("end", f"⏳ 请耐心等待结果...\n")

                                self.controller.show_toast("视频生成任务已提交", "success")

                                # 存储任务ID
                                self.controller.current_video_task_id = task_id

                                # 开始轮询检查结果，传递图片数量
                                self.start_video_result_polling(task_id, len(image_urls))

                        else:
                            error_msg = result.get('message', '未知错误')
                            log_text.insert("end", f"❌ 视频生成失败\n")
                            log_text.insert("end", f"错误信息: {error_msg}\n")

                            # 提供常见错误的解决方案
                            if "1210" in error_msg or "参数" in error_msg:
                                log_text.insert("end", f"💡 可能的原因:\n")
                                log_text.insert("end", f"  1. 图片URL格式不正确\n")
                                log_text.insert("end", f"  2. 双图生成时使用了单图格式\n")
                                log_text.insert("end", f"  3. 图片URL包含特殊字符\n")

                            if 'response_text' in result:
                                log_text.insert("end", f"API响应: {result['response_text'][:200]}...\n")

                            self.controller.show_toast(f"视频生成失败: {error_msg[:30]}", "error")

                        log_text.configure(state="disabled")
                        log_text.see("end")

                    self.root.after(0, update_ui)

                except Exception as e:
                    def show_error():
                        log_text.configure(state="normal")
                        log_text.insert("end", f"❌ 视频生成出错: {str(e)}\n")
                        log_text.configure(state="disabled")
                        log_text.see("end")
                        self.controller.show_toast(f"视频生成出错: {str(e)[:30]}", "error")

                    self.root.after(0, show_error)

            threading.Thread(target=generate_thread, daemon=True).start()

        except Exception as e:
            self.controller.show_toast(f"视频生成失败: {str(e)}", "error")

    def start_video_result_polling(self, task_id: str, image_count: int = 0):
        """开始轮询检查视频生成结果"""

        def polling_thread():
            try:
                log_text = self.view.get_component("video_log_text")
                if not log_text:
                    print("❌ 视频日志组件未找到")
                    return

                # 直接在日志中显示延迟信息
                log_text.configure(state="normal")
                if image_count == 0:
                    log_text.insert("end", f"\n⏰ 文字生成视频，首次状态检查将在10秒后开始...\n")
                else:
                    log_text.insert("end", f"\n⏰ 图片生成视频，首次状态检查将在30秒后开始...\n")
                log_text.insert("end", f"🔁 后续每10秒自动检查一次\n")
                log_text.configure(state="disabled")
                log_text.see("end")

                # 等待视频生成完成
                result = self.controller.multimodal_other.wait_for_video_completion(
                    task_id,
                    image_count=image_count,
                    interval=10,
                    max_attempts=30
                )

                # 结果处理
                if result["success"] and result["status"] == "SUCCESS":
                    cover_url = result.get("cover_url")
                    video_url = result.get("video_url")

                    # 下载视频
                    filename = f"cogvideox_{int(time.time())}"
                    download_result = self.controller.multimodal_other.download_video(video_url, cover_url, filename)

                    if download_result["success"]:
                        video_path = download_result["video_path"]
                        cover_path = download_result["cover_path"]

                        log_text.configure(state="normal")
                        log_text.insert("end", f"\n✅ 视频生成完成！\n")
                        log_text.insert("end", f"📁 视频保存路径: {video_path}\n")
                        log_text.insert("end", f"💾 视频大小: {download_result.get('video_size', 0):.1f} MB\n")
                        if cover_path:
                            log_text.insert("end", f"🖼️ 封面保存路径: {cover_path}\n")
                        log_text.configure(state="disabled")

                        self.controller.show_toast("视频生成完成", "success")

                        # 存储最近生成的视频路径
                        self.controller.latest_video_path = video_path
                        self.controller.latest_video_cover_path = cover_path

                    else:
                        log_text.configure(state="normal")
                        log_text.insert("end", f"\n❌ 视频下载失败: {download_result['message']}\n")
                        log_text.configure(state="disabled")

                elif result.get("status") == "FAIL":
                    log_text.configure(state="normal")
                    log_text.insert("end", f"\n❌ 视频生成失败\n")
                    log_text.insert("end", f"错误信息: {result.get('message', '未知错误')}\n")
                    log_text.configure(state="disabled")

                else:
                    log_text.configure(state="normal")
                    log_text.insert("end", f"\n⚠️ 视频生成超时\n")
                    log_text.configure(state="disabled")

            except Exception as e:
                log_text = self.view.get_component("video_log_text")
                if log_text:
                    log_text.configure(state="normal")
                    log_text.insert("end", f"\n❌ 轮询检查出错: {str(e)}\n")
                    log_text.configure(state="disabled")

        threading.Thread(target=polling_thread, daemon=True).start()

    def preview_latest_image(self):
        """预览最新生成的图像"""
        try:
            if hasattr(self.controller, 'latest_image_path') and self.controller.latest_image_path:
                from yuntai.multimodal_other import ImagePreviewWindow  # 修复导入路径

                # 检查PIL是否可用
                try:
                    from PIL import Image
                    # 在新窗口中预览图像
                    preview_window = ImagePreviewWindow(
                        self.root,
                        self.controller.latest_image_path,
                        "图像预览 - CogView-3-Flash"
                    )
                except ImportError:
                    # 如果PIL不可用，用默认程序打开
                    import subprocess
                    import platform
                    if platform.system() == "Windows":
                        os.startfile(self.controller.latest_image_path)
                    else:
                        self.controller.show_toast("PIL库未安装，无法预览", "warning")

            else:
                self.controller.show_toast("没有可预览的图像", "warning")

        except Exception as e:
            self.controller.show_toast(f"预览图像失败: {str(e)}", "error")

    def preview_latest_video(self):
        """预览最新生成的视频"""
        try:
            if hasattr(self.controller, 'latest_video_path') and self.controller.latest_video_path:
                from yuntai.multimodal_other import VideoPreviewWindow  # 修复导入路径

                cover_path = getattr(self.controller, 'latest_video_cover_path', None)

                # 在新窗口中预览视频
                preview_window = VideoPreviewWindow(
                    self.root,
                    self.controller.latest_video_path,
                    cover_path,
                    "视频预览 - CogVideoX-Flash"
                )
            else:
                self.controller.show_toast("没有可预览的视频", "warning")

        except Exception as e:
            self.controller.show_toast(f"预览视频失败: {str(e)}", "error")

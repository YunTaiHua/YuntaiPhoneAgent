"""
动态功能处理器模块
==================

本模块实现动态功能处理器，负责处理图像/视频生成功能。
使用 PyQt6 信号机制实现线程安全的 UI 更新。

主要功能：
    - 图像生成：使用智谱 AI CogView 模型生成图像
    - 视频生成：使用智谱 AI CogVideoX 模型生成视频
    - 结果轮询：异步轮询视频生成结果
    - 预览功能：预览生成的图像和视频

类说明：
    - DynamicHandler: 动态功能处理器类

使用示例：
    >>> from yuntai.handlers import DynamicHandler
    >>> 
    >>> # 创建处理器
    >>> handler = DynamicHandler(controller)
    >>> 
    >>> # 显示面板
    >>> handler.show_panel()
    >>> 
    >>> # 生成图像
    >>> handler.generate_image()
"""
import logging
import threading
import time
import traceback

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

from yuntai.processors.media_generator import MediaGenerator
from yuntai.views.dynamic import ImagePreviewWindow
from yuntai.core.config import ZHIPU_API_KEY, PROJECT_ROOT


class DynamicHandler(QObject):
    """
    动态功能处理器
    
    负责处理图像/视频生成功能，使用 PyQt6 信号机制实现线程安全的 UI 更新。
    
    Attributes:
        controller: GUI 控制器实例
        view: GUI 视图实例
        task_manager: 任务管理器实例
    
    使用示例：
        >>> handler = DynamicHandler(controller)
        >>> handler.show_panel()
    """
    
    # 定义信号用于跨线程UI更新
    image_log_signal = pyqtSignal(str)          # 图像日志信号
    video_log_signal = pyqtSignal(str)          # 视频日志信号
    image_update_signal = pyqtSignal(dict)      # 图像更新信号
    video_update_signal = pyqtSignal(dict)      # 视频更新信号
    video_error_signal = pyqtSignal(str)        # 视频错误信号

    def __init__(self, controller):
        """
        初始化动态功能处理器
        
        Args:
            controller: GUI 控制器实例
        """
        super().__init__()
        # 存储控制器引用
        self.controller = controller
        self.view = controller.view
        self.task_manager = controller.task_manager
        
        # 连接信号到槽函数
        self.image_log_signal.connect(self._on_image_log_message)
        self.video_log_signal.connect(self._on_video_log_message)
        self.image_update_signal.connect(self._on_image_update)
        self.video_update_signal.connect(self._on_video_update)
        self.video_error_signal.connect(self._on_video_error)
        
        logger.debug("DynamicHandler 初始化完成")

    def _on_image_log_message(self, message):
        """
        图像日志信号槽函数 - 在主线程中执行
        
        Args:
            message: 日志消息
        """
        try:
            log_text = self.view.get_component("image_log_text")
            if log_text:
                log_text.append(message)
                # 滚动到底部
                cursor = log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                log_text.setTextCursor(cursor)
        except Exception as e:
            logger.warning("图像日志更新失败: %s", str(e))
            print(f"[ERROR] _on_image_log_message: {e}")

    def _on_video_log_message(self, message):
        """
        视频日志信号槽函数 - 在主线程中执行
        
        Args:
            message: 日志消息
        """
        try:
            log_text = self.view.get_component("video_log_text")
            if log_text:
                log_text.append(message)
                # 滚动到底部
                cursor = log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                log_text.setTextCursor(cursor)
        except Exception as e:
            logger.warning("视频日志更新失败: %s", str(e))
            print(f"[ERROR] _on_video_log_message: {e}")

    def _on_image_update(self, result):
        """
        图像更新信号槽函数 - 在主线程中执行
        
        Args:
            result: 图像生成结果字典
        """
        try:
            if result["success"]:
                try:
                    # 提取图像数据
                    image_data = result["data"]
                    image_url = image_data["data"][0]["url"]
                except (KeyError, IndexError) as e:
                    self.image_log_signal.emit(f"❌ 解析图像数据失败: {e}")
                    self.controller.show_toast("解析图像数据失败", "error")
                    return

                try:
                    # 下载图像
                    filename = f"cogview_{int(time.time())}"
                    image_path = self.controller.media_generator.download_image(image_url, filename)

                    # 输出成功信息
                    self.image_log_signal.emit(f"✅ 图像生成成功！")
                    self.image_log_signal.emit(f"📁 保存路径: {image_path}")
                    self.image_log_signal.emit(f"🖼️ 图像尺寸: {result.get('size', 'N/A')}")
                    self.image_log_signal.emit(f"⚡ 生成质量: {result.get('quality', 'N/A')}")

                    self.controller.show_toast("图像生成成功", "success")
                    self.controller.latest_image_path = image_path
                    logger.info("图像生成成功: %s", image_path)

                except Exception as download_error:
                    self.image_log_signal.emit(f"❌ 图像下载失败: {download_error}")
                    self.controller.show_toast("图像下载失败", "error")
                    logger.error("图像下载失败: %s", str(download_error))

            else:
                self.image_log_signal.emit(f"❌ 图像生成失败: {result['message']}")
                self.controller.show_toast("图像生成失败", "error")
                logger.warning("图像生成失败: %s", result['message'])
        except Exception as e:
            logger.error("图像更新处理失败: %s", str(e), exc_info=True)
            print(f"[ERROR] _on_image_update: {e}")
            traceback.print_exc()

    def _on_video_update(self, result):
        """
        视频更新信号槽函数 - 在主线程中执行
        
        Args:
            result: 视频生成结果字典
        """
        try:
            if result["success"]:
                task_id = result.get("task_id")
                task_status = result.get("task_status", "UNKNOWN")

                if task_status == "FAIL":
                    # 视频生成立即失败
                    error_msg = result.get('message', '未知错误')
                    self.video_log_signal.emit(f"❌ 视频生成立即失败")
                    self.video_log_signal.emit(f"错误信息: {error_msg}")

                    # 提供可能的原因提示
                    if "image" in error_msg.lower():
                        self.video_log_signal.emit(f"💡 可能的原因:")
                        self.video_log_signal.emit(f"  1. 图片URL不可访问")
                        self.video_log_signal.emit(f"  2. 图片格式不支持")
                        self.video_log_signal.emit(f"  3. 图片尺寸不匹配（双图时）")
                        self.video_log_signal.emit(f"  4. 图片过大或过小")
                    
                    self.controller.show_toast(f"视频生成失败: {error_msg[:30]}", "error")
                    logger.warning("视频生成立即失败: %s", error_msg)

                else:
                    # 视频生成任务已提交
                    self.video_log_signal.emit(f"✅ 视频生成任务已提交！")
                    self.video_log_signal.emit(f"📏 视频尺寸: {result.get('size', 'N/A')}")

                    image_count = result.get('image_count', 0)
                    if image_count == 0:
                        self.video_log_signal.emit(f"⏰ 文字生成视频，首次状态检查将在10秒后开始")
                    else:
                        self.video_log_signal.emit(f"⏰ 图片生成视频，首次状态检查将在30秒后开始")

                    self.video_log_signal.emit(f"⏳ 请耐心等待结果...")

                    self.controller.show_toast("视频生成任务已提交", "success")
                    self.controller.current_video_task_id = task_id
                    logger.info("视频生成任务已提交: %s", task_id)
                    
                    # 开始轮询结果
                    self.start_video_result_polling(task_id, image_count)

            else:
                # 视频生成失败
                error_msg = result.get('message', '未知错误')
                self.video_log_signal.emit(f"❌ 视频生成失败")
                self.video_log_signal.emit(f"错误信息: {error_msg}")

                # 提供可能的原因提示
                if "1210" in error_msg or "参数" in error_msg:
                    self.video_log_signal.emit(f"💡 可能的原因:")
                    self.video_log_signal.emit(f"  1. 图片URL格式不正确")
                    self.video_log_signal.emit(f"  2. 双图生成时使用了单图格式")
                    self.video_log_signal.emit(f"  3. 图片URL包含特殊字符")

                if 'response_text' in result:
                    self.video_log_signal.emit(f"API响应: {result['response_text'][:200]}...")
                
                self.controller.show_toast(f"视频生成失败: {error_msg[:30]}", "error")
                logger.warning("视频生成失败: %s", error_msg)
        except Exception as e:
            logger.error("视频更新处理失败: %s", str(e), exc_info=True)
            print(f"[ERROR] _on_video_update: {e}")
            traceback.print_exc()

    def _on_video_error(self, error_msg):
        """
        视频错误信号槽函数 - 在主线程中执行
        
        Args:
            error_msg: 错误消息
        """
        try:
            self.video_log_signal.emit(f"❌ 视频生成出错: {error_msg}")
            self.controller.show_toast(f"视频生成出错: {error_msg[:30]}", "error")
            logger.error("视频生成出错: %s", error_msg)
        except Exception as e:
            logger.warning("视频错误处理失败: %s", str(e))
            print(f"[ERROR] _on_video_error: {e}")

    def show_panel(self):
        """显示动态功能页面"""
        logger.debug("显示动态功能页面")
        try:
            self.view.create_dynamic_page()
            self._bind_events()

            # 初始化媒体生成器
            if not hasattr(self.controller, 'media_generator'):
                self.controller.media_generator = MediaGenerator(ZHIPU_API_KEY, PROJECT_ROOT)
                logger.debug("媒体生成器初始化完成")

        except Exception as e:
            logger.error("加载动态功能页面失败: %s", str(e), exc_info=True)
            print(f"❌ 加载动态功能页面失败: {e}")
            self.controller.show_toast(f"加载动态功能页面失败: {str(e)}", "error")
            traceback.print_exc()

    def _bind_events(self):
        """绑定动态功能页面事件"""
        logger.debug("绑定动态功能页面事件")
        
        # 图像生成按钮
        generate_image_btn = self.view.get_component("generate_image_btn")
        if generate_image_btn:
            try:
                generate_image_btn.clicked.disconnect()
            except TypeError:
                pass
            generate_image_btn.clicked.connect(self.generate_image)

        # 图像预览按钮
        preview_image_btn = self.view.get_component("preview_image_btn")
        if preview_image_btn:
            try:
                preview_image_btn.clicked.disconnect()
            except TypeError:
                pass
            preview_image_btn.clicked.connect(self.preview_latest_image)

        # 视频生成按钮
        generate_video_btn = self.view.get_component("generate_video_btn")
        if generate_video_btn:
            try:
                generate_video_btn.clicked.disconnect()
            except TypeError:
                pass
            generate_video_btn.clicked.connect(self.generate_video)

        # 视频预览按钮
        preview_video_btn = self.view.get_component("preview_video_btn")
        if preview_video_btn:
            try:
                preview_video_btn.clicked.disconnect()
            except TypeError:
                pass
            preview_video_btn.clicked.connect(self.preview_latest_video)

    def generate_image(self):
        """生成图像"""
        logger.info("开始生成图像")
        
        try:
            # 检查页面是否已创建
            if not self.view.get_component("dynamic_tabview"):
                self.controller.show_toast("请先进入动态功能页面", "warning")
                return

            # 获取组件
            components = {}
            component_names = [
                "image_prompt_text",
                "image_size_menu",
                "image_quality_menu",
                "image_log_text",
            ]

            missing_components = []
            for name in component_names:
                component = self.view.get_component(name)
                if component:
                    components[name] = component
                else:
                    missing_components.append(name)

            if missing_components:
                error_msg = f"缺少UI组件: {', '.join(missing_components)}"
                logger.warning(error_msg)
                print(f"❌ {error_msg}")
                self.controller.show_toast("UI组件未正确初始化，请刷新页面", "error")
                return

            # 获取输入参数
            prompt = components["image_prompt_text"].toPlainText().strip()
            if not prompt:
                self.controller.show_toast("请输入图像描述", "warning")
                return

            size = components["image_size_menu"].currentText()
            quality = components["image_quality_menu"].currentText()

            # 清空日志并显示提示
            log_text = components["image_log_text"]
            log_text.clear()
            log_text.append("🔄 正在生成图像...")

            # 在后台线程中执行生成
            def generate_thread():
                try:
                    if not hasattr(self.controller, 'media_generator'):
                        self.controller.media_generator = MediaGenerator(ZHIPU_API_KEY, PROJECT_ROOT)

                    result = self.controller.media_generator.generate_image(prompt, size, quality)
                    result['size'] = size
                    result['quality'] = quality
                    self.image_update_signal.emit(result)

                except Exception as e:
                    logger.error("图像生成出错: %s", str(e), exc_info=True)
                    self.image_log_signal.emit(f"❌ 图像生成出错: {str(e)}")
                    self.controller.show_toast(f"图像生成出错: {str(e)[:30]}", "error")

            threading.Thread(target=generate_thread, daemon=True).start()

        except Exception as e:
            logger.error("图像生成失败: %s", str(e), exc_info=True)
            self.controller.show_toast(f"图像生成失败: {str(e)}", "error")

    def generate_video(self):
        """生成视频"""
        logger.info("开始生成视频")
        
        try:
            # 检查页面是否已创建
            if not self.view.get_component("dynamic_tabview"):
                self.controller.show_toast("请先进入动态功能页面", "warning")
                return

            # 获取组件
            components = {}
            component_names = [
                "video_prompt_text",
                "image_url1_entry",
                "image_url2_entry",
                "video_size_menu",
                "video_fps_menu",
                "video_quality_menu",
                "video_audio_check",
                "video_log_text",
            ]

            missing_components = []
            for name in component_names:
                component = self.view.get_component(name)
                if component:
                    components[name] = component
                else:
                    missing_components.append(name)

            if missing_components:
                error_msg = f"缺少UI组件: {', '.join(missing_components)}"
                logger.warning(error_msg)
                print(f"❌ {error_msg}")
                self.controller.show_toast("UI组件未正确初始化，请刷新页面", "error")
                return

            # 获取输入参数
            prompt = components["video_prompt_text"].toPlainText().strip()
            if not prompt:
                self.controller.show_toast("请输入视频描述", "warning")
                return

            # 获取图片 URL
            image_urls = []
            url1 = components["image_url1_entry"].text().strip()
            url2 = components["image_url2_entry"].text().strip()

            if url1:
                image_urls.append(url1)
            if url2:
                image_urls.append(url2)

            size = components["video_size_menu"].currentText()

            try:
                fps = int(components["video_fps_menu"].currentText())
            except (ValueError, TypeError):
                fps = 30

            quality = components["video_quality_menu"].currentText()
            with_audio = components["video_audio_check"].isChecked()

            # 清空日志并显示提示
            log_text = components["video_log_text"]
            log_text.clear()
            log_text.append("🔄 正在提交视频生成任务...")

            # 在后台线程中执行生成
            def generate_thread():
                try:
                    if not hasattr(self.controller, 'media_generator'):
                        self.controller.media_generator = MediaGenerator(ZHIPU_API_KEY, PROJECT_ROOT)

                    result = self.controller.media_generator.generate_video(
                        prompt, image_urls, size, fps, quality, with_audio
                    )
                    result['size'] = size
                    result['image_count'] = len(image_urls)
                    self.video_update_signal.emit(result)

                except Exception as e:
                    logger.error("视频生成出错: %s", str(e), exc_info=True)
                    self.video_error_signal.emit(str(e))

            threading.Thread(target=generate_thread, daemon=True).start()

        except Exception as e:
            logger.error("视频生成失败: %s", str(e), exc_info=True)
            self.controller.show_toast(f"视频生成失败: {str(e)}", "error")

    def start_video_result_polling(self, task_id: str, image_count: int = 0):
        """
        开始轮询检查视频生成结果
        
        Args:
            task_id: 任务 ID
            image_count: 图片数量（0 表示文字生成视频）
        """
        logger.info("开始轮询视频结果: %s", task_id)

        def polling_thread():
            try:
                # 定义轮询回调函数
                def polling_callback(event_type, attempt, task_id, status, interval):
                    if event_type == "START":
                        self.video_log_signal.emit("🎬 视频生成任务已提交")
                        self.video_log_signal.emit("-" * 50)
                    elif event_type == "WAIT":
                        wait_text = f"⏳ 等待10-30秒后检查..."
                        if attempt == 1:
                            wait_text = f"⏰ 首次检查在{interval}秒后开始"
                        self.video_log_signal.emit(wait_text)
                    elif event_type == "CHECK":
                        self.video_log_signal.emit(f"📊 第{attempt}次检查: 任务ID={task_id}, 状态={status}")
                    elif event_type == "SUCCESS":
                        self.video_log_signal.emit(f"🎉 第{attempt}次检查成功！")
                        self.video_log_signal.emit("-" * 50)
                    elif event_type == "FAIL":
                        self.video_log_signal.emit(f"❌ 第{attempt}次检查失败: {status}")
                        self.video_log_signal.emit("-" * 50)
                    elif event_type == "TIMEOUT":
                        self.video_log_signal.emit(f"⚠️ 达到最大尝试次数，停止轮询")
                        self.video_log_signal.emit("-" * 50)

                # 等待视频生成完成
                result = self.controller.media_generator.wait_for_video_completion(
                    task_id,
                    image_count=image_count,
                    interval=10,
                    max_attempts=100,
                    callback=polling_callback
                )

                if result["success"] and result["status"] == "SUCCESS":
                    # 下载视频和封面
                    cover_url = result.get("cover_url")
                    video_url = result.get("video_url")

                    filename = f"cogvideox_{int(time.time())}"
                    download_result = self.controller.media_generator.download_video(video_url, cover_url, filename)

                    if download_result["success"]:
                        video_path = download_result["video_path"]
                        cover_path = download_result["cover_path"]

                        self.video_log_signal.emit(f"\n✅ 视频生成完成！")
                        self.video_log_signal.emit(f"📁 视频保存路径: {video_path}")
                        self.video_log_signal.emit(f"💾 视频大小: {download_result.get('video_size', 0):.1f} MB")
                        if cover_path:
                            self.video_log_signal.emit(f"🖼️ 封面保存路径: {cover_path}")

                        self.controller.show_toast("视频生成完成", "success")
                        self.controller.latest_video_path = video_path
                        self.controller.latest_video_cover_path = cover_path
                        logger.info("视频生成完成: %s", video_path)

                    else:
                        self.video_log_signal.emit(f"\n❌ 视频下载失败: {download_result['message']}")
                        logger.warning("视频下载失败: %s", download_result['message'])

                elif result.get("status") == "FAIL":
                    self.video_log_signal.emit(f"\n❌ 视频生成失败")
                    self.video_log_signal.emit(f"错误信息: {result.get('message', '未知错误')}")
                    logger.warning("视频生成失败: %s", result.get('message', '未知错误'))

                else:
                    self.video_log_signal.emit(f"\n⚠️ 视频生成超时")
                    logger.warning("视频生成超时")

            except Exception as e:
                logger.error("轮询检查出错: %s", str(e), exc_info=True)
                self.video_log_signal.emit(f"\n❌ 轮询检查出错: {str(e)}")

        threading.Thread(target=polling_thread, daemon=True).start()

    def preview_latest_image(self):
        """预览最新生成的图像"""
        logger.debug("预览最新图像")
        
        try:
            if hasattr(self.controller, 'latest_image_path') and self.controller.latest_image_path:
                # 获取主窗口作为 parent
                main_window = self.view if hasattr(self.view, 'window') else None
                preview = ImagePreviewWindow(main_window, self.controller.latest_image_path)
                preview.exec()
            else:
                self.controller.show_toast("没有可预览的图像", "warning")
        except Exception as e:
            logger.error("预览图像失败: %s", str(e), exc_info=True)
            self.controller.show_toast(f"预览失败: {str(e)}", "error")
            traceback.print_exc()

    def preview_latest_video(self):
        """预览最新生成的视频"""
        logger.debug("预览最新视频")
        
        try:
            if hasattr(self.controller, 'latest_video_path') and self.controller.latest_video_path:
                import webbrowser
                webbrowser.open(f"file:///{self.controller.latest_video_path}")
            else:
                self.controller.show_toast("没有可预览的视频", "warning")
        except Exception as e:
            logger.error("预览视频失败: %s", str(e), exc_info=True)
            self.controller.show_toast(f"预览失败: {str(e)}", "error")
            traceback.print_exc()

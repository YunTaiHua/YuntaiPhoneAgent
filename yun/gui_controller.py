"""
GUIController - 事件处理和业务逻辑模块
负责处理用户操作，连接UI和后台任务
"""

import sys
import os
import threading
import queue
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import time
import datetime
import traceback
import subprocess
from typing import Optional, Dict, Any, Callable

# 第三方库
from zhipuai import ZhipuAI

# 项目模块
from yuntai.config import (
    Color, SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE
)
from yuntai.connection_manager import ConnectionManager
from yuntai.file_manager import FileManager
from yuntai.task_recognizer import TaskRecognizer
from yuntai.agent_executor import AgentExecutor
from yuntai.utils import Utils
from yuntai.reply_manager import SmartContinuousReplyManager

# 重构模块
from .gui_view import GUIView, ThemeColors
from .task_manager import TaskManager

# 使用新的统一配置
from .config import SCRCPY_PATH, validate_config, print_config_summary


class GUIController:
    """GUI控制器 - 处理所有用户事件和业务逻辑"""

    def __init__(self, root, project_root, scrcpy_path):
        self.root = root
        self.project_root = project_root

        # 使用统一配置的 scrcpy 路径
        self.scrcpy_path = SCRCPY_PATH

        # 初始化视图
        self.view = GUIView(root)

        # 初始化任务管理器
        self.task_manager = TaskManager(project_root, self.scrcpy_path)

        # 初始化输出捕获器（重要！）
        self.output_capture = None

        # 消息队列
        self.message_queue = queue.Queue()

        # 状态变量
        self.is_executing = False
        self.is_continuous_mode = False
        self.terminating = threading.Event()
        self.terminate_flag = threading.Event()

        # 活动线程和进程
        self.active_threads = []
        self.active_subprocesses = []

        # 初始化UI事件绑定
        self._bind_ui_events()

        # 启动消息处理循环
        self.root.after(100, self.process_messages)

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 延迟预加载TTS模块
        self.root.after(1000, self.preload_tts_modules)

        # 文件上传相关
        self.attached_files = []  # 存储已选文件路径
        self.multimodal_processor = None  # 多模态处理器

        # 多模态其他功能处理器（动态页面）
        self.multimodal_other = None  # 多模态其他功能处理器


    def _bind_ui_events(self):
        """绑定所有UI事件"""
        # 导航按钮点击事件
        nav_commands = [
            (self.view.get_component("nav_buttons")[0], self.show_dashboard),
            (self.view.get_component("nav_buttons")[1], self.show_connection_panel),
            (self.view.get_component("nav_buttons")[2], self.show_tts_panel),
            (self.view.get_component("nav_buttons")[3], self.show_history_panel),
            (self.view.get_component("nav_buttons")[4], self.show_dynamic_panel),  # 新增（动态页面）
            (self.view.get_component("nav_buttons")[5], self.show_settings_panel),
        ]

        for btn, command in nav_commands:
            if btn:
                btn.configure(command=command)

        # 控制台页面事件
        self._bind_dashboard_events()

        # 连接页面事件
        self._bind_connection_events()

        # TTS页面事件
        self._bind_tts_events()

        # 历史页面事件
        self._bind_history_events()

        # 设置页面事件
        self._bind_settings_events()

        # 设置动态页面
        self._bind_dynamic_events()


    #============动态页面按钮绑定============
    def _bind_dynamic_events(self):
        """绑定动态功能页面事件"""
        # print("🔗 绑定动态功能事件...")

        # 生成图像按钮
        generate_image_btn = self.view.get_component("generate_image_btn")
        if generate_image_btn:
            generate_image_btn.configure(command=self.generate_image)
            # print("✅ 绑定 generate_image_btn")
        else:
            return  # print("❌ generate_image_btn 未找到")

        # 图像描述文本框回车绑定
        image_prompt_text = self.view.get_component("image_prompt_text")
        if image_prompt_text:
            image_prompt_text.bind("<Return>",
                                   lambda e: self._handle_image_generation_enter(e))

        # 预览图像按钮
        preview_image_btn = self.view.get_component("preview_image_btn")
        if preview_image_btn:
            preview_image_btn.configure(command=self.preview_latest_image)
            # print("✅ 绑定 preview_image_btn")
        else:
            return  # print("❌ preview_image_btn 未找到")

        # 生成视频按钮
        generate_video_btn = self.view.get_component("generate_video_btn")
        if generate_video_btn:
            generate_video_btn.configure(command=self.generate_video)
            # print("✅ 绑定 generate_video_btn")
        else:
            return  # print("❌ generate_video_btn 未找到")

        # 视频描述文本框回车绑定
        video_prompt_text = self.view.get_component("video_prompt_text")
        if video_prompt_text:
            video_prompt_text.bind("<Return>",
                                   lambda e: self._handle_video_generation_enter(e))

        # 预览视频按钮
        preview_video_btn = self.view.get_component("preview_video_btn")
        if preview_video_btn:
            preview_video_btn.configure(command=self.preview_latest_video)
            # print("✅ 绑定 preview_video_btn")
        else:
            return  # print("❌ preview_video_btn 未找到")

        return  # print("🔗 动态功能事件绑定完成")

    def show_dynamic_panel(self):
        """显示动态功能页面"""
        try:
            print("🎨 加载动态功能页面...")
            self.view.create_dynamic_page()

            # 绑定事件
            self._bind_dynamic_events()

            # 初始化多模态其他功能处理器
            if not self.multimodal_other:
                from .multimodal_other import MultimodalOther
                from .config import ZHIPU_API_KEY, PROJECT_ROOT
                self.multimodal_other = MultimodalOther(ZHIPU_API_KEY, PROJECT_ROOT)

            print("✅ 动态功能页面已加载")

            self.show_toast("动态功能页面已加载", "success")

        except Exception as e:
            print(f"❌ 加载动态功能页面失败: {e}")
            self.show_toast(f"加载动态功能页面失败: {str(e)}", "error")
            import traceback
            traceback.print_exc()
    # ============动态页面按钮绑定结束===============


    # =============处理回车事件================
    def _handle_image_generation_enter(self, event):
        """处理图像生成文本框的回车事件"""
        # 检查是否按下了 Ctrl+Enter 或 Shift+Enter
        modifiers = event.state

        # 检查 Ctrl 或 Shift 是否被按下
        ctrl_pressed = (modifiers & 0x0004) != 0  # Control 键
        shift_pressed = (modifiers & 0x0001) != 0  # Shift 键

        if ctrl_pressed or shift_pressed:
            # Ctrl+Enter 或 Shift+Enter：换行
            widget = event.widget
            widget.insert(tk.INSERT, "\n")
            return "break"  # 阻止默认行为
        else:
            # 普通的 Enter：生成图像
            self.generate_image()
            return "break"  # 阻止默认行为

    def _handle_video_generation_enter(self, event):
        """处理视频生成文本框的回车事件"""
        # 检查是否按下了 Ctrl+Enter 或 Shift+Enter
        modifiers = event.state

        # 检查 Ctrl 或 Shift 是否被按下
        ctrl_pressed = (modifiers & 0x0004) != 0  # Control 键
        shift_pressed = (modifiers & 0x0001) != 0  # Shift 键

        if ctrl_pressed or shift_pressed:
            # Ctrl+Enter 或 Shift+Enter：换行
            widget = event.widget
            widget.insert(tk.INSERT, "\n")
            return "break"  # 阻止默认行为
        else:
            # 普通的 Enter：生成视频
            self.generate_video()
            return "break"  # 阻止默认行为

    def _handle_tts_synthesis_enter(self, event):
        """处理TTS合成文本框的回车事件"""
        # 检查是否按下了 Ctrl+Enter 或 Shift+Enter
        modifiers = event.state

        # 检查 Ctrl 或 Shift 是否被按下
        ctrl_pressed = (modifiers & 0x0004) != 0  # Control 键
        shift_pressed = (modifiers & 0x0001) != 0  # Shift 键

        if ctrl_pressed or shift_pressed:
            # Ctrl+Enter 或 Shift+Enter：换行
            widget = event.widget
            widget.insert(tk.INSERT, "\n")
            return "break"  # 阻止默认行为
        else:
            # 普通的 Enter：执行合成
            self.tts_start_synthesis()
            return "break"  # 阻止默认行为
    # ============处理回车事件结束===============


    def _bind_dashboard_events(self):
        """绑定控制台页面事件"""

        # 文件上传按钮
        attach_btn = self.view.get_component("attach_button")
        if attach_btn:
            attach_btn.configure(command=self.show_file_upload)

        # 执行命令按钮
        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            execute_btn.configure(command=self.execute_command)

        # 终止操作按钮
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            terminate_btn.configure(command=self.terminate_operation)

        # 语音播报按钮
        tts_btn = self.view.get_component("tts_button")
        if tts_btn:
            tts_btn.configure(command=self.show_tts_settings_popup)

        # 清空输出按钮
        clear_btn = self.view.get_component("clear_output_btn")
        if clear_btn:
            clear_btn.configure(command=self.clear_output)

        # 手机投屏按钮
        scrcpy_btn = self.view.get_component("scrcpy_button")
        if scrcpy_btn:
            scrcpy_btn.configure(command=self.show_scrcpy_popup)

        # 命令输入框回车事件
        command_input = self.view.get_component("command_input")
        if command_input:
            command_input.bind("<Return>", lambda e: self.execute_command())

        # 清空输出按钮
        clear_btn = self.view.get_component("clear_output_btn")
        if clear_btn:
            clear_btn.configure(command=self.clear_output)

    def _bind_connection_events(self):
        """绑定连接页面事件"""
        # 检测设备按钮
        detect_btn = self.view.get_component("detect_devices_btn")
        if detect_btn:
            detect_btn.configure(command=self.detect_devices_gui)

        # 连接设备按钮
        connect_btn = self.view.get_component("connect_device_btn")
        if connect_btn:
            connect_btn.configure(command=self.connect_device_gui)

        # 断开连接按钮
        disconnect_btn = self.view.get_component("disconnect_device_btn")
        if disconnect_btn:
            disconnect_btn.configure(command=self.disconnect_device)

        # 连接方式切换事件
        conn_var = self.view.get_component("conn_var")
        if conn_var:
            conn_var.trace("w", lambda *args: self._show_connection_form())

    def _bind_tts_events(self):
        """绑定TTS页面事件"""
        # 选择模型按钮
        select_gpt_btn = self.view.get_component("tts_select_gpt_btn")
        if select_gpt_btn:
            select_gpt_btn.configure(command=self.tts_select_gpt_model)

        select_sovits_btn = self.view.get_component("tts_select_sovits_btn")
        if select_sovits_btn:
            select_sovits_btn.configure(command=self.tts_select_sovits_model)

        select_audio_btn = self.view.get_component("tts_select_audio_btn")
        if select_audio_btn:
            select_audio_btn.configure(command=self.tts_select_ref_audio)

        select_text_btn = self.view.get_component("tts_select_text_btn")
        if select_text_btn:
            select_text_btn.configure(command=self.tts_select_ref_text)

        # 功能按钮
        synth_btn = self.view.get_component("tts_synth_btn")
        if synth_btn:
            synth_btn.configure(command=self.tts_start_synthesis)

        load_btn = self.view.get_component("tts_load_btn")
        if load_btn:
            load_btn.configure(command=self.tts_load_selected_models)

        stop_btn = self.view.get_component("tts_stop_btn")
        if stop_btn:
            stop_btn.configure(command=self.tts_stop_audio_playback)

        # TTS合成文本框回车绑定
        tts_text_input = self.view.get_component("tts_text_input")
        if tts_text_input:
            # 注意：CTkTextbox 的事件绑定方式
            tts_text_input.bind("<Return>",
                                lambda e: self._handle_tts_synthesis_enter(e))
            # 防止默认的回车行为
            tts_text_input.bind("<Control-Return>",
                                lambda e: self._handle_tts_synthesis_enter(e))
            tts_text_input.bind("<Shift-Return>",
                                lambda e: self._handle_tts_synthesis_enter(e))

        # 音频列表双击事件
        audio_listbox = self.view.get_component("tts_audio_listbox")
        if audio_listbox:
            audio_listbox.bind('<Double-Button-1>', self.tts_on_audio_double_click)

        # 音频列表按钮
        play_btn = self.view.get_component("tts_play_btn")
        if play_btn:
            play_btn.configure(command=self.tts_play_selected_audio)

        refresh_btn = self.view.get_component("tts_refresh_btn")
        if refresh_btn:
            refresh_btn.configure(command=self.tts_update_synthesized_list)

    def _bind_history_events(self):
        """绑定历史页面事件"""
        refresh_btn = self.view.get_component("refresh_history_btn")
        if refresh_btn:
            refresh_btn.configure(command=self.load_history_data)

        clear_btn = self.view.get_component("clear_history_btn")
        if clear_btn:
            clear_btn.configure(command=self.clear_history_data)

    def _bind_settings_events(self):
        """绑定设置页面事件"""
        settings_btns = [
            self.view.get_component("settings_btn_0"),
            self.view.get_component("settings_btn_1"),
            self.view.get_component("settings_btn_2"),
            self.view.get_component("settings_btn_3"),
        ]

        settings_commands = [
            self.show_connection_panel,
            self.check_system_gui,
            self.show_tts_panel,
            self.show_file_management,
        ]

        for btn, command in zip(settings_btns, settings_commands):
            if btn:
                btn.configure(command=command)

    # ========== 页面显示方法 ==========

    # 添加新方法：显示文件上传对话框
    def show_file_upload(self):
        """显示文件上传对话框"""
        # 简单检查：如果还在执行任务，直接拒绝
        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return

        try:
            # 调用视图的方法显示文件选择对话框
            file_paths = self.view.show_file_upload_dialog()

            if file_paths:
                # 过滤不支持的文件
                valid_files = []
                error_messages = []

                for file_path in file_paths:
                    supported, reason = self._check_file_supported(file_path)
                    if supported:
                        valid_files.append(file_path)
                    else:
                        file_name = os.path.basename(file_path)
                        error_messages.append(f"{file_name}: {reason}")

                # 添加到已选文件列表
                if valid_files:
                    self.attached_files.extend(valid_files)

                    # 更新UI显示 - 确保传递controller参数
                    if self.view:
                        self.view.show_attached_files(self.attached_files, self)  # 传递self作为controller

                    self.show_toast(f"已添加 {len(valid_files)} 个文件", "success")

                # 显示错误信息
                if error_messages:
                    error_count = len(error_messages)
                    if error_count <= 3:
                        for msg in error_messages:
                            self.show_toast(msg, "warning")
                    else:
                        self.show_toast(f"跳过 {error_count} 个不支持的文件", "warning")

        except Exception as e:
            self.show_toast(f"文件选择失败: {str(e)}", "error")
            print(f"❌ 文件选择失败: {e}")

    # 添加新方法：检查文件是否支持
    def _check_file_supported(self, file_path: str) -> tuple[bool, str]:
        """检查文件是否支持并返回原因"""
        # 初始化多模态处理器
        if not self.multimodal_processor:
            from .multimodal_processor import MultimodalProcessor
            self.multimodal_processor = MultimodalProcessor()

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"

        # 检查文件类型
        if not self.multimodal_processor.is_file_supported(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            return False, f"不支持的文件类型: {ext}"

        # 检查文件大小
        size_ok, msg = self.multimodal_processor.check_file_size(file_path)
        if not size_ok:
            return False, f"文件过大: {msg}"

        return True, ""

    def show_dashboard(self):
        """显示控制台页面"""
        self.view.create_dashboard_page()
        self._bind_dashboard_events()

    def show_connection_panel(self):
        """显示设备管理页面"""
        self.view.create_connection_page()
        self._bind_connection_events()
        self._update_connection_status_gui(self.task_manager.is_connected)

    def show_tts_panel(self):
        """显示TTS语音合成页面"""
        self.view.create_tts_page(self.task_manager.tts_manager)
        self._bind_tts_events()
        self.tts_update_synthesized_list()

    def show_history_panel(self):
        """显示历史记录页面"""
        self.view.create_history_page()
        self._bind_history_events()
        self.load_history_data()

    def show_settings_panel(self):
        """显示系统设置页面"""
        self.view.create_settings_page()
        self._bind_settings_events()

    # ==============动态页面功能=================
    def generate_video(self):
        """生成视频"""
        try:
            # 首先检查页面是否已创建
            if not self.view.get_component("dynamic_tabview"):
                self.show_toast("请先进入动态功能页面", "warning")
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
                self.show_toast("UI组件未正确初始化，请刷新页面", "error")
                return

            # 现在可以安全地使用组件
            prompt = components["video_prompt_text"].get("1.0", "end-1c").strip()
            if not prompt:
                self.show_toast("请输入视频描述", "warning")
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
                    if not self.multimodal_other:
                        from .config import ZHIPU_API_KEY, PROJECT_ROOT
                        from .multimodal_other import MultimodalOther
                        self.multimodal_other = MultimodalOther(ZHIPU_API_KEY, PROJECT_ROOT)

                    print(f"\n🎬 开始视频生成:")
                    print(f"  描述: {prompt}")
                    print(f"  图片数量: {len(image_urls)}")
                    print(f"  尺寸: {size}")
                    print(f"  帧率: {fps}")
                    print(f"  质量: {quality}")
                    print(f"  音效: {with_audio}")

                    # 调用视频生成API
                    result = self.multimodal_other.generate_video(
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

                                self.show_toast(f"视频生成失败: {error_msg[:30]}", "error")

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

                                self.show_toast("视频生成任务已提交", "success")

                                # 存储任务ID
                                self.current_video_task_id = task_id

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

                            self.show_toast(f"视频生成失败: {error_msg[:30]}", "error")

                        log_text.configure(state="disabled")
                        log_text.see("end")

                    self.root.after(0, update_ui)

                except Exception as e:
                    def show_error():
                        log_text.configure(state="normal")
                        log_text.insert("end", f"❌ 视频生成出错: {str(e)}\n")
                        log_text.configure(state="disabled")
                        log_text.see("end")
                        self.show_toast(f"视频生成出错: {str(e)[:30]}", "error")

                    self.root.after(0, show_error)

            threading.Thread(target=generate_thread, daemon=True).start()

        except Exception as e:
            self.show_toast(f"视频生成失败: {str(e)}", "error")
            import traceback
            traceback.print_exc()

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
                result = self.multimodal_other.wait_for_video_completion(
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
                    download_result = self.multimodal_other.download_video(video_url, cover_url, filename)

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

                        self.show_toast("视频生成完成", "success")

                        # 存储最近生成的视频路径
                        self.latest_video_path = video_path
                        self.latest_video_cover_path = cover_path

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
            if hasattr(self, 'latest_image_path') and self.latest_image_path:
                from .multimodal_other import ImagePreviewWindow

                # 检查PIL是否可用
                try:
                    from PIL import Image
                    # 在新窗口中预览图像
                    preview_window = ImagePreviewWindow(
                        self.root,
                        self.latest_image_path,
                        "图像预览 - CogView-3-Flash"
                    )
                except ImportError:
                    # 如果PIL不可用，用默认程序打开
                    import subprocess
                    import platform
                    if platform.system() == "Windows":
                        os.startfile(self.latest_image_path)
                    else:
                        self.show_toast("PIL库未安装，无法预览", "warning")

            else:
                self.show_toast("没有可预览的图像", "warning")

        except Exception as e:
            self.show_toast(f"预览图像失败: {str(e)}", "error")

    def preview_latest_video(self):
        """预览最新生成的视频"""
        try:
            if hasattr(self, 'latest_video_path') and self.latest_video_path:
                from .multimodal_other import VideoPreviewWindow

                cover_path = getattr(self, 'latest_video_cover_path', None)

                # 在新窗口中预览视频
                preview_window = VideoPreviewWindow(
                    self.root,
                    self.latest_video_path,
                    cover_path,
                    "视频预览 - CogVideoX-Flash"
                )
            else:
                self.show_toast("没有可预览的视频", "warning")

        except Exception as e:
            self.show_toast(f"预览视频失败: {str(e)}", "error")

    def generate_image(self):
        """生成图像"""
        try:
            # 首先检查页面是否已创建
            if not self.view.get_component("dynamic_tabview"):
                self.show_toast("请先进入动态功能页面", "warning")
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
                self.show_toast("UI组件未正确初始化，请刷新页面", "error")
                return

            prompt = components["image_prompt_text"].get("1.0", "end-1c").strip()
            if not prompt:
                self.show_toast("请输入图像描述", "warning")
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
                    if not self.multimodal_other:
                        from .config import ZHIPU_API_KEY, PROJECT_ROOT
                        from .multimodal_other import MultimodalOther
                        self.multimodal_other = MultimodalOther(ZHIPU_API_KEY, PROJECT_ROOT)

                    # 调用图像生成API
                    result = self.multimodal_other.generate_image(prompt, size, quality)

                    def update_ui():
                        log_text.configure(state="normal")

                        if result["success"]:
                            image_data = result["data"]
                            image_url = image_data["data"][0]["url"]

                            try:
                                # 下载图像
                                filename = f"cogview_{int(time.time())}"
                                image_path = self.multimodal_other.download_image(image_url, filename)

                                log_text.insert("end", f"✅ 图像生成成功！\n")
                                log_text.insert("end", f"📁 保存路径: {image_path}\n")
                                log_text.insert("end", f"🖼️ 图像尺寸: {size}\n")
                                log_text.insert("end", f"⚡ 生成质量: {quality}\n")

                                self.show_toast("图像生成成功", "success")

                                # 存储最近生成的图像路径
                                self.latest_image_path = image_path

                            except Exception as download_error:
                                log_text.insert("end", f"❌ 图像下载失败: {download_error}\n")
                                self.show_toast("图像下载失败", "error")

                        else:
                            log_text.insert("end", f"❌ 图像生成失败: {result['message']}\n")
                            self.show_toast("图像生成失败", "error")

                        log_text.configure(state="disabled")
                        log_text.see("end")

                    self.root.after(0, update_ui)

                except Exception as e:
                    def show_error():
                        log_text.configure(state="normal")
                        log_text.insert("end", f"❌ 图像生成出错: {str(e)}\n")
                        log_text.configure(state="disabled")
                        log_text.see("end")
                        self.show_toast(f"图像生成出错: {str(e)[:30]}", "error")

                    self.root.after(0, show_error)

            # 在新线程中生成图像
            threading.Thread(target=generate_thread, daemon=True).start()

        except Exception as e:
            self.show_toast(f"图像生成失败: {str(e)}", "error")
    # =================动态页面功能结束====================


    # ========== 连接管理方法 ==========

    def _show_connection_form(self):
        """显示连接表单"""
        conn_var = self.view.get_component("conn_var")
        usb_frame = self.view.get_component("usb_frame")
        wireless_frame = self.view.get_component("wireless_frame")

        if conn_var and usb_frame and wireless_frame:
            if conn_var.get() == "usb":
                wireless_frame.pack_forget()
                usb_frame.pack(fill="x")
            else:
                usb_frame.pack_forget()
                wireless_frame.pack(fill="x")

    def check_initial_connection(self):
        """检查初始连接"""
        self.task_manager.check_initial_connection()
        self._update_connection_status_gui(self.task_manager.is_connected)

    def connect_device_gui(self):
        """GUI界面连接设备"""
        config = self._get_connection_config_from_ui()
        if not config:
            return

        def connect_thread():
            success, device_id, message = self.task_manager.connect_device(config)

            if success:
                self.message_queue.put(("success", f"✅ {message}"))
                self._update_connection_status_gui(True)
            else:
                self.message_queue.put(("error", f"❌ 连接失败: {message}"))
                self._update_connection_status_gui(False)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _get_connection_config_from_ui(self):
        """从UI获取连接配置"""
        conn_var = self.view.get_component("conn_var")
        if not conn_var:
            self.show_toast("UI组件未初始化", "error")
            return None

        config = {
            "connection_type": conn_var.get(),
            "wireless_ip": "",
            "wireless_port": "5555",
            "usb_device_id": ""
        }

        if conn_var.get() == "usb":
            usb_entry = self.view.get_component("usb_entry")
            if usb_entry:
                device_id = usb_entry.get().strip()
                if not device_id:
                    self.show_toast("请输入USB设备ID", "warning")
                    return None
                config["usb_device_id"] = device_id
        else:
            ip_entry = self.view.get_component("ip_entry")
            port_entry = self.view.get_component("port_entry")

            if ip_entry and port_entry:
                ip = ip_entry.get().strip()
                port = port_entry.get().strip()

                if not ip:
                    self.show_toast("请输入IP地址", "warning")
                    return None

                config["wireless_ip"] = ip
                config["wireless_port"] = port if port else "5555"

        return config

    def detect_devices_gui(self):
        """GUI界面检测设备 - 弹窗显示结果"""

        def detect_thread():
            devices = self.task_manager.detect_devices()

            # 在主线程中显示弹窗
            def show_result_dialog():
                # 创建弹窗
                result_window = ctk.CTkToplevel(self.root)
                result_window.title("设备检测结果")
                result_window.geometry("600x500")
                result_window.resizable(True, True)
                result_window.transient(self.root)
                result_window.grab_set()

                # 标题
                ctk.CTkLabel(
                    result_window,
                    text="📱 设备检测结果",
                    font=("Microsoft YaHei", 20, "bold")
                ).pack(pady=20)

                if devices:
                    # 有设备的情况
                    device_count = len(devices)
                    status_text = f"✅ 检测到 {device_count} 个设备"

                    # 状态标签
                    ctk.CTkLabel(
                        result_window,
                        text=status_text,
                        font=("Microsoft YaHei", 14, "bold"),
                        text_color=ThemeColors.SUCCESS
                    ).pack(pady=(0, 10))

                    # 创建可复制的文本框显示设备列表
                    text_frame = ctk.CTkFrame(result_window, corner_radius=10)
                    text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

                    # 添加复制按钮的框架
                    toolbar = ctk.CTkFrame(text_frame, fg_color="transparent", height=40)
                    toolbar.pack(fill="x", padx=10, pady=(10, 0))

                    ctk.CTkLabel(
                        toolbar,
                        text="设备列表（可全选复制）:",
                        font=("Microsoft YaHei", 12, "bold")
                    ).pack(side="left")

                    # 复制按钮
                    def copy_to_clipboard():
                        # 复制所有设备信息到剪贴板
                        import pyperclip
                        device_text = "\n".join([f"{i + 1}. {device}" for i, device in enumerate(devices)])
                        pyperclip.copy(device_text)
                        self.show_toast("已复制到剪贴板", "success")

                    copy_btn = ctk.CTkButton(
                        toolbar,
                        text="📋 复制",
                        font=("Microsoft YaHei", 12),
                        height=30,
                        width=80,
                        command=copy_to_clipboard
                    )
                    copy_btn.pack(side="right", padx=5)

                    # 可复制的文本框
                    result_text = ctk.CTkTextbox(
                        text_frame,
                        font=("Consolas", 12),
                        activate_scrollbars=True
                    )
                    result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

                    # 填充设备信息
                    result_text.insert("1.0", "设备ID列表:\n" + "=" * 50 + "\n\n")
                    for i, device in enumerate(devices, 1):
                        result_text.insert("end", f"{i:2d}. {device}\n")

                    # 添加使用提示
                    result_text.insert("end", "\n" + "=" * 50 + "\n")
                    result_text.insert("end", "💡 使用说明:\n")
                    result_text.insert("end", "1. 选择文本进行复制\n")
                    result_text.insert("end", "2. 点击上方复制按钮可复制全部\n")
                    result_text.insert("end", "3. 在USB连接方式下使用设备ID连接\n")

                    # 1. 有设备的情况：
                    result_text.configure(state="normal")  # 先设为normal以插入内容
                    result_text.bind("<Control-c>", lambda e: copy_to_clipboard())
                    result_text.configure(state="disabled")  # 插入内容后设为disabled

                    # 2. 无设备的情况：
                    result_text.configure(state="normal")
                    result_text.configure(state="disabled")  # 插入内容后设为disabled

                else:
                    # 无设备的情况 - 也提供可复制的文本
                    status_text = "❌ 未检测到任何设备"

                    # 状态标签
                    ctk.CTkLabel(
                        result_window,
                        text=status_text,
                        font=("Microsoft YaHei", 14, "bold"),
                        text_color=ThemeColors.DANGER
                    ).pack(pady=(0, 10))

                    # 可复制的文本框
                    text_frame = ctk.CTkFrame(result_window, corner_radius=10)
                    text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

                    # 工具栏
                    toolbar = ctk.CTkFrame(text_frame, fg_color="transparent", height=40)
                    toolbar.pack(fill="x", padx=10, pady=(10, 0))

                    ctk.CTkLabel(
                        toolbar,
                        text="故障排除指南:",
                        font=("Microsoft YaHei", 12, "bold")
                    ).pack(side="left")

                    # 复制按钮
                    def copy_troubleshooting():
                        import pyperclip
                        troubleshooting_text = """请检查以下项目：
    1. 手机是否已通过USB线连接电脑
    2. 手机是否已开启【开发者选项】和【USB调试】
    3. 连接电脑时，手机上是否点击了【允许USB调试】
    4. 尝试重新插拔USB线或重启ADB服务
    5. 如果是无线连接，请确保IP和端口正确"""
                        pyperclip.copy(troubleshooting_text)
                        self.show_toast("故障排除指南已复制", "success")

                    copy_btn = ctk.CTkButton(
                        toolbar,
                        text="📋 复制指南",
                        font=("Microsoft YaHei", 12),
                        height=30,
                        width=100,
                        command=copy_troubleshooting
                    )
                    copy_btn.pack(side="right", padx=5)

                    # 文本框内容
                    result_text = ctk.CTkTextbox(
                        text_frame,
                        font=("Microsoft YaHei", 12),
                        activate_scrollbars=True
                    )
                    result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

                    # 填充故障排除信息
                    result_text.insert("1.0", "请检查以下项目：\n" + "=" * 50 + "\n\n")
                    checks = [
                        "1. 📱 手机是否已通过USB线连接电脑",
                        "2. ⚙️ 手机是否已开启【开发者选项】和【USB调试】",
                        "3. 📲 连接电脑时，手机上是否点击了【允许USB调试】",
                        "4. 🔄 尝试重新插拔USB线或重启ADB服务",
                        "5. 🔌 如果是无线连接，请确保IP和端口正确"
                    ]

                    for check in checks:
                        result_text.insert("end", f"{check}\n")

                    result_text.insert("end", "\n" + "=" * 50 + "\n")
                    result_text.insert("end", "💡 解决方案:\n")
                    result_text.insert("end", "• 在手机设置中搜索【开发者选项】\n")
                    result_text.insert("end", "• 打开【USB调试】开关\n")
                    result_text.insert("end", "• 连接电脑时授权调试权限\n")

                    result_text.configure(state="normal")

                # 关闭按钮
                ctk.CTkButton(
                    result_window,
                    text="关闭",
                    font=("Microsoft YaHei", 14),
                    height=40,
                    width=120,
                    command=result_window.destroy
                ).pack(pady=20)

                # ⚠️ 重要：移除下面这行代码，它会影响设备管理页面的布局
                # 不更新设备管理页面的状态，保持原样

                # 只显示一个简单的Toast提示
                if devices:
                    self.show_toast(f"检测到 {len(devices)} 个设备", "success")
                else:
                    self.show_toast("未检测到设备", "warning")

            # 在主线程中显示弹窗
            self.root.after(0, show_result_dialog)

        # 启动检测线程
        threading.Thread(target=detect_thread, daemon=True).start()

    def disconnect_device(self):
        """断开设备连接"""
        self.task_manager.disconnect_device()
        self._update_connection_status_gui(False)
        self.show_toast("设备已断开", "info")

    def _update_connection_status_gui(self, connected):
        """更新连接状态显示"""
        self.root.after(0, lambda: self.__update_connection_status_gui(connected))

    def __update_connection_status_gui(self, connected):
        """在GUI线程中更新连接状态"""
        connection_indicator = self.view.get_component("connection_indicator")
        status_label = self.view.get_component("status_label")

        if connected:
            if connection_indicator:
                connection_indicator.configure(
                    text="● 已连接",
                    text_color=ThemeColors.SUCCESS
                )
            if status_label:
                status_label.configure(text="设备已连接")
        else:
            if connection_indicator:
                connection_indicator.configure(
                    text="● 未连接",
                    text_color=ThemeColors.DANGER
                )
            if status_label:
                status_label.configure(text="设备未连接")

        # 更新连接页面状态 - 只显示状态，不显示设备ID
        conn_status_label = self.view.get_component("connection_status_label")
        if conn_status_label:
            if connected:
                conn_status_label.configure(
                    text="● 已连接",
                    text_color=ThemeColors.SUCCESS,
                    font=("Microsoft YaHei", 24, "bold")
                )
            else:
                conn_status_label.configure(
                    text="● 未连接",
                    text_color=ThemeColors.DANGER,
                    font=("Microsoft YaHei", 24, "bold")
                )

        # 删除对connection_info_label的更新，让第二行不显示
        conn_info_label = self.view.get_component("connection_info_label")
        if conn_info_label:
            conn_info_label.configure(text="")  # 清空第二行

    # ========== TTS管理方法 ==========

    def preload_tts_modules(self):
        """预加载TTS模块"""

        def load_async():
            success = self.task_manager.preload_tts_modules()
            self.update_tts_indicator(success)

        threading.Thread(target=load_async, daemon=True).start()

    def update_tts_indicator(self, enabled):
        """更新TTS状态指示器"""
        self.root.after(0, lambda: self._update_tts_indicator_gui(enabled))

    def _update_tts_indicator_gui(self, enabled):
        """在GUI线程中更新TTS指示器"""
        tts_indicator = self.view.get_component("tts_indicator")
        if tts_indicator:
            if enabled:
                tts_indicator.configure(
                    text="● TTS: 开启",
                    text_color=ThemeColors.SUCCESS
                )
            else:
                tts_indicator.configure(
                    text="● TTS: 关闭",
                    text_color=ThemeColors.WARNING
                )

    def tts_add_log(self, msg):
        """添加TTS操作日志"""
        tts_log_text = self.view.get_component("tts_log_text")
        if tts_log_text and tts_log_text.winfo_exists():
            def update_gui():
                try:
                    tts_log_text.config(state="normal")
                    timestamp = time.strftime("[%H:%M:%S]")
                    tts_log_text.insert("end", f"{timestamp} {msg}\n")
                    tts_log_text.see("end")
                    tts_log_text.config(state="disabled")
                except tk.TclError:
                    pass

            self.root.after(0, update_gui)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def tts_update_synthesized_list(self):
        """更新TTS历史音频列表"""
        tts_audio_listbox = self.view.get_component("tts_audio_listbox")
        if tts_audio_listbox and tts_audio_listbox.winfo_exists():
            def update_gui():
                try:
                    tts_audio_listbox.delete(0, tk.END)
                    # 强制重新加载文件
                    files = self.task_manager.tts_manager.load_synthesized_files()

                    if not files:
                        # 检查输出目录
                        output_dir = self.task_manager.tts_manager.default_tts_config["output_path"]
                        if os.path.exists(output_dir):
                            wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
                            self.tts_add_log(f"📁 发现 {len(wav_files)} 个音频文件在 {output_dir}")

                            # 添加到管理器
                            for wav_file in sorted(wav_files, reverse=True):
                                abs_path = os.path.join(output_dir, wav_file)
                                with self.task_manager.tts_manager.tts_synthesized_files_lock:
                                    self.task_manager.tts_manager.tts_synthesized_files.append((abs_path, wav_file))

                            files = self.task_manager.tts_manager.tts_synthesized_files

                    for idx, (_, filename) in enumerate(files):
                        tts_audio_listbox.insert(idx, filename)

                    self.tts_add_log(f"✅ 音频列表已更新，共 {len(files)} 个文件")

                except Exception as e:
                    self.tts_add_log(f"❌ 更新音频列表失败: {str(e)}")

            self.root.after(0, update_gui)

    def tts_play_selected_audio(self):
        """播放选中的历史音频"""
        # 首先检查是否已有音频在播放
        if hasattr(self.task_manager.tts_manager,
                   'is_playing_audio') and self.task_manager.tts_manager.is_playing_audio:
            self.tts_add_log("⚠️ 已有音频正在播放，跳过本次播放请求")
            return

        tts_audio_listbox = self.view.get_component("tts_audio_listbox")
        if not tts_audio_listbox:
            return

        selected_idx = tts_audio_listbox.curselection()
        if not selected_idx:
            self.tts_add_log("⚠️ 请先选择一个音频文件！")
            return

        idx = selected_idx[0]
        # 重新加载文件确保数据是最新的
        files = self.task_manager.tts_manager.load_synthesized_files()
        if 0 <= idx < len(files):
            audio_path = files[idx][0]

            # 检查文件是否存在
            if not os.path.exists(audio_path):
                self.tts_add_log(f"❌ 音频文件不存在: {audio_path}")
                return

            # 在新线程中播放
            def play_thread():
                try:
                    self.tts_add_log(f"🔊 正在播放: {os.path.basename(audio_path)}")
                    self.task_manager.tts_manager.play_audio_file(audio_path)
                    self.tts_add_log(f"✅ 播放完成: {os.path.basename(audio_path)}")
                except Exception as e:
                    self.tts_add_log(f"❌ 播放失败: {str(e)}")

            threading.Thread(target=play_thread, daemon=True).start()
        else:
            self.tts_add_log("❌ 选择的文件索引无效")

    def tts_on_audio_double_click(self, event):
        """双击播放音频"""
        self.tts_play_selected_audio()

    def tts_stop_audio_playback(self):
        """停止当前正在播放的音频"""
        if self.task_manager.stop_audio_playback():
            self.tts_add_log("⏹️ 已停止音频播放")
        else:
            self.tts_add_log("ℹ️ 当前没有正在播放的音频")

    def tts_select_gpt_model(self):
        """选择GPT模型"""
        if not self.task_manager.tts_manager.tts_files_database["gpt"]:
            self.tts_add_log("⚠️ 未找到任何GPT模型文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("gpt", filename):
                gpt_var = self.view.get_component("tts_gpt_var")
                if gpt_var:
                    gpt_var.set(filename)
                self.tts_add_log(f"📌 已选择GPT模型：{filename}")

        self._create_file_selection_popup(
            "选择GPT模型",
            self.task_manager.tts_manager.tts_files_database["gpt"],
            on_select
        )

    def tts_select_sovits_model(self):
        """选择SoVITS模型"""
        if not self.task_manager.tts_manager.tts_files_database["sovits"]:
            self.tts_add_log("⚠️ 未找到任何SoVITS模型文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("sovits", filename):
                sovits_var = self.view.get_component("tts_sovits_var")
                if sovits_var:
                    sovits_var.set(filename)
                self.tts_add_log(f"📌 已选择SoVITS模型：{filename}")

        self._create_file_selection_popup(
            "选择SoVITS模型",
            self.task_manager.tts_manager.tts_files_database["sovits"],
            on_select
        )

    def tts_select_ref_audio(self):
        """选择参考音频"""
        if not self.task_manager.tts_manager.tts_files_database["audio"]:
            self.tts_add_log("⚠️ 未找到任何参考音频文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("audio", filename):
                audio_var = self.view.get_component("tts_audio_var")
                if audio_var:
                    audio_var.set(filename)
                self.tts_add_log(f"📌 已选择参考音频：{filename}")

                # 自动匹配参考文本
                txt_filename = os.path.splitext(filename)[0] + '.txt'
                if txt_filename in self.task_manager.tts_manager.tts_files_database["text"]:
                    if self.task_manager.tts_manager.set_current_model("text", txt_filename):
                        text_var = self.view.get_component("tts_text_var")
                        if text_var:
                            text_var.set(txt_filename)
                        self.tts_add_log(f"✅ 自动匹配参考文本：{txt_filename}")

        self._create_file_selection_popup(
            "选择参考音频",
            self.task_manager.tts_manager.tts_files_database["audio"],
            on_select
        )

    def tts_select_ref_text(self):
        """选择参考文本"""
        if not self.task_manager.tts_manager.tts_files_database["text"]:
            self.tts_add_log("⚠️ 未找到任何参考文本文件！")
            return

        def on_select(filename):
            if self.task_manager.tts_manager.set_current_model("text", filename):
                text_var = self.view.get_component("tts_text_var")
                if text_var:
                    text_var.set(filename)
                self.tts_add_log(f"📌 已选择参考文本：{filename}")

        self._create_file_selection_popup(
            "选择参考文本",
            self.task_manager.tts_manager.tts_files_database["text"],
            on_select
        )

    def _create_file_selection_popup(self, title, file_dict, select_callback):
        """创建文件选择弹窗"""
        select_win = ctk.CTkToplevel(self.root)
        select_win.title(title)
        select_win.geometry("500x400")
        select_win.transient(self.root)
        select_win.grab_set()

        # 创建Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview", font=("Consolas", 12))
        style.configure("Custom.Treeview.Heading", font=("Consolas", 12, "bold"))

        tree = ttk.Treeview(select_win, style="Custom.Treeview", show="tree")
        tree.column("#0", width=450, minwidth=450)
        tree.pack(fill="both", expand=True, padx=15, pady=15)

        # 插入文件名
        filenames = sorted(file_dict.keys())
        for filename in filenames:
            tree.insert("", "end", text=filename, values=(filename))

        def confirm_selection():
            selected = tree.selection()
            if selected:
                filename = tree.item(selected[0], "values")[0]
                select_callback(filename)
                select_win.destroy()
            else:
                messagebox.showwarning("警告", "请选择一个文件！")

        # 确认按钮
        ctk.CTkButton(
            select_win,
            text="确认",
            font=("Microsoft YaHei", 12),
            width=120,
            height=35,
            command=confirm_selection
        ).pack(pady=15)

    def tts_load_selected_models(self):
        """加载选中的TTS模型"""
        if not self.task_manager.tts_manager.get_current_model("gpt") or \
                not self.task_manager.tts_manager.get_current_model("sovits"):
            self.tts_add_log("⚠️ 请先选择GPT和SoVITS模型！")
            return

        def load_thread():
            try:
                # 先确保模块已加载
                if not self.task_manager.tts_manager.tts_modules_loaded:
                    success, message = self.task_manager.tts_manager.load_tts_modules()
                    if not success:
                        self.tts_add_log(f"❌ 无法加载TTS模块: {message}")
                        return

                gpt_model = self.task_manager.tts_manager.get_current_model("gpt")
                sovits_model = self.task_manager.tts_manager.get_current_model("sovits")

                self.tts_add_log("🔄 正在加载GPT模型...")
                # 这里需要根据实际TTS模块的API调用加载函数
                # 示例代码，需要根据实际TTS模块调整
                if 'change_gpt_weights' in self.task_manager.tts_manager.tts_modules:
                    self.task_manager.tts_manager.tts_modules['change_gpt_weights'](gpt_model)
                    self.tts_add_log("✅ GPT模型加载成功")

                self.tts_add_log("🔄 正在加载SoVITS模型...")
                if 'change_sovits_weights' in self.task_manager.tts_manager.tts_modules:
                    self.task_manager.tts_manager.tts_modules['change_sovits_weights'](sovits_model)
                    self.tts_add_log("✅ SoVITS模型加载成功")

                self.tts_add_log("✅ TTS模型加载完成，可以开始合成")
            except Exception as e:
                self.tts_add_log(f"❌ TTS模型加载失败: {str(e)}")
                traceback.print_exc()

        threading.Thread(target=load_thread, daemon=True).start()

    def tts_start_synthesis(self):
        """启动TTS合成"""
        if self.task_manager.tts_manager.is_tts_synthesizing:
            self.tts_add_log("⚠️ 正在合成中，请稍候")
            return

        # 获取合成文本
        tts_text_input = self.view.get_component("tts_text_input")
        if not tts_text_input:
            return

        target_text = tts_text_input.get("1.0", "end-1c").strip()
        if not target_text:
            self.tts_add_log("⚠️ 合成文本不能为空！")
            return

        # 检查必要项
        if not self.task_manager.tts_manager.get_current_model("gpt") or \
                not self.task_manager.tts_manager.get_current_model("sovits"):
            self.tts_add_log("⚠️ 请先选择并加载模型！")
            return
        if not self.task_manager.tts_manager.get_current_model("audio"):
            self.tts_add_log("⚠️ 请先选择参考音频！")
            return
        if not self.task_manager.tts_manager.get_current_model("text"):
            self.tts_add_log("⚠️ 请先选择参考文本！")
            return

        ref_audio = self.task_manager.tts_manager.get_current_model("audio")
        ref_text = self.task_manager.tts_manager.get_current_model("text")

        # 启动合成线程
        def synth_thread():
            try:
                self.tts_add_log("🔄 语音合成中...")
                success, result = self.task_manager.tts_synthesize_text(
                    target_text, ref_audio, ref_text, auto_play=True
                )

                if success:
                    self.tts_add_log(f"✅ 合成完成")
                    self.tts_update_synthesized_list()
                else:
                    self.tts_add_log(f"❌ 合成失败: {result}")
            except Exception as e:
                self.tts_add_log(f"❌ 合成出错：{e}")

        threading.Thread(target=synth_thread, daemon=True).start()

    # ========== 命令执行方法 ==========

    def execute_command(self):
        """执行命令"""
        if self.is_executing:
            self.show_toast("请等待当前任务完成", "warning")
            return

        command_input = self.view.get_component("command_input")
        if not command_input:
            return

        command = command_input.get().strip()

        # 检查是否有附件
        has_attachments = len(self.attached_files) > 0

        if not command and not has_attachments:
            self.show_toast("请输入命令或选择文件", "warning")
            return

        # 清空输入框（无论是否有附件）
        command_input.delete(0, tk.END)

        # 检查终止标志
        if self.terminate_flag.is_set():
            self.terminate_flag.clear()

        # 确保输出捕获器存在并绑定
        output_text = self.view.get_component("output_text")
        if output_text:
            if not self.output_capture:
                from .output_capture import SimpleOutputCapture
                self.output_capture = SimpleOutputCapture(output_text)
            elif self.output_capture.text_widget != output_text:
                self.output_capture.set_text_widget(output_text)

        # 设置执行状态并禁用执行按钮，启用终止按钮
        self.is_executing = True
        self._disable_execute_button()
        self._enable_terminate_button()

        # 在新线程中执行命令
        def run_command():
            try:
                # 确保使用正确的输出流
                if self.output_capture:
                    sys.stdout = self.output_capture.custom_stdout
                    sys.stderr = self.output_capture.custom_stderr

                # 打印指令分割线
                print(f"\n{'=' * 180}\n")

                if has_attachments:
                    print(f"\n📋 多模态指令: {command if command else '[无文本]'}")
                    print(f"📎 附件数量: {len(self.attached_files)} 个文件\n")
                else:
                    print(f"\n📋 指令: {command}\n")

                # 检查是否是特殊命令
                if command.lower() == "quit":
                    self._append_output("👋 再见！\n")
                    self.root.after(1000, self.root.quit)
                    return
                elif command.lower() == "s":
                    self._append_output(f"🛑 检测到终止命令's'，发送终止信号\n")
                    self.root.after(0, self.terminate_operation)
                    return
                elif command.lower() in ["setup", "设置", "连接设置"]:
                    self.task_manager.setup_connection()
                    return
                elif command.lower() in ["show", "history", "历史", "查看历史"]:
                    self._show_history_command()
                    return
                elif command.lower() in ["clear", "清除", "清空", "清空历史"]:
                    self._clear_history_command()
                    return
                elif command.lower() == "detect" or command.lower() == "检测":
                    devices = self.task_manager.detect_devices()
                    self._append_output(f"📱 可用设备列表:\n")
                    if devices:
                        for i, device in enumerate(devices, 1):
                            self._append_output(f"  {i}. {device}\n")
                    else:
                        self._append_output(f"  未找到可用设备\n")
                    return

                # 检查连接状态（只有需要设备操作且没有附件时才检查）
                if not has_attachments and not self.task_manager.is_connected:
                    # 使用任务识别器判断任务类型
                    task_info = self.task_manager.task_recognizer.recognize_task_intent(command)
                    task_type = task_info.get("task_type", "free_chat")

                    # 只有非聊天任务才需要设备连接
                    if task_type != "free_chat":
                        self._append_output(f"❌ 设备未连接，请先连接设备\n")
                        return

                result = None

                # 根据是否有附件选择处理方式
                if has_attachments:
                    # 有附件：使用多模态处理
                    result = self._handle_multimodal_chat(command, self.attached_files)
                else:
                    # 无附件：使用任务管理器处理
                    result = self.task_manager.dispatch_task(
                        command,
                        self.task_manager.task_args,
                        self.task_manager.device_id
                    )

                #========== 新增：处理持续回复标记 ==========
                if result and isinstance(result, str) and "🔄CONTINUOUS_REPLY:" in result:
                    # 提取APP和目标对象
                    try:
                        parts = result.replace("🔄CONTINUOUS_REPLY:", "").split(":")
                        if len(parts) == 2:
                            target_app, target_object = parts

                            # 先确保设备已连接
                            if not self.task_manager.is_connected:
                                self._append_output(f"❌ 设备未连接，无法启动持续回复\n")
                                return

                            self._append_output(f"🚀 检测到持续回复模式: {target_app} -> {target_object}\n")
                            self._append_output(f"🔄 正在启动持续回复线程...\n")

                            # 启动持续回复线程
                            self.start_continuous_reply_thread(
                                self.task_manager.task_args,
                                target_app,
                                target_object,
                                self.task_manager.device_id
                            )

                            # 保持按钮状态（不要重置）
                            print("\n🔄 持续回复模式已启动，保持按钮状态")
                            return
                    except Exception as e:
                        print(f"❌ 解析持续回复标记失败: {e}")
                        result = f"❌ 解析持续回复参数失败: {str(e)}"
                # ========== 新增结束 ==========

                # 处理结果
                if result:
                    self._append_output(f"\n🎉 结果：{result}\n")

                # 重要：检查是否是持续回复模式
                if "持续回复模式" in str(result) or "continuous_reply" in str(result).lower():
                    print(f"🔄 检测到持续回复模式，保持按钮状态")
                    # 持续回复模式会自己管理按钮状态
                    return

            except Exception as e:
                self._append_output(f"\n❌ 错误：{str(e)}\n")
                traceback.print_exc()
            finally:
                # 清理已选文件（无论成功失败）
                def safe_clear():
                    try:
                        # 这里也要传递controller参数
                        self.clear_attached_files()
                    except Exception as e:
                        print(f"❌ 清理文件失败: {e}")

                # 延迟清理
                self.root.after(100, safe_clear)

                # 只有非持续回复模式才在这里重置按钮状态
                if not self.is_continuous_mode:
                    # 发送完成消息
                    self.message_queue.put(("success", "命令执行完成"))
                    # 恢复执行按钮状态
                    self.root.after(0, self._enable_execute_button)
                    self.root.after(0, self._disable_terminate_button)
                    self.is_executing = False

        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    # 添加新方法：处理多模态聊天
    def _handle_multimodal_chat(self, text: str, file_paths: list[str]) -> str:
        """处理多模态聊天（带附件）"""
        #print(f"\n🖼️ 多模态聊天处理中...")
        print(f"\n📋 文本: {text}")
        print(f"\n📎 附件: {len(file_paths)} 个文件")

        try:
            # 检查是否真的有附件
            if not file_paths or len(file_paths) == 0:
                print("⚠️  没有附件，退回普通聊天")
                # 如果没有附件，让任务管理器处理
                return self.task_manager._handle_free_chat(text)

            # 验证附件文件是否存在
            valid_files = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    valid_files.append(file_path)
                else:
                    print(f"⚠️  文件不存在: {file_path}")

            if len(valid_files) == 0:
                print("⚠️  没有有效的附件文件")
                return self.task_manager._handle_free_chat(text)

            # 初始化多模态处理器
            if not self.multimodal_processor:
                from .multimodal_processor import MultimodalProcessor
                self.multimodal_processor = MultimodalProcessor()

            # 获取历史对话（修复后的方法）
            history = self._get_chat_history_for_multimodal()

            #print(f"🔄 正在使用GLM-4.6v-flash分析内容...")

            # 使用GLM-4.6v-flash处理
            success, response = self.multimodal_processor.process_with_files(
                text=text,
                file_paths=valid_files,
                history=history,
                temperature=0.7,
                max_tokens=2000
            )

            if success:
                print(f"\n✅ 多模态分析完成")

                # 保存到对话历史
                self._save_multimodal_chat_history(text, valid_files, response)

                # 语音播报（如果有TTS）
                if self.task_manager.tts_manager.tts_enabled and len(response) > 5:
                    def speak_reply():
                        try:
                            # 使用智能语音合成
                            self.task_manager.tts_manager.speak_text_intelligently(response)
                        except Exception as e:
                            print(f"❌ 语音播报失败: {e}")

                    # 使用Timer延迟执行，避免阻塞
                    threading.Timer(0.5, speak_reply).start()

                return response
            else:
                error_msg = f"❌ 图片分析失败: {response}"
                print(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 多模态处理失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg

    def _get_chat_history_for_multimodal(self) -> list[Dict]:
        """获取用于多模态聊天的历史记录（转换为正确的消息格式）"""
        try:
            from .config import CONVERSATION_HISTORY_FILE

            history_data = self.task_manager.file_manager.safe_read_json_file(
                CONVERSATION_HISTORY_FILE,
                {"sessions": [], "free_chats": []}
            )

            free_chats = history_data.get("free_chats", [])[-3:]  # 只取最近3条，避免token过多

            # 转换为正确的消息格式
            messages = []
            for chat in free_chats:
                # 用户消息
                user_input = chat.get("user_input", "")
                if user_input:
                    messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": user_input}]
                    })

                # 助手消息
                assistant_reply = chat.get("assistant_reply", "")
                if assistant_reply:
                    messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": assistant_reply}]
                    })

            return messages

        except Exception as e:
            print(f"❌ 获取历史记录失败: {e}")
            return []

    def _save_multimodal_chat_history(self, text: str, file_paths: list[str], reply: str):
        """保存多模态聊天历史"""
        try:
            # 获取文件名列表
            file_names = [os.path.basename(f) for f in file_paths]

            # 格式与自由聊天统一
            session_data = {
                "type": "free_chat",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": text,
                "assistant_reply": reply,
                "model_used": "glm-4.6v-flash",
                "attached_files": file_names  # 额外字段记录附件
            }

            self.task_manager.file_manager.save_conversation_history(session_data)

        except Exception as e:
            print(f"❌ 保存聊天历史失败: {e}")

    def clear_attached_files(self):
        """清空已选文件列表并更新UI"""
        # 简单检查：如果还在执行任务，直接拒绝
        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return

        if not self.attached_files:
            return

        file_count = len(self.attached_files)
        self.attached_files.clear()

        # 更新UI显示 - 确保传递controller参数
        if self.view:
            self.view.show_attached_files(self.attached_files, self)  # 传递self作为controller

        self.show_toast(f"已清空 {file_count} 个文件", "success")

    def remove_attached_file(self, file_path: str):
        """从已选文件列表中移除单个文件"""
        # 简单检查：如果还在执行任务，直接拒绝
        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return

        if file_path in self.attached_files:
            self.attached_files.remove(file_path)

            # 更新UI显示 - 确保传递controller参数
            if self.view:
                self.view.show_attached_files(self.attached_files, self)  # 传递self作为controller

            file_name = os.path.basename(file_path)
            self.show_toast(f"已移除文件: {file_name}", "info")
        else:
            self.show_toast("文件不存在", "warning")

    def terminate_operation(self):
        """终止当前操作"""
        print("\n" + "=" * 180 + "\n")
        print("🛑 正在发送终止信号...")

        # 清理已完成的线程
        self._cleanup_finished_threads()

        if not self.active_threads and not self.is_continuous_mode:
            self.show_toast("没有正在执行的操作", "info")
            return

        # 设置终止标志
        self.terminating.set()
        self.terminate_flag.set()

        # 立即更新按钮状态
        self._disable_terminate_button()

        if self.is_continuous_mode:
            self._append_output(f"\n🛑 正在终止持续回复模式...\n")
            self.show_toast("已发送终止信号", "warning")
        else:
            self._append_output(f"\n🛑 正在终止当前任务...\n")
            self.show_toast("已发送终止信号", "warning")

    def _cleanup_active_threads(self):
        """清理活动线程"""
        # 移除已经结束的线程
        self.active_threads = [t for t in self.active_threads if t.is_alive()]
        print(f"📊 当前活动线程数: {len(self.active_threads)}")

    def _is_chat_command(self, command):
        """检查是否是聊天命令"""
        chat_keywords = ["你好", "谢谢", "请问", "怎么", "什么", "为什么", "如何", "?", "？"]
        return any(keyword in command for keyword in chat_keywords)

    def _show_history_command(self):
        """显示历史记录命令"""
        history = self.task_manager.file_manager.safe_read_json_file(
            "conversation_history.json",
            {"sessions": [], "free_chats": []}
        )

        self._append_output(f"\n📚 对话历史\n")

        # 显示聊天会话
        sessions = history.get("sessions", [])
        if sessions:
            self._append_output(f"📱 聊天会话 ({len(sessions)}条):\n")
            for i, session in enumerate(sessions[-5:], 1):
                self._append_output(f"\n{i}. {session.get('timestamp', '未知时间')}\n")
                self._append_output(
                    f"   目标: {session.get('target_app', '未知')} -> {session.get('target_object', '未知')}\n")
                self._append_output(f"   回复: {session.get('reply_generated', '')}\n")

        # 显示自由聊天
        free_chats = history.get("free_chats", [])
        if free_chats:
            self._append_output(f"\n💬 自由聊天 ({len(free_chats)}条):\n")
            for i, chat in enumerate(free_chats[-5:], 1):
                self._append_output(f"\n{i}. {chat.get('timestamp', '未知时间')}\n")
                self._append_output(f"   用户: {chat.get('user_input', '')}\n")
                self._append_output(f"   回复: {chat.get('assistant_reply', '')}\n")

        if not sessions and not free_chats:
            self._append_output(f"暂无对话历史\n")

    def _clear_history_command(self):
        """清空历史记录命令"""
        try:
            import os
            if os.path.exists("conversation_history.json"):
                os.remove("conversation_history.json")
                self._append_output(f"✅ 对话历史已清空\n")
                # 重新初始化文件
                with open("conversation_history.json", 'w', encoding='utf-8') as f:
                    import json
                    json.dump({"sessions": [], "free_chats": []}, f, ensure_ascii=False, indent=2)
            else:
                self._append_output(f"⚠️  没有对话历史文件\n")
        except Exception as e:
            self._append_output(f"❌ 清空历史失败：{e}\n")

    # ========== 输出管理方法 ==========

    def clear_output(self):
        """清空输出框"""
        output_text = self.view.get_component("output_text")
        if output_text:
            try:
                output_text.configure(state="normal")
                output_text.delete("1.0", tk.END)

                # 添加起始提示
                output_text.insert("end", "📱 Phone Agent 控制台\n")
                output_text.insert("end", "=" * 80 + "\n\n")

                output_text.configure(state="disabled")
                output_text.see("end")
            except tk.TclError:
                pass

    def _append_output(self, text):
        """追加输出到文本框"""
        output_text = self.view.get_component("output_text")
        if output_text:
            try:
                output_text.configure(state="normal")
                output_text.insert("end", text)
                output_text.see("end")
                output_text.configure(state="disabled")
            except tk.TclError:
                pass
        else:
            print(text, end="")

    def _disable_execute_button(self):
        """禁用执行按钮"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            execute_btn.configure(
                state="disabled",
                fg_color=ThemeColors.TEXT_DISABLED,
                text="执行中..."
            )

    def _enable_execute_button(self):
        """启用执行按钮"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            execute_btn.configure(
                state="normal",
                fg_color=ThemeColors.PRIMARY,
                text="执行命令"
            )

    def _enable_terminate_button(self):
        """启用终止按钮"""
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            terminate_btn.configure(
                state="normal",
                fg_color=ThemeColors.DANGER
            )

    # ========== 历史管理方法 ==========

    def load_history_data(self):
        """加载历史数据"""
        try:
            history = self.task_manager.file_manager.safe_read_json_file(
                CONVERSATION_HISTORY_FILE,
                {"sessions": [], "free_chats": []}
            )

            text_content = ""

            # 聊天会话
            sessions = history.get("sessions", [])
            if sessions:
                text_content += "📱 聊天会话:\n" + "=" * 50 + "\n\n"
                for session in sessions[-20:]:
                    text_content += f"时间: {session.get('timestamp', '未知')}\n"
                    text_content += f"目标: {session.get('target_app', '未知')} -> {session.get('target_object', '未知')}\n"
                    if session.get('reply_generated'):
                        text_content += f"回复: {session.get('reply_generated')}\n"
                    text_content += "-" * 30 + "\n\n"

            # 自由聊天
            free_chats = history.get("free_chats", [])
            if free_chats:
                text_content += "\n💬 自由聊天:\n" + "=" * 50 + "\n\n"
                for chat in free_chats[-20:]:
                    text_content += f"时间: {chat.get('timestamp', '未知')}\n"
                    text_content += f"用户: {chat.get('user_input', '')}\n"
                    text_content += f"回复: {chat.get('assistant_reply', '')}\n"
                    text_content += "-" * 30 + "\n\n"

            if not text_content:
                text_content = "暂无历史记录"

            # 更新历史文本框
            history_text = self.view.get_component("history_text")
            if history_text:
                history_text.configure(state="normal")
                history_text.delete("1.0", tk.END)
                history_text.insert("1.0", text_content)
                history_text.configure(state="disabled")

            self.show_toast("历史记录已刷新", "success")

        except Exception as e:
            self.show_toast(f"加载历史失败: {str(e)}", "error")

    def clear_history_data(self):
        """清空历史数据"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？此操作不可恢复！"):
            try:
                success = self.task_manager.file_manager.safe_write_json_file(
                    CONVERSATION_HISTORY_FILE,
                    {"sessions": [], "free_chats": []}
                )
                if success:
                    self.load_history_data()
                    self.show_toast("历史记录已清空", "success")
                else:
                    self.show_toast("清空历史失败", "error")
            except Exception as e:
                self.show_toast(f"清空历史失败: {str(e)}", "error")

    # ========== 其他功能方法 ==========

    def show_tts_settings_popup(self):
        """显示TTS设置弹窗"""
        popup = ctk.CTkToplevel(self.root)
        popup.title("🎤 TTS语音设置（语音合成有延迟）")
        popup.geometry("500x400")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        # 标题
        ctk.CTkLabel(
            popup,
            text="🎤 TTS语音设置（语音合成有延迟）",
            font=("Microsoft YaHei", 20, "bold")
        ).pack(pady=20)

        # TTS启用开关
        tts_enable_frame = ctk.CTkFrame(popup, fg_color="transparent")
        tts_enable_frame.pack(fill="x", padx=30, pady=10)

        tts_switch_var = ctk.StringVar(value="on" if self.task_manager.tts_manager.tts_enabled else "off")
        tts_switch = ctk.CTkSwitch(
            tts_enable_frame,
            text="启用语音播报",
            variable=tts_switch_var,
            onvalue="on",
            offvalue="off",
            font=("Microsoft YaHei", 14)
        )
        tts_switch.pack(pady=10)

        # 模型选择区域
        model_frame = ctk.CTkFrame(popup, fg_color="transparent")
        model_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            model_frame,
            text="选择TTS模型:",
            font=("Microsoft YaHei", 14)
        ).pack(anchor="w", pady=(0, 10))

        # GPT模型选择
        gpt_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        gpt_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            gpt_frame,
            text="GPT模型:",
            font=("Microsoft YaHei", 12),
            width=80
        ).pack(side="left")

        gpt_var = ctk.StringVar(value="未选择")
        current_gpt = self.task_manager.tts_manager.get_current_model("gpt")
        if current_gpt and os.path.basename(current_gpt) in self.task_manager.tts_manager.tts_files_database["gpt"]:
            gpt_var.set(os.path.basename(current_gpt))

        gpt_menu = ctk.CTkOptionMenu(
            gpt_frame,
            variable=gpt_var,
            values=["未选择"] + list(self.task_manager.tts_manager.tts_files_database["gpt"].keys()),
            font=("Microsoft YaHei", 12),
            width=200
        )
        gpt_menu.pack(side="left", padx=(10, 0))

        # SoVITS模型选择
        sovits_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        sovits_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            sovits_frame,
            text="SoVITS模型:",
            font=("Microsoft YaHei", 12),
            width=80
        ).pack(side="left")

        sovits_var = ctk.StringVar(value="未选择")
        current_sovits = self.task_manager.tts_manager.get_current_model("sovits")
        if current_sovits and os.path.basename(current_sovits) in self.task_manager.tts_manager.tts_files_database[
            "sovits"]:
            sovits_var.set(os.path.basename(current_sovits))

        sovits_menu = ctk.CTkOptionMenu(
            sovits_frame,
            variable=sovits_var,
            values=["未选择"] + list(self.task_manager.tts_manager.tts_files_database["sovits"].keys()),
            font=("Microsoft YaHei", 12),
            width=200
        )
        sovits_menu.pack(side="left", padx=(10, 0))

        # 参考音频选择
        audio_frame = ctk.CTkFrame(model_frame, fg_color="transparent")
        audio_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            audio_frame,
            text="参考音频:",
            font=("Microsoft YaHei", 12),
            width=80
        ).pack(side="left")

        audio_var = ctk.StringVar(value="未选择")
        current_audio = self.task_manager.tts_manager.get_current_model("audio")
        if current_audio and os.path.basename(current_audio) in self.task_manager.tts_manager.tts_files_database[
            "audio"]:
            audio_var.set(os.path.basename(current_audio))

        audio_menu = ctk.CTkOptionMenu(
            audio_frame,
            variable=audio_var,
            values=["未选择"] + list(self.task_manager.tts_manager.tts_files_database["audio"].keys()),
            font=("Microsoft YaHei", 12),
            width=200
        )
        audio_menu.pack(side="left", padx=(10, 0))

        # 按钮区域
        button_frame = ctk.CTkFrame(popup, fg_color="transparent")
        button_frame.pack(pady=20)

        def apply_settings():
            # 更新TTS启用状态
            self.task_manager.tts_manager.tts_enabled = (tts_switch_var.get() == "on")

            # 更新TTS指示器
            self.update_tts_indicator(self.task_manager.tts_manager.tts_enabled)

            # 更新模型选择
            if gpt_var.get() != "未选择":
                self.task_manager.tts_manager.set_current_model("gpt", gpt_var.get())

            if sovits_var.get() != "未选择":
                self.task_manager.tts_manager.set_current_model("sovits", sovits_var.get())

            if audio_var.get() != "未选择":
                self.task_manager.tts_manager.set_current_model("audio", audio_var.get())
                # 自动匹配参考文本
                txt_filename = os.path.splitext(audio_var.get())[0] + '.txt'
                if txt_filename in self.task_manager.tts_manager.tts_files_database["text"]:
                    self.task_manager.tts_manager.set_current_model("text", txt_filename)

            self.show_toast("TTS设置已保存", "success")
            popup.destroy()

        ctk.CTkButton(
            button_frame,
            text="保存设置",
            font=("Microsoft YaHei", 14),
            height=40,
            width=120,
            fg_color=ThemeColors.PRIMARY,
            command=apply_settings
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="取消",
            font=("Microsoft YaHei", 14),
            height=40,
            width=120,
            fg_color=ThemeColors.TEXT_SECONDARY,
            command=popup.destroy
        ).pack(side="left", padx=10)

    def check_system_gui(self):
        """可视化系统检查"""
        check_window = ctk.CTkToplevel(self.root)
        check_window.title("🔍 系统检查")
        check_window.geometry("600x400")
        check_window.resizable(False, False)
        check_window.transient(self.root)
        check_window.grab_set()

        # 标题
        title_frame = ctk.CTkFrame(check_window, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            title_frame,
            text="🔍 系统检查",
            font=("Microsoft YaHei", 20, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="正在检查系统配置和依赖...",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))

        # 检查结果区域
        result_frame = ctk.CTkFrame(check_window, corner_radius=10)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 创建滚动文本框显示结果
        result_text = ctk.CTkTextbox(
            result_frame,
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        result_text.pack(fill="both", expand=True, padx=10, pady=10)

        # 状态标签
        status_label = ctk.CTkLabel(
            check_window,
            text="准备开始检查...",
            font=("Microsoft YaHei", 11)
        )
        status_label.pack(side="left", padx=20, pady=(0, 10))

        # 检查线程
        def check_thread():
            try:
                check_window.after(0, lambda: status_label.configure(text="检查ADB环境..."))

                # 检查ADB
                adb_result = self.task_manager.utils.check_system_requirements()

                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "📱 ADB 环境检查\n")
                result_text.insert("end", "=" * 60 + "\n")
                if adb_result:
                    result_text.insert("end", "✅ ADB检查通过\n")
                    result_text.insert("end", "  已安装ADB工具\n")
                    result_text.insert("end", "  设备连接功能正常\n\n")
                else:
                    result_text.insert("end", "❌ ADB检查失败\n")
                    result_text.insert("end", "  请确保已安装ADB并添加到系统PATH\n\n")

                check_window.after(0, lambda: status_label.configure(text="检查模型API..."))

                # 检查模型API
                api_result = self.task_manager.utils.check_model_api(
                    "https://open.bigmodel.cn/api/paas/v4",
                    "autoglm-phone",
                    ZHIPU_API_KEY
                )

                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "🤖 模型API检查\n")
                result_text.insert("end", "=" * 60 + "\n")
                if api_result:
                    result_text.insert("end", "✅ 模型API检查通过\n")
                    result_text.insert("end", f"  模型: autoglm-phone\n")
                    result_text.insert("end", f"  密钥: {ZHIPU_API_KEY[:10]}...\n\n")
                else:
                    result_text.insert("end", "❌ 模型API检查失败\n")
                    result_text.insert("end", "  请检查API密钥或网络连接\n\n")

                check_window.after(0, lambda: status_label.configure(text="检查TTS功能..."))

                # 检查TTS功能
                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "🎤 TTS功能检查\n")
                result_text.insert("end", "=" * 60 + "\n")

                if self.task_manager.tts_manager.tts_available:
                    result_text.insert("end", "✅ TTS模块可用\n")

                    # 检查文件数据库
                    gpt_count = len(self.task_manager.tts_manager.tts_files_database["gpt"])
                    sovits_count = len(self.task_manager.tts_manager.tts_files_database["sovits"])
                    audio_count = len(self.task_manager.tts_manager.tts_files_database["audio"])
                    text_count = len(self.task_manager.tts_manager.tts_files_database["text"])

                    result_text.insert("end", f"  GPT模型: {gpt_count} 个\n")
                    result_text.insert("end", f"  SoVITS模型: {sovits_count} 个\n")
                    result_text.insert("end", f"  参考音频: {audio_count} 个\n")
                    result_text.insert("end", f"  参考文本: {text_count} 个\n")

                    if gpt_count > 0 and sovits_count > 0 and audio_count > 0 and text_count > 0:
                        result_text.insert("end", "  ✅ TTS资源完整\n")
                    else:
                        result_text.insert("end", "  ⚠️  TTS资源不完整\n")
                else:
                    result_text.insert("end", "❌ TTS模块不可用\n")
                    result_text.insert("end", "  请安装GPT-SoVITS并配置环境\n")

                result_text.insert("end", "\n")

                # 检查设备连接
                check_window.after(0, lambda: status_label.configure(text="检查设备连接..."))

                result_text.insert("end", "=" * 60 + "\n")
                result_text.insert("end", "📱 设备连接检查\n")
                result_text.insert("end", "=" * 60 + "\n")

                if self.task_manager.is_connected:
                    result_text.insert("end", f"✅ 设备已连接: {self.task_manager.device_id}\n")
                    result_text.insert("end",
                                       f"  连接类型: {self.task_manager.config.get('connection_type', '未知')}\n")
                else:
                    result_text.insert("end", "⚠️  设备未连接\n")
                    result_text.insert("end", "  请前往设备管理页面连接设备\n")

                # 总体结论
                result_text.insert("end", "\n" + "=" * 60 + "\n")
                result_text.insert("end", "📋 检查结论\n")
                result_text.insert("end", "=" * 60 + "\n")

                if adb_result and api_result:
                    result_text.insert("end", "🎉 系统检查通过，核心组件正常\n")
                    check_window.after(0, lambda: status_label.configure(
                        text="检查完成，核心组件正常",
                        text_color=ThemeColors.SUCCESS
                    ))
                else:
                    result_text.insert("end", "⚠️  系统检查发现一些问题\n")
                    check_window.after(0, lambda: status_label.configure(
                        text="检查完成，发现一些问题",
                        text_color=ThemeColors.WARNING
                    ))

                # 滚动到顶部
                result_text.see("1.0")

            except Exception as e:
                result_text.insert("end", f"\n❌ 检查过程中发生错误: {str(e)}\n")
                check_window.after(0, lambda: status_label.configure(
                    text=f"检查出错: {str(e)[:30]}...",
                    text_color=ThemeColors.DANGER
                ))

        # 启动检查线程
        threading.Thread(target=check_thread, daemon=True).start()

    def show_file_management(self):
        """显示文件管理"""
        try:
            info_text = f"""文件管理:

历史记录文件: {CONVERSATION_HISTORY_FILE}
日志目录: {RECORD_LOGS_DIR}/
永久记忆文件: {FOREVER_MEMORY_FILE}
连接配置文件: {CONNECTION_CONFIG_FILE}

TTS相关目录:
• GPT模型目录: {self.task_manager.tts_manager.default_tts_config['gpt_model_dir']}
• SoVITS模型目录: {self.task_manager.tts_manager.default_tts_config['sovits_model_dir']}
• 参考音频目录: {self.task_manager.tts_manager.default_tts_config['ref_audio_root']}
• TTS输出目录: {self.task_manager.tts_manager.default_tts_config['output_path']}

文件状态:
• 历史记录文件: {'存在' if os.path.exists(CONVERSATION_HISTORY_FILE) else '不存在'}
• 日志目录: {'存在' if os.path.exists(RECORD_LOGS_DIR) else '不存在'}
• 永久记忆文件: {'存在' if os.path.exists(FOREVER_MEMORY_FILE) else '不存在'}
• 连接配置文件: {'存在' if os.path.exists(CONNECTION_CONFIG_FILE) else '不存在'}"""
            messagebox.showinfo("文件管理", info_text)
        except Exception as e:
            messagebox.showerror("错误", f"获取文件信息失败: {str(e)}")

    # ========== 修改 gui_controller（原始）.py 中的 show_scrcpy_popup 方法 ==========

    def show_scrcpy_popup(self):
        """显示投屏设置弹窗"""
        popup = ctk.CTkToplevel(self.root)
        popup.title("📱 手机投屏")
        popup.geometry("400x350")  # 增加高度以容纳设备选择
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        # 标题
        ctk.CTkLabel(
            popup,
            text="📱 手机投屏设置",
            font=("Microsoft YaHei", 20, "bold")
        ).pack(pady=20)

        # 获取可用设备列表
        devices = self.task_manager.detect_devices()

        # 设备选择区域
        device_frame = ctk.CTkFrame(popup, fg_color="transparent")
        device_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            device_frame,
            text="选择设备:",
            font=("Microsoft YaHei", 14)
        ).pack(anchor="w", pady=(0, 5))

        # 设备选择变量
        device_var = ctk.StringVar()

        if devices:
            # 创建设备选择下拉菜单
            device_menu = ctk.CTkOptionMenu(
                device_frame,
                variable=device_var,
                values=devices,
                font=("Microsoft YaHei", 12),
                width=300
            )
            device_menu.pack(fill="x", pady=(0, 10))
            # 默认选择第一个设备
            if devices:
                device_var.set(devices[0])
        else:
            ctk.CTkLabel(
                device_frame,
                text="⚠️ 未检测到可用设备",
                font=("Microsoft YaHei", 12),
                text_color=ThemeColors.WARNING
            ).pack(pady=(0, 10))
            device_var.set("")

        # 窗口置顶勾选框
        always_on_top_var = ctk.BooleanVar(value=False)
        always_on_top_check = ctk.CTkCheckBox(
            popup,
            text="窗口置顶",
            variable=always_on_top_var,
            font=("Microsoft YaHei", 14)
        )
        always_on_top_check.pack(pady=10)

        # 启动按钮
        def start_scrcpy():
            if not devices:
                self.show_toast("没有可用设备", "warning")
                return

            selected_device = device_var.get()
            if not selected_device:
                self.show_toast("请选择一个设备", "warning")
                return

            # 构建命令
            cmd = [self.scrcpy_path, "--stay-awake"]

            # 添加设备选择参数
            cmd.append("-s")
            cmd.append(selected_device)

            if always_on_top_var.get():
                cmd.append("--always-on-top")

            try:
                # 在新线程中启动scrcpy
                def run_scrcpy():
                    try:
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        self.active_subprocesses.append(process)
                        self.show_toast(f"手机投屏已启动 ({selected_device})", "success")
                        # 等待进程结束
                        process.wait()
                        if process in self.active_subprocesses:
                            self.active_subprocesses.remove(process)
                    except Exception as e:
                        print(f"启动scrcpy失败: {e}")
                        self.show_toast(f"启动失败: {str(e)}", "error")

                threading.Thread(target=run_scrcpy, daemon=True).start()
                popup.destroy()

            except Exception as e:
                self.show_toast(f"启动失败: {str(e)}", "error")

        start_button = ctk.CTkButton(
            popup,
            text="启动投屏",
            font=("Microsoft YaHei", 14),
            height=40,
            width=120,
            fg_color="#9b59b6",
            command=start_scrcpy
        )
        start_button.pack(pady=20)

        # 提示信息
        info_label = ctk.CTkLabel(
            popup,
            text="注意：请确保手机已开启USB调试模式\n点击其他地方时窗口会自动最小化",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_SECONDARY
        )
        info_label.pack(pady=10)

    # ========== 工具方法 ==========

    def show_toast(self, message, type="info"):
        """显示Toast通知"""
        colors = {
            "info": ThemeColors.PRIMARY,
            "success": ThemeColors.SUCCESS,
            "warning": ThemeColors.WARNING,
            "error": ThemeColors.DANGER
        }

        try:
            toast = ctk.CTkLabel(
                self.root,
                text=message,
                font=("Microsoft YaHei", 12),
                text_color=ThemeColors.TEXT_PRIMARY,
                fg_color=colors[type],
                corner_radius=8
            )

            # 显示位置
            toast.place(relx=0.5, rely=0.9, anchor="center")

            # 3秒后自动隐藏
            def hide_toast():
                try:
                    toast.destroy()
                except:
                    pass

            self.root.after(3000, hide_toast)
        except:
            pass

    def process_messages(self):
        """处理消息队列"""
        try:
            while not self.message_queue.empty():
                msg_type, msg = self.message_queue.get_nowait()
                status_label = self.view.get_component("status_label")
                if status_label:
                    status_label.configure(text=msg)
        except queue.Empty:
            pass

        self.root.after(100, self.process_messages)

    def start_continuous_reply_thread(self, args, target_app: str, target_object: str,
                                      device_id: str):
        """启动持续回复线程"""
        # 确保没有已经在运行的持续回复
        if self.is_continuous_mode:
            print("⚠️  已经有持续回复在运行")
            return

        self.is_continuous_mode = True
        self.terminate_flag.clear()

        # 立即设置按钮状态
        self._disable_execute_button()
        self._enable_terminate_button()

        def continuous_thread():
            try:
                print(f"\n🚀 持续回复线程启动: {target_app} -> {target_object}")

                # 使用TerminableContinuousReplyManager
                from .agent_core import TerminableContinuousReplyManager
                manager = TerminableContinuousReplyManager(
                    args, target_app, target_object, device_id,
                    self.task_manager.zhipu_client, self.task_manager.file_manager,
                    terminate_flag=self.terminate_flag
                )

                # 运行持续回复循环
                success = manager.run_continuous_loop()

                if success:
                    print(f"\n✅ 持续回复完成")
                else:
                    print(f"\n⏹️  持续回复已终止")

            except Exception as e:
                print(f"\n❌ 持续回复错误：{str(e)}\n")
                import traceback
                traceback.print_exc()
            finally:
                # 重置状态
                self.is_continuous_mode = False
                self.terminate_flag.clear()
                # 恢复按钮状态
                self.root.after(0, self._reset_button_states)

        thread = threading.Thread(target=continuous_thread)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    def _cleanup_finished_threads(self):
        """清理已完成的线程"""
        # 移除已经结束的线程
        self.active_threads = [t for t in self.active_threads if t.is_alive()]

    def _reset_button_states(self):
        """重置按钮状态"""
        self._enable_execute_button()
        self._disable_terminate_button()
        self.is_executing = False
        #print("🔄 按钮状态已重置")

    def _disable_execute_button(self):
        """禁用执行按钮"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn and execute_btn.winfo_exists():
            execute_btn.configure(
                state="disabled",
                fg_color=ThemeColors.TEXT_DISABLED,
                text="执行中..."
            )

    def _enable_execute_button(self):
        """启用执行按钮"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn and execute_btn.winfo_exists():
            execute_btn.configure(
                state="normal",
                fg_color=ThemeColors.PRIMARY,
                text="执行命令"
            )

    def _disable_terminate_button(self):
        """禁用终止按钮"""
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn and terminate_btn.winfo_exists():
            terminate_btn.configure(
                state="disabled",
                fg_color=ThemeColors.TEXT_DISABLED
            )

    def _enable_terminate_button(self):
        """启用终止按钮"""
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn and terminate_btn.winfo_exists():
            terminate_btn.configure(
                state="normal",
                fg_color=ThemeColors.DANGER
            )

    def cleanup_on_exit(self):
        """退出时清理所有资源"""
        print("🧹 正在清理资源...")

        # 停止所有音频播放
        self.task_manager.stop_audio_playback()

        # 终止所有子进程
        for process in self.active_subprocesses:
            try:
                if process.poll() is None:  # 进程还在运行
                    process.terminate()
                    process.wait(timeout=2)
            except:
                pass

        # 等待活动线程结束（最多2秒）
        for thread in self.active_threads:
            if thread.is_alive():
                thread.join(timeout=1)

        # 清理TTS资源
        self.task_manager.cleanup()

    def on_closing(self):
        """窗口关闭事件"""
        self.cleanup_on_exit()
        self.root.quit()
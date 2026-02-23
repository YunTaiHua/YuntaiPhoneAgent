"""
GUIController - 事件处理和业务逻辑模块 (重构版)
负责处理用户操作，连接UI和后台任务，并协调各个Handler
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
from typing import Optional, Dict, Any, Callable

# 第三方库
from zhipuai import ZhipuAI

# 项目模块
from yuntai.core.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE
)
# 引用 TaskManager（保留用于连接管理和TTS）
from yuntai.services.task_manager import TaskManager
# 引用新的 TaskChain
from yuntai.chains import TaskChain, ReplyChain
from yuntai.agents import JudgementAgent
# 引用 Handlers
from yuntai.handlers import ConnectionHandler, TTSHandler, DynamicHandler, SystemHandler

# 使用新的统一配置
from yuntai.core.config import SCRCPY_PATH, validate_config, print_config_summary, ZHIPU_CHAT_MODEL, ZHIPU_MODEL, \
    ZHIPU_API_BASE_URL
from yuntai.gui.gui_view import GUIView
from yuntai.core.config import ThemeColors
from yuntai.gui.output_capture import SimpleOutputCapture


class GUIController:
    """GUI控制器 - 处理所有用户事件和业务逻辑"""

    def __init__(self, root, project_root, scrcpy_path):
        self.root = root
        self.project_root = project_root
        self.scrcpy_path = SCRCPY_PATH

        # 初始化视图
        self.view = GUIView(root)

        # 初始化任务管理器（保留用于连接管理和TTS）
        self.task_manager = TaskManager(project_root, self.scrcpy_path)

        # 初始化新的 TaskChain
        self.task_chain = TaskChain(
            device_id="",
            file_manager=self.task_manager.file_manager,
            tts_manager=self.task_manager.tts_manager
        )

        # 初始化判断 Agent
        self.judgement_agent = JudgementAgent()

        # 初始化输出捕获器
        self.output_capture = None

        # 消息队列
        self.message_queue = queue.Queue()

        # 状态变量
        self.is_executing = False
        self.is_continuous_mode = False
        self.terminating = threading.Event()
        self.terminate_flag = threading.Event()
        self._current_reply_chain = None

        # 活动线程和进程
        self.active_threads = []
        self.active_subprocesses = []

        # 设备类型（默认Android）
        self.device_type = "android"

        # 初始化 Handlers
        self.connection_handler = ConnectionHandler(self)
        self.tts_handler = TTSHandler(self)
        self.dynamic_handler = DynamicHandler(self)
        self.system_handler = SystemHandler(self)

        # 初始化UI事件绑定
        self._bind_ui_events()

        # 启动消息处理循环
        self.root.after(100, self.process_messages)

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 延迟预加载TTS模块
        self.root.after(1000, self.preload_tts_modules)

        # 文件上传相关
        self.attached_files = []
        self.multimodal_processor = None

        # 设置设备类型变化回调
        self._setup_device_type_callback()

    def _bind_ui_events(self):
        """绑定所有UI事件（主要是导航和主控台）"""
        # 导航按钮点击事件
        nav_commands = [
            (self.view.get_component("nav_buttons")[0], self.show_dashboard),
            (self.view.get_component("nav_buttons")[1], self.connection_handler.show_panel),
            (self.view.get_component("nav_buttons")[2], self.tts_handler.show_panel),
            (self.view.get_component("nav_buttons")[3], self.system_handler.show_history_panel),
            (self.view.get_component("nav_buttons")[4], self.dynamic_handler.show_panel),
            (self.view.get_component("nav_buttons")[5], self.system_handler.show_settings_panel),
        ]

        for btn, command in nav_commands:
            if btn:
                btn.configure(command=command)

        # 绑定控制台页面事件
        self._bind_dashboard_events()

    def _bind_dashboard_events(self):
        """绑定控制台页面事件"""
        attach_btn = self.view.get_component("attach_button")
        if attach_btn:
            attach_btn.configure(command=self.show_file_upload)

        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            execute_btn.configure(command=self.execute_command)

        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            terminate_btn.configure(command=self.terminate_operation)

        # TTS设置按钮（调用TTS Handler的弹窗）
        tts_btn = self.view.get_component("tts_button")
        if tts_btn:
            tts_btn.configure(command=self.tts_handler.show_tts_settings_popup)

        clear_btn = self.view.get_component("clear_output_btn")
        if clear_btn:
            clear_btn.configure(command=self.clear_output)

        scrcpy_btn = self.view.get_component("scrcpy_button")
        if scrcpy_btn:
            scrcpy_btn.configure(command=self.connection_handler.show_scrcpy_popup)

        command_input = self.view.get_component("command_input")
        if command_input:
            command_input.bind("<Return>", self._on_command_input_return)
            command_input.bind("<Shift-Return>", self._on_command_input_shift_return)
            command_input.bind("<Control-Return>", self._on_command_input_ctrl_return)

        enter_btn = self.view.get_component("enter_button")
        if enter_btn:
            enter_btn.configure(command=self.simulate_enter)

        # 绑定主题切换按钮
        theme_toggle_btn = self.view.get_component("theme_toggle_button")
        if theme_toggle_btn:
            theme_toggle_btn.configure(command=self.toggle_theme)

        # 绑定文件管理上传按钮
        file_upload_btn = self.view.get_component("file_upload_button")
        if file_upload_btn:
            file_upload_btn.configure(command=self.show_file_upload)

        # 绑定快捷键按钮
        for key, app_name in SHORTCUTS.items():
            shortcut_btn = self.view.get_component(f"shortcut_btn_{key}")
            if shortcut_btn:
                shortcut_btn.configure(command=lambda k=key: self.execute_shortcut(k))

    def _on_command_input_return(self, event=None):
        """输入框按Enter键执行命令"""
        self.execute_command()
        return "break"

    def _on_command_input_shift_return(self, event=None):
        """Shift+Enter换行"""
        text_widget = self.view.get_component("command_input")
        if text_widget:
            text_widget.insert(tk.INSERT, "\n")
            text_widget.see(tk.INSERT)
        return "break"

    def _on_command_input_ctrl_return(self, event=None):
        """Ctrl+Enter换行"""
        text_widget = self.view.get_component("command_input")
        if text_widget:
            text_widget.insert(tk.INSERT, "\n")
            text_widget.see(tk.INSERT)
        return "break"

    # ============ 页面显示方法 ============

    def show_dashboard(self):
        """显示控制台页面"""
        self.view.create_dashboard_page()
        self._bind_dashboard_events()

    # ============ 文件上传与附件管理 ============

    def show_file_upload(self):
        """显示文件上传对话框"""
        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return

        try:
            file_paths = self.view.show_file_upload_dialog()
            if file_paths:
                valid_files = []
                error_messages = []

                for file_path in file_paths:
                    supported, reason = self._check_file_supported(file_path)
                    if supported:
                        valid_files.append(file_path)
                    else:
                        file_name = os.path.basename(file_path)
                        error_messages.append(f"{file_name}: {reason}")

                if valid_files:
                    self.attached_files.extend(valid_files)
                    self.view.show_attached_files(self.attached_files, self)
                    self.show_toast(f"已添加 {len(valid_files)} 个文件", "success")

                if error_messages:
                    error_count = len(error_messages)
                    if error_count <= 3:
                        for msg in error_messages:
                            self.show_toast(msg, "warning")
                    else:
                        self.show_toast(f"跳过 {error_count} 个不支持的文件", "warning")

        except Exception as e:
            self.show_toast(f"文件选择失败: {str(e)}", "error")

    def _check_file_supported(self, file_path: str) -> tuple[bool, str]:
        """检查文件是否支持"""
        if not self.multimodal_processor:
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            self.multimodal_processor = MultimodalProcessor()

        if not os.path.exists(file_path):
            return False, "文件不存在"
        if not self.multimodal_processor.is_file_supported(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            return False, f"不支持的文件类型: {ext}"

        size_ok, msg = self.multimodal_processor.check_file_size(file_path)
        if not size_ok:
            return False, f"文件过大: {msg}"
        return True, ""

    def clear_attached_files(self):
        """清空已选文件列表"""
        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return

        file_count = len(self.attached_files)
        self.attached_files.clear()
        if self.view:
            self.view.show_attached_files(self.attached_files, self)
        if file_count > 0:
            self.show_toast(f"已清空 {file_count} 个文件", "success")

    def remove_attached_file(self, file_path: str):
        """移除单个文件"""
        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return
        if file_path in self.attached_files:
            self.attached_files.remove(file_path)
            if self.view:
                self.view.show_attached_files(self.attached_files, self)
            self.show_toast(f"已移除: {os.path.basename(file_path)}", "info")

    # ============ 核心命令执行 ============

    def execute_command(self):
        """执行命令"""
        if self.is_executing:
            self.show_toast("请等待当前任务完成", "warning")
            return

        command_input = self.view.get_component("command_input")
        if not command_input: return
        command = command_input.get("1.0", "end-1c").strip()
        has_attachments = len(self.attached_files) > 0

        if not command and not has_attachments:
            self.show_toast("请输入命令或选择文件", "warning")
            return

        command_input.delete("1.0", tk.END)
        command_input.configure(height=35)
        if self.terminate_flag.is_set():
            self.terminate_flag.clear()

        output_text = self.view.get_component("output_text")
        if output_text:
            if not self.output_capture:
                self.output_capture = SimpleOutputCapture(output_text)
            elif self.output_capture.text_widget != output_text:
                self.output_capture.set_text_widget(output_text)

        self.is_executing = True
        self._disable_execute_button()
        self._enable_terminate_button()

        def run_command():
            try:
                if self.output_capture:
                    sys.stdout = self.output_capture.custom_stdout
                    sys.stderr = self.output_capture.custom_stderr

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'═' * 9} [{timestamp} 对话开始] {'═' * 9}\n")
                if has_attachments:
                    print(f"💭 多模态指令: {command if command else '[无文本]'}")
                    print(f"📎 附件数量: {len(self.attached_files)} 个文件")
                else:
                    print(f"💭 指令: {command}")

                # 特殊命令处理
                if command.lower() == "quit":
                    self._append_output("👋 再见！\n")
                    self.root.after(1000, self.root.quit)
                    return
                elif command.lower() == "s":
                    self._append_output(f"🛑 检测到终止命令's'\n")
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
                    self._append_output(f"📱 可用设备列表:")
                    if devices:
                        for i, device in enumerate(devices, 1):
                            self._append_output(f"  {i}. {device}")
                    else:
                        self._append_output(f"  未找到可用设备")
                    return

                if not has_attachments and not self.task_manager.is_connected:
                    task_result = self.judgement_agent.judge(command)
                    task_type = task_result.task_type
                    if task_type != "free_chat":
                        self._append_output(f"❌ 设备未连接，请先连接设备")
                        return

                result = None
                if has_attachments:
                    result = self._handle_multimodal_chat(command, self.attached_files)
                else:
                    self._sync_device_to_task_chain()
                    result, task_info = self.task_chain.process(command)

                # 持续回复处理
                if result and isinstance(result, str) and "🔄CONTINUOUS_REPLY:" in result:
                    try:
                        parts = result.replace("🔄CONTINUOUS_REPLY:", "").split(":")
                        if len(parts) == 2:
                            target_app, target_object = parts
                            if not self.task_manager.is_connected:
                                self._append_output(f"❌ 设备未连接，无法启动持续回复")
                                return
                            self.start_continuous_reply_thread(
                                self.task_manager.task_args, target_app, target_object, self.task_manager.device_id
                            )
                            return
                    except Exception as e:
                        print(f"❌ 解析持续回复标记失败: {e}")
                        result = f"❌ 解析持续回复参数失败: {str(e)}"

                if result:
                    self._append_output(f"🎉 结果：{result}")

                if "持续回复模式" in str(result) or "continuous_reply" in str(result).lower():
                    print(f"🔄 检测到持续回复模式，保持按钮状态")
                    return

            except Exception as e:
                self._append_output(f"❌ 错误：{str(e)}\n")
                traceback.print_exc()
            finally:
                def safe_clear():
                    try:
                        self.clear_attached_files()
                    except Exception as e:
                        print(f"❌ 清理文件失败: {e}")

                self.root.after(100, safe_clear)

                if not self.is_continuous_mode:
                    self.message_queue.put(("success", "命令执行完成"))
                    self.root.after(0, self._enable_execute_button)
                    self.root.after(0, self._disable_terminate_button)
                    self.is_executing = False

        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    def _handle_multimodal_chat(self, text: str, file_paths: list[str]) -> str:
        """处理多模态聊天"""
        print(f"📋 文本: {text}")
        print(f"📌 附件: {len(file_paths)} 个文件")

        try:
            if not file_paths or len(file_paths) == 0:
                return self.chat_agent.chat(text) if hasattr(self, 'chat_agent') else "无法处理"

            valid_files = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    valid_files.append(file_path)
                else:
                    print(f"⚠️  文件不存在: {file_path}")

            if len(valid_files) == 0:
                return self.chat_agent.chat(text) if hasattr(self, 'chat_agent') else "无法处理"

            if not self.multimodal_processor:
                from yuntai.processors.multimodal_processor import MultimodalProcessor
                self.multimodal_processor = MultimodalProcessor()

            history = self._get_chat_history_for_multimodal()

            success, response, audio_result = self.multimodal_processor.process_with_files(
                text=text, file_paths=valid_files, history=history,
                temperature=0.7, max_tokens=2000
            )

            if success:
                print(f"✅ 多模态分析完成")
                if audio_result:
                    audio_transcription = audio_result.get("audio_transcription", "")
                    if audio_transcription: pass

                self._save_multimodal_chat_history(text, valid_files, response)

                if self.task_manager.tts_manager.tts_enabled and len(response) > 5:
                    def speak_reply():
                        try:
                            self.task_manager.tts_manager.speak_text_intelligently(response)
                        except Exception as e:
                            print(f"❌ 语音播报失败: {e}")

                    threading.Timer(0.5, speak_reply).start()

                return response
            else:
                error_msg = f"❌ 多模态分析失败: {response}"
                print(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 多模态处理失败: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def _get_chat_history_for_multimodal(self) -> list[Dict]:
        try:
            from yuntai.core.config import CONVERSATION_HISTORY_FILE
            history_data = self.task_manager.file_manager.safe_read_json_file(
                CONVERSATION_HISTORY_FILE, {"sessions": [], "free_chats": []}
            )
            free_chats = history_data.get("free_chats", [])[-3:]
            messages = []
            for chat in free_chats:
                user_input = chat.get("user_input", "")
                if user_input:
                    messages.append({"role": "user", "content": [{"type": "text", "text": user_input}]})
                assistant_reply = chat.get("assistant_reply", "")
                if assistant_reply:
                    messages.append({"role": "assistant", "content": [{"type": "text", "text": assistant_reply}]})
            return messages
        except Exception as e:
            print(f"❌ 获取历史记录失败: {e}")
            return []

    def _save_multimodal_chat_history(self, text: str, file_paths: list[str], reply: str):
        try:
            file_names = [os.path.basename(f) for f in file_paths]
            session_data = {
                "type": "free_chat",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": text,
                "assistant_reply": reply,
                "model_used": ZHIPU_CHAT_MODEL,
                "attached_files": file_names
            }
            self.task_manager.file_manager.save_conversation_history(session_data)
        except Exception as e:
            print(f"❌ 保存聊天历史失败: {e}")

    def terminate_operation(self):
        """终止当前操作"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'═' * 9} [{timestamp} 操作终止] {'═' * 9}")
        print("🛑 正在发送终止信号...\n")
        self._cleanup_active_threads()
        
        self.task_chain.stop_continuous_reply()
        
        if hasattr(self, '_current_reply_chain') and self._current_reply_chain:
            self._current_reply_chain.stop()
        
        if not self.active_threads and not self.is_continuous_mode:
            self.show_toast("没有正在执行的操作", "info")
            return

        self.terminating.set()
        self.terminate_flag.set()
        self._disable_terminate_button()

        if self.is_continuous_mode:
            self._append_output(f"\n🛑 正在终止持续回复模式...")
        else:
            self._append_output(f"\n🛑 正在终止当前任务...")
        self.show_toast("已发送终止信号", "warning")

    def simulate_enter(self):
        """模拟回车键效果"""
        print("[用户点击模拟回车按钮]")
        try:
            from yuntai.core.agent_executor import AgentExecutor
            AgentExecutor.user_confirm()
        except Exception as e:
            print(f"⚠️  发送确认信号失败: {e}")

        output_text = self.view.get_component("output_text")
        if output_text:
            try:
                output_text.configure(state="normal")
                output_text.insert("end", "[用户已确认]")
                output_text.see("end")
                output_text.configure(state="disabled")
            except Exception:
                pass

    def _setup_device_type_callback(self):
        """设置设备类型变化回调"""

        def on_device_type_change(device_type: str):
            self.device_type = device_type
            self.task_manager.set_device_type(device_type)
            self.task_manager.agent_executor.set_device_type(device_type)

        self.view._device_type_callback = on_device_type_change

    def _sync_device_to_task_chain(self):
        """同步设备ID到TaskChain"""
        if self.task_manager.device_id:
            self.task_chain.set_device_id(self.task_manager.device_id)

    # ============ 持续回复 ============

    def start_continuous_reply_thread(self, args, target_app: str, target_object: str, device_id: str):
        if self.is_continuous_mode:
            print("⚠️  已经有持续回复在运行")
            return
        self.is_continuous_mode = True
        self.terminate_flag.clear()
        self._disable_execute_button()
        self._enable_terminate_button()

        def continuous_thread():
            try:
                print(f"🚀 持续回复线程启动: {target_app} -> {target_object}")
                
                from yuntai.chains import ReplyChain
                self._current_reply_chain = ReplyChain(
                    device_id=device_id,
                    file_manager=self.task_manager.file_manager,
                    tts_manager=self.task_manager.tts_manager
                )
                
                success, result = self._current_reply_chain.continuous_reply(target_app, target_object)
                
                if success:
                    print(f"✅ {result}")
                else:
                    print(f"⏹️  {result}")
            except Exception as e:
                print(f"❌ 持续回复错误：{str(e)}\n")
                traceback.print_exc()
            finally:
                self.is_continuous_mode = False
                self.terminate_flag.clear()
                self.root.after(0, self._reset_button_states)

        thread = threading.Thread(target=continuous_thread)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    # ============ 输出管理 ============

    def clear_output(self):
        """清空输出框"""
        output_text = self.view.get_component("output_text")
        if output_text:
            try:
                output_text.configure(state="normal")
                output_text.delete("1.0", tk.END)
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
                if "Press Enter" in text or "请按回车" in text or "请登录" in text or "需要您协助" in text:
                    self._highlight_enter_button()
            except tk.TclError:
                pass
        else:
            print(text, end="")

    def _highlight_enter_button(self):
        """高亮显示模拟回车按钮"""
        enter_btn = self.view.get_component("enter_button")
        if enter_btn and enter_btn.winfo_ismapped():
            enter_btn.configure(fg_color="#ff6b6b", hover_color="#ff4757")
            self.root.after(3000, lambda: enter_btn.configure(
                fg_color=ThemeColors.PRIMARY, hover_color="#3451b2"
            ))

    # ============ 按钮状态控制 ============

    def _disable_execute_button(self):
        execute_btn = self.view.get_component("execute_button")
        if execute_btn and execute_btn.winfo_exists():
            execute_btn.configure(state="disabled", fg_color=ThemeColors.TEXT_DISABLED, text="执行中...")
        self.view.show_enter_button()

    def _enable_execute_button(self):
        execute_btn = self.view.get_component("execute_button")
        if execute_btn and execute_btn.winfo_exists():
            execute_btn.configure(state="normal", fg_color=ThemeColors.PRIMARY, text="▶ 执行命令")
        self.view.hide_enter_button()

    def _disable_terminate_button(self):
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn and terminate_btn.winfo_exists():
            terminate_btn.configure(state="disabled", fg_color=ThemeColors.TEXT_DISABLED)

    def _enable_terminate_button(self):
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn and terminate_btn.winfo_exists():
            terminate_btn.configure(state="normal", fg_color=ThemeColors.DANGER)

    def _reset_button_states(self):
        self._enable_execute_button()
        self._disable_terminate_button()
        self.is_executing = False

    # ============ TTS 相关 ============

    def preload_tts_modules(self):
        """预加载TTS模块"""

        def load_async():
            self.view.show_tts_loading("正在加载TTS语音资源中...")
            success = self.task_manager.preload_tts_modules()
            self.update_tts_indicator(success)
            if success:
                self._synthesize_welcome_message()
            else:
                self.view.hide_tts_loading()

        threading.Thread(target=load_async, daemon=True).start()

    def _synthesize_welcome_message(self):
        """启动时合成欢迎语（自动降级）"""
        try:
            tts = self.task_manager.tts_manager

            for model_type, db_key in [("gpt", "gpt"), ("sovits", "sovits"), ("audio", "audio")]:
                if not tts.get_current_model(model_type) and tts.tts_files_database[db_key]:
                    tts.set_current_model(model_type, list(tts.tts_files_database[db_key].keys())[0])

            if tts.get_current_model("audio") and not tts.get_current_model("text"):
                audio_name = os.path.splitext(os.path.basename(tts.get_current_model("audio")))[0]
                txt_file = f"{audio_name}.txt"
                if txt_file in tts.tts_files_database["text"]:
                    tts.set_current_model("text", txt_file)

            if not tts.get_current_model("text") and tts.tts_files_database["text"]:
                tts.set_current_model("text", list(tts.tts_files_database["text"].keys())[0])

            if not all([tts.get_current_model(t) for t in ["gpt", "sovits", "audio", "text"]]):
                self.view.hide_tts_loading()
                return

            self.view.show_tts_loading("正在合成欢迎语...")
            tts.speak_text_intelligently("你好，我是小芸，很高兴为您服务")
            self._wait_audio_then_hide()
        except Exception:
            self.view.hide_tts_loading()

    def _wait_audio_then_hide(self):
        """等待欢迎语音频播放完成后隐藏加载遮罩"""
        def check_audio():
            try:
                import time
                time.sleep(2)
                tts = self.task_manager.tts_manager
                for _ in range(30):
                    if not tts.is_playing_audio and not tts.is_tts_synthesizing:
                        self.root.after(0, self.view.hide_tts_loading)
                        return
                    time.sleep(0.5)
                self.root.after(0, self.view.hide_tts_loading())
            except Exception:
                self.root.after(0, self.view.hide_tts_loading)
        threading.Thread(target=check_audio, daemon=True).start()

    def update_tts_indicator(self, enabled):
        """更新TTS状态指示器"""
        self.root.after(0, lambda: self._update_tts_indicator_gui(enabled))

    def _update_tts_indicator_gui(self, enabled):
        tts_indicator = self.view.get_component("tts_indicator")
        if tts_indicator:
            if enabled:
                tts_indicator.configure(text="● TTS: 开启", text_color=ThemeColors.SUCCESS)
            else:
                tts_indicator.configure(text="● TTS: 关闭", text_color=ThemeColors.WARNING)

    # ============ 辅助方法 ============

    def _show_history_command(self):
        """显示历史记录命令"""
        history = self.task_manager.file_manager.safe_read_json_file(
            "conversation_history.json", {"sessions": [], "free_chats": []}
        )
        self._append_output(f"📚 对话历史")
        sessions = history.get("sessions", [])
        if sessions:
            self._append_output(f"📱 聊天会话 ({len(sessions)}条):")
            for i, session in enumerate(sessions[-5:], 1):
                self._append_output(f"\n{i}. {session.get('timestamp', '未知时间')}")
                self._append_output(
                    f"   目标: {session.get('target_app', '未知')} -> {session.get('target_object', '未知')}")
                self._append_output(f"   回复: {session.get('reply_generated', '')}")
        free_chats = history.get("free_chats", [])
        if free_chats:
            self._append_output(f"💬 自由聊天 ({len(free_chats)}条):\n")
            for i, chat in enumerate(free_chats[-5:], 1):
                self._append_output(f"{i}. {chat.get('timestamp', '未知时间')}")
                self._append_output(f"   用户: {chat.get('user_input', '')}")
                self._append_output(f"   回复: {chat.get('assistant_reply', '')}")
        if not sessions and not free_chats:
            self._append_output(f"暂无对话历史")

    def _clear_history_command(self):
        """清空历史记录命令"""
        try:
            if os.path.exists("conversation_history.json"):
                os.remove("conversation_history.json")
                self._append_output(f"✅ 对话历史已清空")
                with open("conversation_history.json", 'w', encoding='utf-8') as f:
                    import json
                    json.dump({"sessions": [], "free_chats": []}, f, ensure_ascii=False, indent=2)
            else:
                self._append_output(f"⚠️  没有对话历史文件")
        except Exception as e:
            self._append_output(f"❌ 清空历史失败：{e}")

    def _cleanup_active_threads(self):
        self.active_threads = [t for t in self.active_threads if t.is_alive()]

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
                self.root, text=message, font=("Microsoft YaHei", 12),
                text_color=ThemeColors.TEXT_PRIMARY, fg_color=colors[type],
                corner_radius=8
            )
            toast.place(relx=0.5, rely=0.9, anchor="center")

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

    def cleanup_on_exit(self):
        """退出时清理所有资源"""
        print("🧹 正在清理资源...")
        self.task_manager.stop_audio_playback()
        for process in self.active_subprocesses:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=2)
            except:
                pass
        for thread in self.active_threads:
            if thread.is_alive(): thread.join(timeout=1)
        self.task_manager.cleanup()

    # ============ 初始连接检查 ============

    def check_initial_connection(self):
        """检查初始连接"""
        self.task_manager.check_initial_connection()
        self.connection_handler._update_connection_status_gui(self.task_manager.is_connected)
        self._sync_device_to_task_chain()


    def on_closing(self):
        """窗口关闭事件"""
        self.cleanup_on_exit()
        self.root.quit()

    # ============ 主题切换 ============

    def toggle_theme(self):
        """切换深色/浅色主题"""
        import customtkinter as ctk
        from yuntai.views.theme import DarkThemeColors, ThemeColors
        import tkinter as tk

        current_mode = ctk.get_appearance_mode().lower()
        new_mode = "dark" if current_mode == "light" else "light"

        ctk.set_appearance_mode(new_mode)

        # 获取新主题颜色
        new_colors = DarkThemeColors if new_mode == "dark" else ThemeColors

        def update_widget(widget, depth=0):
            """递归更新所有部件的颜色"""
            if depth > 10:  # 防止无限递归
                return

            try:
                widget_type = type(widget).__name__

                # CTkFrame - 卡片框架
                if isinstance(widget, ctk.CTkFrame):
                    # 检查是否是主要框架
                    if widget in [self.view.nav_frame, self.view.components.get("nav_frame")]:
                        widget.configure(fg_color=new_colors.BG_NAV)
                    elif widget == self.view.components.get("main_container"):
                        widget.configure(fg_color=new_colors.BG_MAIN)
                    elif widget == self.view.components.get("status_bar"):
                        widget.configure(fg_color=new_colors.BG_NAV, border_color=new_colors.BORDER_LIGHT)
                    else:
                        # 根据当前颜色判断应该使用什么新颜色
                        try:
                            current_fg = widget.cget("fg_color")
                            current_border = widget.cget("border_width")
                            
                            if current_fg and current_fg != "transparent":
                                # 检查是否是卡片样式（有边框）
                                if current_border > 0:
                                    # 检查当前颜色类型以保持颜色类型一致
                                    if current_fg in [ThemeColors.BG_CARD_ALT, DarkThemeColors.BG_CARD_ALT]:
                                        widget.configure(fg_color=new_colors.BG_CARD_ALT, border_color=new_colors.BORDER_LIGHT)
                                    elif current_fg in [ThemeColors.BG_HOVER, DarkThemeColors.BG_HOVER]:
                                        widget.configure(fg_color=new_colors.BG_HOVER, border_color=new_colors.BORDER_LIGHT)
                                    elif current_fg in [ThemeColors.BG_INPUT, DarkThemeColors.BG_INPUT]:
                                        widget.configure(fg_color=new_colors.BG_INPUT, border_color=new_colors.BORDER_LIGHT)
                                    else:
                                        widget.configure(fg_color=new_colors.BG_CARD, border_color=new_colors.BORDER_LIGHT)
                                else:
                                    # 无边框框架
                                    if current_fg in [ThemeColors.BG_CARD, DarkThemeColors.BG_CARD]:
                                        widget.configure(fg_color=new_colors.BG_CARD)
                                    elif current_fg in [ThemeColors.BG_CARD_ALT, DarkThemeColors.BG_CARD_ALT]:
                                        widget.configure(fg_color=new_colors.BG_CARD_ALT)
                                    elif current_fg in [ThemeColors.BG_HOVER, DarkThemeColors.BG_HOVER]:
                                        widget.configure(fg_color=new_colors.BG_HOVER)
                                    elif current_fg in [ThemeColors.BG_INPUT, DarkThemeColors.BG_INPUT]:
                                        widget.configure(fg_color=new_colors.BG_INPUT)
                        except:
                            pass

                # CTkButton - 按钮
                elif isinstance(widget, ctk.CTkButton):
                    # 主题切换按钮特殊处理
                    if widget == self.view.components.get("theme_toggle_button"):
                        icon = "☀️" if new_mode == "dark" else "🌙"
                        widget.configure(
                            text=icon,
                            fg_color=new_colors.BG_HOVER,
                            hover_color=new_colors.BG_CARD_ALT,
                            border_color=new_colors.BORDER_LIGHT,
                            text_color=new_colors.TEXT_PRIMARY
                        )
                    else:
                        # 获取当前颜色判断按钮类型
                        try:
                            current_fg = widget.cget("fg_color")
                            if current_fg == ThemeColors.PRIMARY or current_fg == DarkThemeColors.PRIMARY:
                                widget.configure(fg_color=new_colors.PRIMARY, hover_color=new_colors.PRIMARY_HOVER)
                            elif current_fg == ThemeColors.SECONDARY or current_fg == DarkThemeColors.SECONDARY:
                                widget.configure(fg_color=new_colors.SECONDARY, hover_color=new_colors.SECONDARY_HOVER)
                            elif current_fg == ThemeColors.DANGER or current_fg == DarkThemeColors.DANGER:
                                widget.configure(fg_color=new_colors.DANGER, hover_color=new_colors.DANGER_HOVER)
                            elif current_fg == ThemeColors.ACCENT or current_fg == DarkThemeColors.ACCENT:
                                widget.configure(fg_color=new_colors.ACCENT, hover_color=new_colors.ACCENT_HOVER)
                            elif current_fg == ThemeColors.SUCCESS or current_fg == DarkThemeColors.SUCCESS:
                                widget.configure(fg_color=new_colors.SUCCESS, hover_color=new_colors.SUCCESS_HOVER)
                            elif current_fg == ThemeColors.WARNING or current_fg == DarkThemeColors.WARNING:
                                widget.configure(fg_color=new_colors.WARNING, hover_color=new_colors.WARNING_HOVER)
                            elif "BG_HOVER" in str(current_fg):
                                widget.configure(fg_color=new_colors.BG_HOVER, text_color=new_colors.TEXT_PRIMARY)
                            else:
                                # 默认按钮样式
                                widget.configure(text_color=new_colors.TEXT_PRIMARY)
                        except:
                            widget.configure(text_color=new_colors.TEXT_PRIMARY)

                # CTkTextbox - 文本框
                elif isinstance(widget, ctk.CTkTextbox):
                    widget.configure(
                        fg_color=new_colors.BG_CARD_ALT,
                        text_color=new_colors.TEXT_PRIMARY,
                        border_color=new_colors.BORDER_LIGHT
                    )

                # CTkScrollableFrame - 可滚动框架
                elif isinstance(widget, ctk.CTkScrollableFrame):
                    widget.configure(
                        fg_color="transparent",
                        scrollbar_button_color=new_colors.BG_HOVER,
                        scrollbar_button_hover_color=new_colors.PRIMARY
                    )

                # CTkLabel - 标签
                elif isinstance(widget, ctk.CTkLabel):
                    text = str(widget.cget("text"))
                    # 状态指示器
                    if any(keyword in text for keyword in ["已连接", "●", "未连接"]):
                        if "未连接" in text:
                            widget.configure(text_color=new_colors.DANGER)
                        else:
                            widget.configure(text_color=new_colors.SUCCESS)
                    elif ": " in text and any(keyword in text for keyword in ["TTS", "开启", "关闭", "ON", "OFF"]):
                        if "开启" in text or "ON" in text:
                            widget.configure(text_color=new_colors.SUCCESS)
                        else:
                            widget.configure(text_color=new_colors.WARNING)
                    else:
                        # 普通标签
                        try:
                            current_color = widget.cget("text_color")
                            if current_color in [ThemeColors.TEXT_PRIMARY, DarkThemeColors.TEXT_PRIMARY, ThemeColors.TEXT_SECONDARY, DarkThemeColors.TEXT_SECONDARY, ThemeColors.TEXT_DISABLED, DarkThemeColors.TEXT_DISABLED]:
                                # 根据原始颜色映射到新颜色
                                if current_color in [ThemeColors.TEXT_SECONDARY, DarkThemeColors.TEXT_SECONDARY]:
                                    widget.configure(text_color=new_colors.TEXT_SECONDARY)
                                elif current_color in [ThemeColors.TEXT_DISABLED, DarkThemeColors.TEXT_DISABLED]:
                                    widget.configure(text_color=new_colors.TEXT_DISABLED)
                                else:
                                    widget.configure(text_color=new_colors.TEXT_PRIMARY)
                        except:
                            widget.configure(text_color=new_colors.TEXT_PRIMARY)

                # CTkEntry - 输入框
                elif isinstance(widget, ctk.CTkEntry):
                    widget.configure(
                        fg_color=new_colors.BG_INPUT,
                        text_color=new_colors.TEXT_PRIMARY,
                        border_color=new_colors.BORDER_MEDIUM
                    )

                # CTkOptionMenu - 下拉菜单
                elif isinstance(widget, ctk.CTkOptionMenu):
                    widget.configure(
                        fg_color=new_colors.BG_INPUT,
                        button_color=new_colors.OPTION_BUTTON_COLOR,
                        button_hover_color=new_colors.OPTION_BUTTON_HOVER,
                        text_color=new_colors.TEXT_PRIMARY
                    )

                # CTkRadioButton - 单选按钮
                elif isinstance(widget, ctk.CTkRadioButton):
                    widget.configure(
                        fg_color=new_colors.PRIMARY,
                        hover_color=new_colors.PRIMARY_HOVER,
                        text_color=new_colors.TEXT_PRIMARY
                    )

                # CTkCheckBox - 复选框
                elif isinstance(widget, ctk.CTkCheckBox):
                    widget.configure(
                        fg_color=new_colors.PRIMARY,
                        hover_color=new_colors.PRIMARY_HOVER,
                        text_color=new_colors.TEXT_PRIMARY
                    )

                # CTkProgressBar - 进度条
                elif isinstance(widget, ctk.CTkProgressBar):
                    widget.configure(
                        fg_color=new_colors.BG_CARD_ALT,
                        progress_color=new_colors.PRIMARY
                    )

                # CTkSlider - 滑块
                elif isinstance(widget, ctk.CTkSlider):
                    widget.configure(
                        fg_color=new_colors.BG_CARD_ALT,
                        button_color=new_colors.PRIMARY,
                        button_hover_color=new_colors.PRIMARY_HOVER
                    )

                # CTkSwitch - 开关
                elif isinstance(widget, ctk.CTkSwitch):
                    widget.configure(
                        fg_color=new_colors.BG_CARD_ALT,
                        progress_color=new_colors.PRIMARY,
                        button_color=new_colors.PRIMARY,
                        button_hover_color=new_colors.PRIMARY_HOVER,
                        text_color=new_colors.TEXT_PRIMARY
                    )

                # CTkSegmentedButton - 分段按钮
                elif isinstance(widget, ctk.CTkSegmentedButton):
                    widget.configure(
                        fg_color=new_colors.BG_CARD_ALT,
                        selected_color=new_colors.PRIMARY,
                        selected_hover_color=new_colors.PRIMARY_HOVER,
                        unselected_color=new_colors.BG_CARD,
                        unselected_hover_color=new_colors.BG_HOVER,
                        text_color=new_colors.TEXT_PRIMARY
                    )

                # CTkTabview - 标签页
                elif isinstance(widget, ctk.CTkTabview):
                    widget.configure(
                        fg_color=new_colors.BG_CARD,
                        segmented_button_fg_color=new_colors.BG_CARD_ALT,
                        segmented_button_selected_color=new_colors.PRIMARY,
                        segmented_button_selected_hover_color=new_colors.PRIMARY_HOVER,
                        segmented_button_unselected_color=new_colors.BG_CARD,
                        segmented_button_unselected_hover_color=new_colors.BG_HOVER
                    )

            except Exception as e:
                # 忽略更新失败的部件
                pass

            # 处理 tkinter 原生控件（非 customtkinter）
            try:
                widget_type = type(widget).__name__
                
                # tkinter.Listbox - 列表框（如TTS历史音频列表）
                if widget_type == "Listbox":
                    widget.configure(
                        bg=new_colors.BG_CARD_ALT,
                        fg=new_colors.TEXT_PRIMARY,
                        selectbackground=new_colors.PRIMARY,
                        selectforeground=new_colors.TEXT_LIGHT,
                        highlightcolor=new_colors.BORDER_MEDIUM,
                        highlightbackground=new_colors.BORDER_MEDIUM
                    )
            except Exception as e:
                # 忽略更新失败的部件
                pass

            # 递归处理子部件
            try:
                children = widget.winfo_children()
                for child in children:
                    update_widget(child, depth + 1)
            except:
                pass

        # 从根窗口开始递归更新
        try:
            update_widget(self.root)
        except Exception as e:
            print(f"主题更新警告: {e}")

        # 遍历所有已创建的页面（包括未显示的）- 确保先临时显示再更新主题
        try:
            if hasattr(self.view, 'content_pages'):
                current_page = self.view.current_page_index
                for i, page in enumerate(self.view.content_pages):
                    if page and page.winfo_exists():
                        # 临时显示页面以确保widget树完整
                        if i != current_page:
                            page.pack(fill="both", expand=True)
                        # 更新页面主题
                        update_widget(page)
                        # 恢复隐藏状态
                        if i != current_page:
                            page.pack_forget()
        except Exception as e:
            print(f"页面更新警告: {e}")

        # 通过components字典更新所有已注册的组件
        for name, component in self.view.components.items():
            if component is None:
                continue
            try:
                if isinstance(component, ctk.CTkFrame):
                    # 更新已注册的框架
                    if 'card' in name.lower() or 'frame' in name.lower():
                        try:
                            border_width = component.cget("border_width")
                            if border_width > 0:
                                component.configure(fg_color=new_colors.BG_CARD, border_color=new_colors.BORDER_LIGHT)
                            elif name in ['usb_frame', 'wireless_frame']:
                                component.configure(fg_color=new_colors.BG_CARD_ALT)
                        except:
                            pass
                elif isinstance(component, ctk.CTkButton) and 'shortcut' in name:
                    # 更新快捷键按钮
                    component.configure(fg_color=new_colors.BG_HOVER, text_color=new_colors.TEXT_PRIMARY)
                elif isinstance(component, ctk.CTkScrollableFrame) and 'files' in name:
                    # 更新文件列表滚动框
                    component.configure(
                        fg_color="transparent",
                        scrollbar_button_color=new_colors.BG_HOVER,
                        scrollbar_button_hover_color=new_colors.PRIMARY
                    )

                # 更新文件列表中的动态组件
                files_scroll_frame = self.view.get_component("files_list_scroll_frame")
                if files_scroll_frame and hasattr(files_scroll_frame, 'winfo_children'):
                    for child in files_scroll_frame.winfo_children():
                        try:
                            child_type = type(child).__name__
                            if child_type == 'CTkFrame':
                                child.configure(fg_color=new_colors.BG_HOVER)
                            elif child_type == 'CTkLabel':
                                child.configure(text_color=new_colors.TEXT_PRIMARY)
                            elif child_type == 'CTkButton':
                                if '清空' in str(child.cget("text")):
                                    child.configure(fg_color=new_colors.WARNING, hover_color=new_colors.WARNING_HOVER, text_color=new_colors.TEXT_LIGHT)
                                else:
                                    child.configure(fg_color=new_colors.DANGER, hover_color=new_colors.DANGER_HOVER, text_color=new_colors.TEXT_LIGHT)
                        except:
                            continue

                # 更新TTS页面的scrolledtext和Listbox
                tts_log_text = self.view.get_component("tts_log_text")
                if tts_log_text and tts_log_text.winfo_exists():
                    try:
                        tts_log_text.configure(fg_color=new_colors.BG_CARD_ALT, text_color=new_colors.TEXT_PRIMARY, border_color=new_colors.BORDER_LIGHT)
                    except:
                        pass

                tts_audio_listbox = self.view.get_component("tts_audio_listbox")
                if tts_audio_listbox and tts_audio_listbox.winfo_exists():
                    try:
                        tts_audio_listbox.configure(bg=new_colors.BG_CARD_ALT, fg=new_colors.TEXT_PRIMARY)
                    except:
                        pass

                # 更新CTkOptionMenu按钮颜色（用于区分下拉按钮和背景）
                for name in self.view.components:
                    component = self.view.components[name]
                    if isinstance(component, ctk.CTkOptionMenu):
                        component.configure(
                            fg_color=new_colors.BG_INPUT,
                            button_color=new_colors.OPTION_BUTTON_COLOR,
                            button_hover_color=new_colors.OPTION_BUTTON_HOVER,
                            text_color=new_colors.TEXT_PRIMARY
                        )

            except Exception as e:
                continue

        # 更新导航按钮高亮
        try:
            self.view._highlight_nav_button(self.view.current_page_index)
        except:
            pass

        # 显示提示
        theme_name = "深色主题" if new_mode == "dark" else "浅色主题"
        self.show_toast(f"已切换到{theme_name}", "info")

    # ============ 快捷键处理 ============

    def execute_shortcut(self, shortcut_key):
        """执行快捷键对应的应用打开命令"""
        # 从 SHORTCUTS 获取完整的命令
        from yuntai.core.config import SHORTCUTS
        command = SHORTCUTS.get(shortcut_key, "")
        if not command:
            return

        command_input = self.view.get_component("command_input")
        if command_input:
            command_input.delete("1.0", tk.END)
            command_input.insert("1.0", command)
            self.execute_command()
            app_name = command.replace("打开", "")
            self.show_toast(f"正在打开{app_name}", "info")

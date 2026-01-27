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
from yuntai.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE
)
# 引用 TaskManager
from yuntai.task_manager import TaskManager
# 引用 Handlers
from .handlers import ConnectionHandler, TTSHandler, DynamicHandler, SystemHandler

# 使用新的统一配置
from .config import SCRCPY_PATH, validate_config, print_config_summary, ZHIPU_CHAT_MODEL, ZHIPU_MODEL, \
    ZHIPU_API_BASE_URL
from .gui_view import GUIView, ThemeColors
from .output_capture import SimpleOutputCapture


class GUIController:
    """GUI控制器 - 处理所有用户事件和业务逻辑"""

    def __init__(self, root, project_root, scrcpy_path):
        self.root = root
        self.project_root = project_root
        self.scrcpy_path = SCRCPY_PATH

        # 初始化视图
        self.view = GUIView(root)

        # 初始化任务管理器
        self.task_manager = TaskManager(project_root, self.scrcpy_path)

        # 初始化输出捕获器
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
            command_input.bind("<Return>", lambda _: self.execute_command())

        enter_btn = self.view.get_component("enter_button")
        if enter_btn:
            enter_btn.configure(command=self.simulate_enter)

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
            from .multimodal_processor import MultimodalProcessor
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
        if not self.attached_files: return

        file_count = len(self.attached_files)
        self.attached_files.clear()
        if self.view:
            self.view.show_attached_files(self.attached_files, self)
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
        command = command_input.get().strip()
        has_attachments = len(self.attached_files) > 0

        if not command and not has_attachments:
            self.show_toast("请输入命令或选择文件", "warning")
            return

        command_input.delete(0, tk.END)
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

                print(f"\n{'=' * 180}\n")
                if has_attachments:
                    print(f"\n📋 多模态指令: {command if command else '[无文本]'}")
                    print(f"📎 附件数量: {len(self.attached_files)} 个文件\n")
                else:
                    print(f"\n📋 指令: {command}\n")

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
                    self._append_output(f"📱 可用设备列表:\n")
                    if devices:
                        for i, device in enumerate(devices, 1):
                            self._append_output(f"  {i}. {device}\n")
                    else:
                        self._append_output(f"  未找到可用设备\n")
                    return

                if not has_attachments and not self.task_manager.is_connected:
                    task_info = self.task_manager.task_recognizer.recognize_task_intent(command)
                    task_type = task_info.get("task_type", "free_chat")
                    if task_type != "free_chat":
                        self._append_output(f"❌ 设备未连接，请先连接设备\n")
                        return

                result = None
                if has_attachments:
                    result = self._handle_multimodal_chat(command, self.attached_files)
                else:
                    result = self.task_manager.dispatch_task(
                        command, self.task_manager.task_args, self.task_manager.device_id
                    )

                # 持续回复处理
                if result and isinstance(result, str) and "🔄CONTINUOUS_REPLY:" in result:
                    try:
                        parts = result.replace("🔄CONTINUOUS_REPLY:", "").split(":")
                        if len(parts) == 2:
                            target_app, target_object = parts
                            if not self.task_manager.is_connected:
                                self._append_output(f"❌ 设备未连接，无法启动持续回复\n")
                                return
                            self._append_output(f"🚀 检测到持续回复模式: {target_app} -> {target_object}\n")
                            self.start_continuous_reply_thread(
                                self.task_manager.task_args, target_app, target_object, self.task_manager.device_id
                            )
                            print("\n🔄 持续回复模式已启动，保持按钮状态")
                            return
                    except Exception as e:
                        print(f"❌ 解析持续回复标记失败: {e}")
                        result = f"❌ 解析持续回复参数失败: {str(e)}"

                if result:
                    self._append_output(f"\n🎉 结果：{result}\n")

                if "持续回复模式" in str(result) or "continuous_reply" in str(result).lower():
                    print(f"🔄 检测到持续回复模式，保持按钮状态")
                    return

            except Exception as e:
                self._append_output(f"\n❌ 错误：{str(e)}\n")
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
        print(f"\n📋 文本: {text}")
        print(f"\n📎 附件: {len(file_paths)} 个文件")

        try:
            if not file_paths or len(file_paths) == 0:
                return self.task_manager._handle_free_chat(text)

            valid_files = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    valid_files.append(file_path)
                else:
                    print(f"⚠️  文件不存在: {file_path}")

            if len(valid_files) == 0:
                return self.task_manager._handle_free_chat(text)

            if not self.multimodal_processor:
                from .multimodal_processor import MultimodalProcessor
                self.multimodal_processor = MultimodalProcessor()

            history = self._get_chat_history_for_multimodal()

            success, response, audio_result = self.multimodal_processor.process_with_files(
                text=text, file_paths=valid_files, history=history,
                temperature=0.7, max_tokens=2000
            )

            if success:
                print(f"\n✅ 多模态分析完成")
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
            from .config import CONVERSATION_HISTORY_FILE
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
        print("\n" + "=" * 180 + "\n")
        print("🛑 正在发送终止信号...")
        self._cleanup_active_threads()
        if not self.active_threads and not self.is_continuous_mode:
            self.show_toast("没有正在执行的操作", "info")
            return

        self.terminating.set()
        self.terminate_flag.set()
        self._disable_terminate_button()

        if self.is_continuous_mode:
            self._append_output(f"\n🛑 正在终止持续回复模式...\n")
        else:
            self._append_output(f"\n🛑 正在终止当前任务...\n")
        self.show_toast("已发送终止信号", "warning")

    def simulate_enter(self):
        """模拟回车键效果"""
        print("\n[用户点击模拟回车按钮]")
        try:
            from yuntai.agent_executor import AgentExecutor
            AgentExecutor.user_confirm()
        except Exception as e:
            print(f"\n⚠️  发送确认信号失败: {e}")

        output_text = self.view.get_component("output_text")
        if output_text:
            try:
                output_text.configure(state="normal")
                output_text.insert("end", "\n[用户已确认]\n")
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
            print(f"📱 设备类型已切换为: {device_type}")

        self.view._device_type_callback = on_device_type_change

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
                print(f"\n🚀 持续回复线程启动: {target_app} -> {target_object}")
                from .agent_core import TerminableContinuousReplyManager
                manager = TerminableContinuousReplyManager(
                    args, target_app, target_object, device_id,
                    self.task_manager.zhipu_client, self.task_manager.file_manager,
                    terminate_flag=self.terminate_flag
                )
                success = manager.run_continuous_loop()
                if success:
                    print(f"\n✅ 持续回复完成")
                else:
                    print(f"\n⏹️  持续回复已终止")
            except Exception as e:
                print(f"\n❌ 持续回复错误：{str(e)}\n")
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
            execute_btn.configure(state="normal", fg_color=ThemeColors.PRIMARY, text="执行命令")
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
            success = self.task_manager.preload_tts_modules()
            self.update_tts_indicator(success)

        threading.Thread(target=load_async, daemon=True).start()

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
        self._append_output(f"\n📚 对话历史\n")
        sessions = history.get("sessions", [])
        if sessions:
            self._append_output(f"📱 聊天会话 ({len(sessions)}条):\n")
            for i, session in enumerate(sessions[-5:], 1):
                self._append_output(f"\n{i}. {session.get('timestamp', '未知时间')}\n")
                self._append_output(
                    f"   目标: {session.get('target_app', '未知')} -> {session.get('target_object', '未知')}\n")
                self._append_output(f"   回复: {session.get('reply_generated', '')}\n")
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
            if os.path.exists("conversation_history.json"):
                os.remove("conversation_history.json")
                self._append_output(f"✅ 对话历史已清空\n")
                with open("conversation_history.json", 'w', encoding='utf-8') as f:
                    import json
                    json.dump({"sessions": [], "free_chats": []}, f, ensure_ascii=False, indent=2)
            else:
                self._append_output(f"⚠️  没有对话历史文件\n")
        except Exception as e:
            self._append_output(f"❌ 清空历史失败：{e}\n")

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


    def on_closing(self):
        """窗口关闭事件"""
        self.cleanup_on_exit()
        self.root.quit()

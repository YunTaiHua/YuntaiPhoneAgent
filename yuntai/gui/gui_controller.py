"""
GUIController - 事件处理和业务逻辑模块 (PyQt6 重构版)
负责处理用户操作，连接UI和后台任务，并协调各个Handler
支持 LangChain Callbacks 实现流式输出
"""

import sys
import os
import threading
import queue
import time
import datetime
import traceback
from typing import Optional, Dict, Any, Callable, List

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject

# 第三方库
from zhipuai import ZhipuAI

# 项目模块
from yuntai.core.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE, SCRCPY_PATH, validate_config, print_config_summary,
    ZHIPU_CHAT_MODEL, ZHIPU_MODEL, ZHIPU_API_BASE_URL
)

# 引用 TaskManager（保留用于连接管理和TTS）
from yuntai.services.task_manager import TaskManager
# 引用新的 TaskChain
from yuntai.chains import TaskChain, ReplyChain
from yuntai.agents import JudgementAgent
# 引用 Handlers
from yuntai.handlers import ConnectionHandler, TTSHandler, DynamicHandler, SystemHandler

# PyQt6 GUI
from yuntai.gui.gui_view import GUIView
from yuntai.gui.styles import ThemeColors
from yuntai.gui.output_capture import SimpleOutputCapture

# LangChain Callbacks
from yuntai.callbacks import (
    get_callback_manager,
    QtStreamingCallbackHandler,
    LoggingCallbackHandler,
    PerformanceCallbackHandler
)


class GUIController(QObject):
    """GUI控制器 - 处理所有用户事件和业务逻辑，支持流式输出"""

    # 定义信号用于线程安全的UI更新
    _output_signal = pyqtSignal(str)
    _hide_tts_loading_signal = pyqtSignal()
    _show_enter_button_signal = pyqtSignal()
    _hide_enter_button_signal = pyqtSignal()
    _show_tts_loading_signal = pyqtSignal(str)
    _update_tts_indicator_signal = pyqtSignal(bool)
    # 新增信号用于替代QTimer.singleShot
    _enable_execute_button_signal = pyqtSignal()
    _disable_execute_button_signal = pyqtSignal()
    _enable_terminate_button_signal = pyqtSignal()
    _disable_terminate_button_signal = pyqtSignal()
    _reset_button_states_signal = pyqtSignal()
    _clear_attached_files_signal = pyqtSignal()
    # 流式输出信号
    _streaming_output_signal = pyqtSignal(str)
    _streaming_complete_signal = pyqtSignal(str)

    def __init__(self, project_root, scrcpy_path):
        super().__init__()
        self.project_root = project_root
        self.scrcpy_path = SCRCPY_PATH

        # 创建QApplication实例（如果不存在）
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        # 初始化视图
        self.view = GUIView()

        # 连接输出信号到槽函数
        self._output_signal.connect(self._do_append_output_from_signal)
        self._hide_tts_loading_signal.connect(self.view.hide_tts_loading)
        self._show_enter_button_signal.connect(self.view.show_enter_button)
        self._hide_enter_button_signal.connect(self.view.hide_enter_button)
        self._show_tts_loading_signal.connect(self.view.show_tts_loading)
        self._update_tts_indicator_signal.connect(self.update_tts_indicator)
        # 连接新增信号
        self._enable_execute_button_signal.connect(self._do_enable_execute_button)
        self._disable_execute_button_signal.connect(self._do_disable_execute_button)
        self._enable_terminate_button_signal.connect(self._do_enable_terminate_button)
        self._disable_terminate_button_signal.connect(self._do_disable_terminate_button)
        self._reset_button_states_signal.connect(self._do_reset_button_states)
        self._clear_attached_files_signal.connect(self._do_clear_attached_files)
        # 连接流式输出信号
        self._streaming_output_signal.connect(self._do_append_output_from_signal)
        self._streaming_complete_signal.connect(self._on_streaming_complete)

        # 初始化任务管理器（保留用于连接管理和TTS）
        self.task_manager = TaskManager(project_root, self.scrcpy_path)

        # 初始化回调管理器
        self.callback_manager = get_callback_manager()
        self._setup_callbacks()

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

        # 启动消息处理定时器
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.process_messages)
        self.message_timer.start(100)

        # 设置窗口关闭事件
        self.view.closeEvent = self.on_closing

        # 延迟预加载TTS模块
        QTimer.singleShot(1000, self.preload_tts_modules)

        # 文件上传相关
        self.attached_files = []
        self.multimodal_processor = None

        # 设置设备类型变化回调
        self._setup_device_type_callback()

    def _setup_callbacks(self):
        """设置 LangChain Callbacks"""
        # 创建 Qt 流式输出处理器
        self.streaming_handler = QtStreamingCallbackHandler(
            append_signal=self._streaming_output_signal,
            complete_signal=self._streaming_complete_signal,
            enable_typewriter=True
        )
        
        # 注册流式输出处理器
        self.callback_manager.register_handler(
            name="gui_streaming",
            handler=self.streaming_handler,
            is_global=True
        )
        
        # 创建日志处理器（默认只写入文件，不输出到控制台）
        self.logging_handler = LoggingCallbackHandler(
            enable_console=False,  # 不输出到控制台
            enable_detailed=True   # 记录详细信息到文件
        )
        
        # 注册日志处理器
        self.callback_manager.register_handler(
            name="gui_logging",
            handler=self.logging_handler,
            is_global=True
        )
        
        # 创建性能监控处理器
        self.performance_handler = PerformanceCallbackHandler(
            enable_console=False,
            enable_detailed=False
        )
        
        # 注册性能处理器
        self.callback_manager.register_handler(
            name="gui_performance",
            handler=self.performance_handler,
            is_global=True
        )
    
    def _on_streaming_complete(self, response: str):
        """流式输出完成回调"""
        # 可以在这里添加完成后的处理逻辑
        pass
    
    def get_callbacks(self) -> List:
        """获取 GUI 控制器的回调处理器列表"""
        return self.callback_manager.get_callbacks(include_global=True)

    def _bind_ui_events(self):
        """绑定所有UI事件（主要是导航和主控台）"""
        # 导航按钮点击事件
        nav_buttons = self.view.get_component("nav_buttons")
        if nav_buttons:
            nav_commands = [
                (0, self.show_dashboard),
                (1, self.connection_handler.show_panel),
                (2, self.tts_handler.show_panel),
                (3, self.system_handler.show_history_panel),
                (4, self.dynamic_handler.show_panel),
                (5, self.system_handler.show_settings_panel),
            ]

            for index, command in nav_commands:
                if index < len(nav_buttons):
                    btn = nav_buttons[index]
                    if btn:
                        btn.clicked.connect(command)

        # 绑定控制台页面事件
        self._bind_dashboard_events()

    def _bind_dashboard_events(self):
        """绑定控制台页面事件"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            try:
                execute_btn.clicked.disconnect()
            except:
                pass
            execute_btn.clicked.connect(self.execute_command)

        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            try:
                terminate_btn.clicked.disconnect()
            except:
                pass
            terminate_btn.clicked.connect(self.terminate_operation)

        # TTS设置按钮（调用TTS Handler的弹窗）
        tts_btn = self.view.get_component("tts_button")
        if tts_btn:
            try:
                tts_btn.clicked.disconnect()
            except:
                pass
            tts_btn.clicked.connect(self.tts_handler.show_tts_settings_popup)

        clear_btn = self.view.get_component("clear_output_btn")
        if clear_btn:
            try:
                clear_btn.clicked.disconnect()
            except:
                pass
            clear_btn.clicked.connect(self.clear_output)

        scrcpy_btn = self.view.get_component("scrcpy_button")
        if scrcpy_btn:
            scrcpy_btn.clicked.connect(self.connection_handler.show_scrcpy_popup)

        scrcpy_btn = self.view.get_component("scrcpy_button")
        if scrcpy_btn:
            try:
                scrcpy_btn.clicked.disconnect()
            except:
                pass
            scrcpy_btn.clicked.connect(self.connection_handler.show_scrcpy_popup)

        enter_btn = self.view.get_component("enter_button")
        if enter_btn:
            try:
                enter_btn.clicked.disconnect()
            except:
                pass
            enter_btn.clicked.connect(self.simulate_enter)

        # 绑定主题切换按钮
        theme_toggle_btn = self.view.get_component("theme_toggle_button")
        if theme_toggle_btn:
            try:
                theme_toggle_btn.clicked.disconnect()
            except:
                pass
            theme_toggle_btn.clicked.connect(self.toggle_theme)

        # 绑定文件管理上传按钮
        file_upload_btn = self.view.get_component("file_upload_button")
        if file_upload_btn:
            try:
                file_upload_btn.clicked.disconnect()
            except:
                pass
            file_upload_btn.clicked.connect(self.show_file_upload)

        # 绑定快捷键按钮
        for key, app_name in SHORTCUTS.items():
            shortcut_btn = self.view.get_component(f"shortcut_btn_{key}")
            if shortcut_btn:
                try:
                    shortcut_btn.clicked.disconnect()
                except:
                    pass
                shortcut_btn.clicked.connect(lambda checked, k=key: self.execute_shortcut(k))

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
        if not command_input:
            return
        command = command_input.toPlainText().strip()
        has_attachments = len(self.attached_files) > 0

        if not command and not has_attachments:
            self.show_toast("请输入命令或选择文件", "warning")
            return

        command_input.clear()
        command_input.setFixedHeight(42)
        if self.terminate_flag.is_set():
            self.terminate_flag.clear()

        output_text = self.view.get_component("output_text")
        if output_text:
            if not self.output_capture:
                self.output_capture = SimpleOutputCapture(output_text, self.view.is_dark_theme)
            elif self.output_capture.text_widget != output_text:
                self.output_capture.set_text_widget(output_text)

        self.is_executing = True
        self._disable_execute_button()
        self._enable_terminate_button()

        def run_command():
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'═' * 9} [{timestamp} 对话开始] {'═' * 9}\n")
                if has_attachments:
                    print(f"💭 多模态指令: {command if command else '[无文本]'}")
                    print(f"📌 附件数量: {len(self.attached_files)} 个文件")
                else:
                    print(f"💭 指令: {command}")

                if not has_attachments and not self.task_manager.is_connected:
                    task_result = self.judgement_agent.judge(command)
                    task_type = task_result.task_type
                    if task_type != "free_chat":
                        print(f"❌ 设备未连接，请先连接设备")
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
                                print(f"❌ 设备未连接，无法启动持续回复")
                                return
                            self.start_continuous_reply_thread(
                                self.task_manager.task_args, target_app, target_object, self.task_manager.device_id
                            )
                            return
                    except Exception as e:
                        print(f"❌ 解析持续回复标记失败: {e}")
                        result = f"❌ 解析持续回复参数失败: {str(e)}"

                if result:
                    print(f"🎉 结果：{result}")

                if "持续回复模式" in str(result) or "continuous_reply" in str(result).lower():
                    print(f"🔄 检测到持续回复模式，保持按钮状态")
                    return

            except Exception as e:
                print(f"❌ 错误：{str(e)}")
                traceback.print_exc()
            finally:
                # 使用信号槽清理附件文件
                QTimer.singleShot(100, self._clear_attached_files_signal.emit)

                if not self.is_continuous_mode:
                    self.message_queue.put(("success", "命令执行完成"))
                    self._enable_execute_button_signal.emit()
                    self._disable_terminate_button_signal.emit()
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
                return "没有可处理的文件"

            valid_files = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    valid_files.append(file_path)
                else:
                    print(f"⚠️  文件不存在: {file_path}")

            if len(valid_files) == 0:
                return "没有有效的文件"

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
                    if audio_transcription:
                        pass

                self._save_multimodal_chat_history(text, valid_files, response)

                if self.task_manager.tts_manager.tts_enabled and len(response) > 5:
                    def speak_reply():
                        try:
                            self.task_manager.tts_manager.speak_text_intelligently(response)
                        except Exception as e:
                            print(f"❌ 语音播报失败: {e}")

                    threading.Timer(0.5, speak_reply).start()

                # 返回空字符串，因为结果已经通过流式输出显示
                return ""
            else:
                error_msg = f"❌ 多模态分析失败: {response}"
                print(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 多模态处理失败: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def _sync_device_to_task_chain(self):
        """同步设备信息到TaskChain"""
        if self.task_manager.is_connected:
            self.task_chain.device_id = self.task_manager.device_id
            self.task_chain.task_args = self.task_manager.task_args

    def _append_output(self, text: str):
        """追加输出到文本框"""
        output_text = self.view.get_component("output_text")
        if output_text:
            # 使用信号确保线程安全
            self._output_signal.emit(text)

    def _do_append_output_from_signal(self, text: str):
        """实际执行输出追加（在主线程中调用）"""
        output_text = self.view.get_component("output_text")
        if output_text:
            output_text.setReadOnly(False)
            output_text.insertPlainText(text)
            output_text.ensureCursorVisible()
            output_text.setReadOnly(True)

    def terminate_operation(self):
        """终止当前操作"""
        if not self.is_executing:
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'═' * 9} [{timestamp} 操作终止] {'═' * 9}")
        print("🛑 正在发送终止信号...\n")
        
        self._cleanup_active_threads()
        
        # 停止持续回复
        if hasattr(self, '_current_reply_chain') and self._current_reply_chain:
            self._current_reply_chain.stop()
        
        # 停止 TaskChain 中的持续回复
        if hasattr(self, 'task_chain') and self.task_chain:
            self.task_chain.stop_continuous_reply()
        
        if not self.active_threads and not self.is_continuous_mode:
            self.show_toast("没有正在执行的操作", "info")
            return

        self.terminate_flag.set()
        self.terminating.set()
        self._disable_terminate_button()

        if self.is_continuous_mode:
            print(f"\n🛑 正在终止持续回复模式...")
        else:
            print(f"\n🛑 正在终止当前任务...")
        self.show_toast("已发送终止信号", "warning")

    def simulate_enter(self):
        """模拟回车键效果"""
        print("[用户点击模拟回车按钮]")
        try:
            from yuntai.core.agent_executor import AgentExecutor
            AgentExecutor.user_confirm()
        except Exception as e:
            print(f"⚠️  发送确认信号失败: {e}")

        print("[用户已确认]")

    def clear_output(self):
        """清空输出区域"""
        output_text = self.view.get_component("output_text")
        if output_text:
            output_text.setReadOnly(False)
            output_text.clear()
            output_text.setReadOnly(True)
            self.show_toast("输出已清空", "info")

    # ============ 按钮状态管理 ============

    def _disable_execute_button(self):
        """禁用执行按钮"""
        self._disable_execute_button_signal.emit()
        self._show_enter_button_signal.emit()

    def _enable_execute_button(self):
        """启用执行按钮"""
        self._enable_execute_button_signal.emit()
        self._hide_enter_button_signal.emit()

    def _disable_terminate_button(self):
        """禁用终止按钮"""
        self._disable_terminate_button_signal.emit()

    def _enable_terminate_button(self):
        """启用终止按钮"""
        self._enable_terminate_button_signal.emit()

    # ============ 信号槽实现方法 ============

    def _do_enable_execute_button(self):
        """信号槽：启用执行按钮"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            execute_btn.setEnabled(True)

    def _do_disable_execute_button(self):
        """信号槽：禁用执行按钮"""
        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            execute_btn.setEnabled(False)

    def _do_enable_terminate_button(self):
        """信号槽：启用终止按钮"""
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            terminate_btn.setEnabled(True)

    def _do_disable_terminate_button(self):
        """信号槽：禁用终止按钮"""
        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            terminate_btn.setEnabled(False)

    def _do_reset_button_states(self):
        """信号槽：重置按钮状态"""
        self._enable_execute_button_signal.emit()
        self._disable_terminate_button_signal.emit()
        self.is_executing = False

    def _do_clear_attached_files(self):
        """信号槽：清理附件文件"""
        try:
            self.clear_attached_files()
        except Exception as e:
            print(f"❌ 清理文件失败: {e}")

    # ============ 消息处理 ============

    def process_messages(self):
        """处理消息队列"""
        try:
            while not self.message_queue.empty():
                msg_type, msg_content = self.message_queue.get_nowait()
                self.show_toast(msg_content, msg_type)
        except:
            pass

    def show_toast(self, message: str, msg_type: str = "info"):
        """显示提示消息 - 使用新的Toast组件"""
        if hasattr(self.view, 'toast_widget'):
            self.view.toast_widget.show_toast(message, msg_type, duration=2000)

    # ============ 设备类型回调 ============

    def _setup_device_type_callback(self):
        """设置设备类型变化回调"""
        self.view._device_type_callback = self._on_device_type_changed

    def _on_device_type_changed(self, device_type: str):
        """设备类型改变时的回调"""
        if "HarmonyOS" in device_type or "HDC" in device_type:
            self.device_type = "harmonyos"
        else:
            self.device_type = "android"
        self.show_toast(f"已切换到 {device_type}", "info")

    # ============ TTS预加载 ============

    def preload_tts_modules(self):
        """预加载TTS模块"""
        
        def load_async():
            # 使用信号在主线程中显示加载遮罩
            self._show_tts_loading_signal.emit("正在加载TTS语音资源中...")
            success = self.task_manager.preload_tts_modules()
            # 使用信号在主线程中更新指示器
            self._update_tts_indicator_signal.emit(success)
            if success:
                self._synthesize_welcome_message()
            else:
                self._hide_tts_loading_signal.emit()
        
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
                self._hide_tts_loading_signal.emit()
                return

            self._show_tts_loading_signal.emit("正在合成欢迎语...")
            tts.speak_text_intelligently("你好，我是小芸，很高兴为您服务")
            self._wait_audio_then_hide()
        except Exception:
            self._hide_tts_loading_signal.emit()

    def _wait_audio_then_hide(self):
        """等待音频播放完成后隐藏遮罩"""
        def wait_thread():
            try:
                tts = self.task_manager.tts_manager
                max_wait = 30
                waited = 0
                while tts.is_playing_audio and waited < max_wait:
                    time.sleep(0.5)
                    waited += 0.5
            finally:
                self._hide_tts_loading_signal.emit()
        
        threading.Thread(target=wait_thread, daemon=True).start()

    # ============ 持续回复线程 ============

    def start_continuous_reply_thread(self, task_args, target_app, target_object, device_id):
        """启动持续回复线程"""
        if self.is_continuous_mode:
            print("⚠️  已经有持续回复在运行")
            return
        
        self.is_continuous_mode = True
        self.terminate_flag.clear()
        self._disable_execute_button()
        self._enable_terminate_button()
        print(f"🔄 启动持续回复模式: {target_app} -> {target_object}")

        def continuous_reply_loop():
            try:
                print(f"🚀 持续回复线程启动: {target_app} -> {target_object}")
                
                self._current_reply_chain = ReplyChain(
                    device_id=device_id,
                    file_manager=self.task_manager.file_manager,
                    tts_manager=self.task_manager.tts_manager
                )
                
                success, result = self._current_reply_chain.continuous_reply(
                    target_app, target_object
                )
                
                if success:
                    print(f"✅ {result}")
                else:
                    print(f"⏹️  {result}")
                    
            except Exception as e:
                print(f"❌ 持续回复错误：{str(e)}")
            finally:
                self.is_continuous_mode = False
                self.terminate_flag.clear()
                self._current_reply_chain = None
                # 使用信号槽重置按钮状态
                self._reset_button_states_signal.emit()

        thread = threading.Thread(target=continuous_reply_loop)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    # ============ 主题切换 ============

    def toggle_theme(self):
        """切换主题"""
        # 重置TTS事件绑定标志，以便重新创建页面后能重新绑定事件
        self.tts_handler._events_bound = False
        self.tts_handler._events_bound_success = False

        # 保存当前页面索引
        current_page = self.view.current_page_index

        self.view.toggle_theme()
        theme_name = "深色主题" if self.view.is_dark_theme else "浅色主题"
        self.show_toast(f"已切换到{theme_name}", "info")

        # 更新输出捕获的主题状态
        if self.output_capture:
            self.output_capture.set_dark_theme(self.view.is_dark_theme)
        
        # 重新绑定当前页面的事件
        self._rebind_current_page_events(current_page)
    
    def _rebind_current_page_events(self, page_index: int):
        """重新绑定当前页面的事件"""
        if page_index == 0:
            # 控制中心页面
            self._bind_dashboard_events()
        elif page_index == 1:
            # 设备管理页面
            self.connection_handler._bind_events()
        elif page_index == 2:
            # TTS语音页面 - 重新绑定事件
            self.tts_handler._bind_events()
        elif page_index == 3:
            # 历史记录页面
            self.system_handler._bind_history_events()
        elif page_index == 4:
            # 动态功能页面
            self.dynamic_handler._bind_events()
        elif page_index == 5:
            # 系统设置页面
            self.system_handler._bind_settings_events()

    # ============ 初始连接检查 ============

    def check_initial_connection(self):
        """检查初始连接"""
        try:
            self.task_manager.check_initial_connection()
            if self.task_manager.is_connected:
                self.connection_handler._update_connection_status_gui(True)
                self.show_toast(f"已自动连接: {self.task_manager.device_id}", "success")
        except Exception as e:
            print(f"初始连接检查失败: {e}")

    # ============ 快捷键处理 ============

    def execute_shortcut(self, shortcut_key):
        """执行快捷键对应的应用打开命令"""
        from yuntai.core.config import SHORTCUTS
        command = SHORTCUTS.get(shortcut_key, "")
        if not command:
            return

        command_input = self.view.get_component("command_input")
        if command_input:
            command_input.clear()
            command_input.setPlainText(command)
            self.execute_command()
            app_name = command.replace("打开", "")
            self.show_toast(f"正在打开{app_name}", "info")

    # ============ TTS 指示器更新 ============

    def update_tts_indicator(self, enabled: bool):
        """更新TTS指示器状态"""
        tts_indicator = self.view.get_component("tts_indicator")
        if tts_indicator:
            if enabled:
                tts_indicator.setText("● TTS: 开")
                tts_indicator.setStyleSheet(f"""
                    color: {ThemeColors.STATUS_ACTIVE}; 
                    background: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-weight: 500;
                """)
            else:
                tts_indicator.setText("● TTS: 关")
                tts_indicator.setStyleSheet(f"""
                    color: {ThemeColors.STATUS_INACTIVE}; 
                    background: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                """)

    # ============ 辅助方法 ============
    
    def _cleanup_active_threads(self):
        """清理已结束的线程"""
        self.active_threads = [t for t in self.active_threads if t.is_alive()]
    
    def _highlight_enter_button(self):
        """高亮显示回车按钮"""
        enter_btn = self.view.get_component("enter_button")
        if enter_btn:
            enter_btn.show()
    
    def _reset_button_states(self):
        """重置按钮状态"""
        self._enable_execute_button()
        self._disable_terminate_button()
        self.is_executing = False
    
    def _get_chat_history_for_multimodal(self) -> list:
        """获取多模态聊天的历史记录"""
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
    
    def _save_multimodal_chat_history(self, text: str, file_paths: list, reply: str):
        """保存多模态聊天历史"""
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

    # ============ 窗口关闭 ============

    def on_closing(self, event):
        """窗口关闭事件处理"""
        self.terminate_operation()
        
        # 恢复标准输出
        if self.output_capture:
            self.output_capture.restore()
        
        # 停止定时器
        if hasattr(self, 'message_timer'):
            self.message_timer.stop()
        
        # 接受关闭事件
        event.accept()

    def run(self):
        """运行应用程序"""
        self.view.show()
        return self.app.exec()


def main():
    """主函数"""
    from yuntai.core.config import PROJECT_ROOT, SCRCPY_PATH
    
    controller = GUIController(PROJECT_ROOT, SCRCPY_PATH)
    sys.exit(controller.run())


if __name__ == "__main__":
    main()

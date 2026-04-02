"""
GUI 控制器核心模块
================

ControllerCore 包含信号定义、初始化逻辑、生命周期管理、UI事件绑定等核心功能。
其他 mixin 模块通过 self 属性访问此核心类中初始化的实例变量。
"""
import sys
import logging
import threading
import queue
import time
import datetime
import traceback
from typing import Any

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

DIVIDER = "═" * 50


def _format_action_lines(action: dict) -> str:
    if not isinstance(action, dict):
        return str(action)
    lines = []
    for key, value in action.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)

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
from phone_agent.events import get_global_event_emitter

# LangChain Callbacks
from yuntai.callbacks import (
    get_callback_manager,
    QtStreamingCallbackHandler,
    LoggingCallbackHandler,
    PerformanceCallbackHandler
)


class ControllerCore(QObject):
    """
    GUI 控制器核心

    包含信号定义、初始化逻辑、生命周期管理、UI事件绑定等核心功能。

    Attributes:
        project_root: 项目根目录
        scrcpy_path: Scrcpy 工具路径
        app: QApplication 实例
        view: GUI 视图实例
        task_manager: 任务管理器实例
        callback_manager: 回调管理器实例
        task_chain: 任务处理链实例
        judgement_agent: 任务判断 Agent
        agent_event_emitter: Agent 事件发射器
        message_queue: 消息队列
        is_executing: 是否正在执行任务
        is_continuous_mode: 是否处于持续回复模式
        terminate_flag: 终止标志
        device_type: 设备类型
    """

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
        """
        初始化 GUI 控制器

        Args:
            project_root: 项目根目录
            scrcpy_path: Scrcpy 工具路径
        """
        super().__init__()

        # 存储路径参数
        self.project_root = project_root
        self.scrcpy_path = SCRCPY_PATH

        logger.debug("初始化 GUIController")

        # 创建QApplication实例（如果不存在）
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
            logger.debug("创建 QApplication 实例")

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
        logger.debug("任务管理器初始化完成")

        # 初始化回调管理器
        self.callback_manager = get_callback_manager()
        self._setup_callbacks()
        logger.debug("回调管理器初始化完成")

        # 初始化新的 TaskChain
        self.task_chain = TaskChain(
            device_id="",
            file_manager=self.task_manager.file_manager,
            tts_manager=self.task_manager.tts_manager
        )

        # 初始化判断 Agent
        self.judgement_agent = JudgementAgent()

        # 初始化结构化事件监听
        self.agent_event_emitter = get_global_event_emitter()
        self.agent_event_emitter.on(self._handle_agent_event)

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
        logger.debug("Handlers 初始化完成")

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

        logger.info("GUIController 初始化完成")

    def _setup_callbacks(self):
        """设置 LangChain Callbacks"""
        logger.debug("设置 LangChain Callbacks")

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
        """
        流式输出完成回调

        Args:
            response: 完整的响应内容
        """
        logger.debug("流式输出完成，响应长度: %d", len(response))

    def get_callbacks(self) -> list:
        """
        获取 GUI 控制器的回调处理器列表

        Returns:
            回调处理器列表
        """
        return self.callback_manager.get_callbacks(include_global=True)

    def _bind_ui_events(self):
        """绑定所有UI事件（主要是导航和主控台）"""
        logger.debug("绑定 UI 事件")

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
        logger.debug("绑定控制台页面事件")

        execute_btn = self.view.get_component("execute_button")
        if execute_btn:
            try:
                execute_btn.clicked.disconnect()
            except TypeError:
                pass
            execute_btn.clicked.connect(self.execute_command)

        terminate_btn = self.view.get_component("terminate_button")
        if terminate_btn:
            try:
                terminate_btn.clicked.disconnect()
            except TypeError:
                pass
            terminate_btn.clicked.connect(self.terminate_operation)

        # TTS设置按钮（调用TTS Handler的弹窗）
        tts_btn = self.view.get_component("tts_button")
        if tts_btn:
            try:
                tts_btn.clicked.disconnect()
            except TypeError:
                pass
            tts_btn.clicked.connect(self.tts_handler.show_tts_settings_popup)

        clear_btn = self.view.get_component("clear_output_btn")
        if clear_btn:
            try:
                clear_btn.clicked.disconnect()
            except TypeError:
                pass
            clear_btn.clicked.connect(self.clear_output)

        scrcpy_btn = self.view.get_component("scrcpy_button")
        if scrcpy_btn:
            try:
                scrcpy_btn.clicked.disconnect()
            except TypeError:
                pass
            scrcpy_btn.clicked.connect(self.connection_handler.show_scrcpy_popup)

        enter_btn = self.view.get_component("enter_button")
        if enter_btn:
            try:
                enter_btn.clicked.disconnect()
            except TypeError:
                pass
            enter_btn.clicked.connect(self.simulate_enter)

        # 绑定主题切换按钮
        theme_toggle_btn = self.view.get_component("theme_toggle_button")
        if theme_toggle_btn:
            try:
                theme_toggle_btn.clicked.disconnect()
            except TypeError:
                pass
            theme_toggle_btn.clicked.connect(self.toggle_theme)

        # 绑定文件管理上传按钮
        file_upload_btn = self.view.get_component("file_upload_button")
        if file_upload_btn:
            try:
                file_upload_btn.clicked.disconnect()
            except TypeError:
                pass
            file_upload_btn.clicked.connect(self.show_file_upload)

        # 绑定快捷键按钮
        for key, app_name in SHORTCUTS.items():
            shortcut_btn = self.view.get_component(f"shortcut_btn_{key}")
            if shortcut_btn:
                try:
                    shortcut_btn.clicked.disconnect()
                except TypeError:
                    pass
                shortcut_btn.clicked.connect(lambda checked, k=key: self.execute_shortcut(k))

    # ============ 页面显示方法 ============

    def show_dashboard(self):
        """显示控制台页面"""
        logger.debug("显示控制台页面")
        self.view.create_dashboard_page()
        self._bind_dashboard_events()

    # ============ 消息处理 ============

    def process_messages(self):
        """处理消息队列"""
        try:
            while not self.message_queue.empty():
                msg_type, msg_content = self.message_queue.get_nowait()
                self.show_toast(msg_content, msg_type)
        except Exception as e:
            logger.debug("处理消息队列失败: %s", str(e))

    # ============ 输出方法 ============

    def _append_output(self, text: str):
        """
        追加输出到文本框

        Args:
            text: 要追加的文本
        """
        output_text = self.view.get_component("output_text")
        if output_text:
            self._output_signal.emit(text)

    def _do_append_output_from_signal(self, text: str):
        """
        实际执行输出追加（在主线程中调用）

        Args:
            text: 要追加的文本
        """
        output_text = self.view.get_component("output_text")
        if output_text:
            output_text.setReadOnly(False)
            output_text.insertPlainText(text)
            output_text.ensureCursorVisible()
            output_text.setReadOnly(True)

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

    # ============ 主题切换 ============

    def toggle_theme(self):
        """切换主题"""
        logger.info("切换主题")

        self.tts_handler._events_bound = False
        self.tts_handler._events_bound_success = False

        current_page = self.view.current_page_index

        self.view.toggle_theme()
        theme_name = "深色主题" if self.view.is_dark_theme else "浅色主题"
        self.show_toast(f"已切换到{theme_name}", "info")

        self._rebind_current_page_events(current_page)

    def _rebind_current_page_events(self, page_index: int):
        """
        重新绑定当前页面的事件

        Args:
            page_index: 页面索引
        """
        logger.debug("重新绑定页面事件，索引: %d", page_index)

        if page_index == 0:
            self._bind_dashboard_events()
        elif page_index == 1:
            self.connection_handler._bind_events()
        elif page_index == 2:
            self.tts_handler._bind_events()
        elif page_index == 3:
            self.system_handler._bind_history_events()
        elif page_index == 4:
            self.dynamic_handler._bind_events()
        elif page_index == 5:
            self.system_handler._bind_settings_events()

    # ============ 设备类型回调 ============

    def _setup_device_type_callback(self):
        """设置设备类型变化回调"""
        self.view._device_type_callback = self._on_device_type_changed

    # ============ 初始连接检查 ============

    def check_initial_connection(self):
        """检查初始连接"""
        logger.debug("检查初始连接")
        try:
            self.task_manager.check_initial_connection()
            if self.task_manager.is_connected:
                self.connection_handler._update_connection_status_gui(True)
                self.show_toast(f"已自动连接: {self.task_manager.device_id}", "success")
        except Exception as e:
            logger.warning("初始连接检查失败: %s", str(e))

    # ============ 窗口关闭 ============

    def on_closing(self, event):
        """
        窗口关闭事件处理

        Args:
            event: 关闭事件对象
        """
        logger.info("窗口关闭")
        self.terminate_operation()

        self.agent_event_emitter.off(self._handle_agent_event)

        if hasattr(self, 'message_timer'):
            self.message_timer.stop()

        event.accept()

    def run(self):
        """
        运行应用程序

        Returns:
            int: 退出代码
        """
        logger.info("运行应用程序")
        self.view.show()
        return self.app.exec()

    def _format_agent_event_text(self, event: dict[str, Any]) -> str:
        """Format structured event into GUI output text."""
        event_type = event.get("type", "")
        payload = event.get("payload", {}) or {}

        if event_type == "run_started":
            return ""
        if event_type == "task_type":
            task_type = payload.get("task_type", "")
            if task_type == "free_chat":
                return f"📋 任务类型: {task_type}\n"
            return f"📋 任务类型: {task_type}\n\n{DIVIDER}\n💭 思考过程\n{DIVIDER}\n"
        if event_type == "thinking_chunk":
            return payload.get("text", "")
        if event_type == "thinking_complete":
            return "\n"
        if event_type == "action_decoded":
            action = payload.get("action", {})
            action_text = _format_action_lines(action)
            return f"\n{DIVIDER}\n🎯 动作\n{DIVIDER}\n{action_text}\n"
        if event_type == "action_executed":
            return ""
        if event_type == "performance_metric":
            if payload.get("name") == "label":
                return f"\n{DIVIDER}\n⏱️  性能指标\n{DIVIDER}\n"
            label = payload.get("label", payload.get("name", "metric"))
            value = payload.get("value", "")
            unit = payload.get("unit", "")
            return f"{label}: {value}{unit}\n"
        if event_type == "result":
            msg = payload.get("message", "")
            return f"\n🎉 结果：{msg}\n" if msg else ""
        if event_type == "error":
            return f"❌ 错误：{payload.get('message', '')}\n"
        if event_type == "status":
            return f"{payload.get('message', '')}\n"
        if event_type == "run_finished":
            return ""
        return ""

    def _handle_agent_event(self, event: dict[str, Any]) -> None:
        """Handle agent structured event in GUI thread-safe way."""
        text = self._format_agent_event_text(event)
        if text:
            self._output_signal.emit(text)

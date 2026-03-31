"""
SystemHandler - 系统管理处理器 (PyQt6 重构版)
=============================================

负责处理历史记录、系统设置和文件管理功能。

主要组件:
    - SystemCheckDialog: 系统检查对话框
    - SystemHandler: 系统管理处理器

功能特性:
    - 历史记录管理（加载、清空）
    - 系统设置页面
    - 系统环境检查（ADB/HDC、模型API、TTS、设备连接）
    - 文件管理信息显示

使用示例:
    >>> handler = SystemHandler(controller)
    >>> handler.show_history_panel()  # 显示历史记录页面
    >>> handler.check_system_gui()  # 执行系统检查
"""

import logging
from pathlib import Path
import threading

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

from yuntai.core.config import (
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR,
    FOREVER_MEMORY_FILE, CONNECTION_CONFIG_FILE,
    ZHIPU_API_BASE_URL, ZHIPU_MODEL, ZHIPU_API_KEY,
    DEVICE_TYPE_HARMONY
)
from yuntai.gui.styles import (
    ThemeColors, ThemeFonts,
    DialogStyle, get_dialog_stylesheet, get_dialog_button_stylesheet,
    get_dialog_card_stylesheet, get_dialog_textedit_stylesheet,
    show_confirm_dialog
)


class SystemCheckDialog(QDialog):
    """
    系统检查对话框 - 带信号支持
    
    显示系统环境检查结果，包括ADB/HDC环境、模型API、TTS功能和设备连接状态。
    支持线程安全的UI更新。
    
    Attributes:
        is_harmony: 是否为HarmonyOS设备
        task_manager: 任务管理器实例
        tool_result: 工具检查结果
        api_result: API检查结果
        colors: 当前主题颜色
    """
    
    # 定义信号
    append_text_signal = pyqtSignal(str)
    set_status_signal = pyqtSignal(str)
    set_status_color_signal = pyqtSignal(str)
    
    def __init__(self, parent, is_harmony, task_manager):
        super().__init__(parent)
        self.is_harmony = is_harmony
        self.task_manager = task_manager
        self.tool_result = False
        self.api_result = False
        
        # 获取当前主题颜色
        self.colors = parent.colors if hasattr(parent, 'colors') else ThemeColors
        
        self.setWindowTitle("🔍 系统检查")
        self.setFixedSize(DialogStyle.DIALOG_WIDTH_LARGE, DialogStyle.DIALOG_HEIGHT_MEDIUM)
        self.setModal(True)
        self.setStyleSheet(get_dialog_stylesheet(self.colors))
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        layout.setSpacing(DialogStyle.DIALOG_SPACING)

        # 标题区域
        title_label = QLabel("🔍 系统检查")
        title_label.setFont(ThemeFonts.TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(title_label)

        device_type_name = "HarmonyOS (HDC)" if self.is_harmony else "Android (ADB)"
        subtitle_label = QLabel(f"正在检查 {device_type_name} 系统配置...")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        layout.addWidget(subtitle_label)

        # 结果文本框
        result_frame = QFrame()
        result_frame.setStyleSheet(get_dialog_card_stylesheet(self.colors))
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(15, 15, 15, 15)

        self.result_text = QTextEdit()
        self.result_text.setFont(ThemeFonts.CODE_SMALL)
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(get_dialog_textedit_stylesheet(self.colors))
        self.result_text.setText("正在准备系统检查，请稍候...\n")
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_frame, 1)

        # 状态标签
        self.status_label = QLabel("准备开始检查...")
        self.status_label.setFont(ThemeFonts.BODY_MEDIUM)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(self.status_label)
        
    def _connect_signals(self):
        self.append_text_signal.connect(self._on_append_text)
        self.set_status_signal.connect(self._on_set_status)
        self.set_status_color_signal.connect(self._on_set_status_color)
        
    def _on_append_text(self, text):
        """追加文本到结果区域"""
        self.result_text.append(text)
        cursor = self.result_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.result_text.setTextCursor(cursor)
        
    def _on_set_status(self, text):
        """设置状态标签文本"""
        self.status_label.setText(text)
        
    def _on_set_status_color(self, color):
        """设置状态标签颜色"""
        self.status_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        
    def append_text(self, text):
        """线程安全的追加文本"""
        self.append_text_signal.emit(text)
        
    def set_status(self, text):
        """线程安全的设置状态"""
        self.set_status_signal.emit(text)
        
    def set_status_color(self, color):
        """线程安全的设置状态颜色"""
        self.set_status_color_signal.emit(color)
        
    def scroll_to_bottom(self):
        """滚动到底部"""
        cursor = self.result_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.result_text.setTextCursor(cursor)


class SystemHandler(QObject):
    """
    系统管理处理器 - 负责历史/设置/文件管理
    
    处理历史记录、系统设置和文件管理功能。
    通过信号槽机制实现线程安全的UI更新。
    
    Attributes:
        controller: 控制器实例
        view: 视图实例
        task_manager: 任务管理器实例
        start_check_thread_signal: 启动检查线程信号
    """

    # 定义信号用于替代QTimer.singleShot
    start_check_thread_signal = pyqtSignal()

    def __init__(self, controller):
        """
        初始化系统处理器
        
        Args:
            controller: 控制器实例
        """
        super().__init__()
        self.controller = controller
        self.view = controller.view
        self.task_manager = controller.task_manager
        logger.debug("SystemHandler初始化完成")

        # 连接信号
        self.start_check_thread_signal.connect(self._on_start_check_thread)

    def show_history_panel(self):
        """显示历史记录页面"""
        self.view.create_history_page()
        self._bind_history_events()
        self.load_history_data()

    def _bind_history_events(self):
        """绑定历史页面事件"""
        refresh_btn = self.view.get_component("refresh_history_btn")
        if refresh_btn:
            try:
                refresh_btn.clicked.disconnect()
            except TypeError:
                pass
            refresh_btn.clicked.connect(self.load_history_data)

        clear_btn = self.view.get_component("clear_history_btn")
        if clear_btn:
            try:
                clear_btn.clicked.disconnect()
            except TypeError:
                pass
            clear_btn.clicked.connect(self.clear_history_data)

    def show_settings_panel(self):
        """显示系统设置页面"""
        self.view.create_settings_page()
        self._bind_settings_events()

    def _bind_settings_events(self):
        """绑定设置页面事件"""
        settings_btns = [
            (self.view.get_component("settings_btn_0"), self.controller.connection_handler.show_panel),
            (self.view.get_component("settings_btn_1"), self.check_system_gui),
            (self.view.get_component("settings_btn_2"), self.controller.tts_handler.show_panel),
            (self.view.get_component("settings_btn_3"), self.show_file_management),
        ]

        for btn, command in settings_btns:
            if btn:
                try:
                    btn.clicked.disconnect()
                except TypeError:
                    pass
                btn.clicked.connect(command)

    def load_history_data(self):
        """加载历史数据"""
        try:
            history = self.task_manager.file_manager.safe_read_json_file(
                CONVERSATION_HISTORY_FILE,
                {"sessions": [], "free_chats": []}
            )

            text_content = ""

            sessions = history.get("sessions", [])
            if sessions:
                text_content += "📱 聊天会话:\n" + "=" * 50 + "\n\n"
                for session in sessions[-20:]:
                    text_content += f"时间: {session.get('timestamp', '未知')}\n"
                    text_content += f"目标: {session.get('target_app', '未知')} -> {session.get('target_object', '未知')}\n"
                    if session.get('reply_generated'):
                        text_content += f"回复: {session.get('reply_generated')}\n"
                    text_content += "-" * 30 + "\n\n"

            free_chats = history.get("free_chats", [])
            if free_chats:
                text_content += "💬 自由聊天:\n" + "=" * 50 + "\n\n"
                for chat in free_chats[-20:]:
                    text_content += f"时间: {chat.get('timestamp', '未知')}\n"
                    text_content += f"用户: {chat.get('user_input', '未知')}\n"
                    text_content += f"AI: {chat.get('assistant_reply', '未知')}\n"
                    text_content += "-" * 30 + "\n\n"

            history_text = self.view.get_component("history_text")
            if history_text:
                history_text.setText(text_content)

        except Exception as e:
            print(f"❌ 加载历史数据失败: {e}")
            import traceback
            traceback.print_exc()

    def clear_history_data(self):
        """清空历史数据"""
        result = show_confirm_dialog(
            self.view,
            "确认清空",
            "确定要清空所有历史记录吗？此操作不可恢复！",
            "确认清空",
            "取消",
            "danger"
        )

        if not result:
            return

        try:
            self.task_manager.file_manager.safe_write_json_file(
                CONVERSATION_HISTORY_FILE,
                {"sessions": [], "free_chats": []}
            )
            self.load_history_data()
            self.controller.show_toast("历史记录已清空", "success")
        except Exception as e:
            self.controller.show_toast(f"清空历史记录失败: {str(e)}", "error")

    def check_system_gui(self):
        """可视化系统检查"""
        device_type_menu = self.view.get_component("device_type_menu")
        is_harmony = False
        if device_type_menu and "HarmonyOS" in device_type_menu.currentText():
            is_harmony = True

        dialog = SystemCheckDialog(self.view, is_harmony, self.task_manager)

        def check_thread():
            try:
                tool_name = "HDC" if is_harmony else "ADB"
                dialog.set_status(f"检查{tool_name}环境...")

                # 检查工具环境
                try:
                    if is_harmony:
                        tool_result = self.task_manager.utils.check_hdc()
                    else:
                        tool_result = self.task_manager.utils.check_system_requirements()
                except Exception as tool_error:
                    tool_result = False

                dialog.tool_result = tool_result

                # 更新工具检查结果
                dialog.append_text("=" * 60)
                dialog.append_text(f"📱 {tool_name} 环境检查")
                dialog.append_text("=" * 60)

                if is_harmony:
                    if tool_result:
                        dialog.append_text("✅ HDC检查通过")
                        dialog.append_text("  HDC工具已安装")
                        dialog.append_text("  HarmonyOS设备连接功能正常")
                    else:
                        dialog.append_text("❌ HDC检查失败")
                        dialog.append_text("  HDC工具未安装或不在PATH中")
                        dialog.append_text("")
                        dialog.append_text("💡 解决方案:")
                        dialog.append_text("  1. 下载HarmonyOS SDK")
                        dialog.append_text("  2. 从SDK目录找到hdc工具")
                        dialog.append_text("  3. 将hdc添加到系统PATH环境变量")
                else:
                    if tool_result:
                        dialog.append_text("✅ ADB检查通过")
                        dialog.append_text("  ADB工具已安装")
                        dialog.append_text("  Android设备连接功能正常")
                    else:
                        dialog.append_text("❌ ADB检查失败")
                        dialog.append_text("  请确保已安装ADB并添加到系统PATH")
                dialog.append_text("")

                dialog.set_status("检查模型API...")

                # 检查模型API
                try:
                    api_result = self.task_manager.utils.check_model_api(
                        ZHIPU_API_BASE_URL,
                        ZHIPU_MODEL,
                        ZHIPU_API_KEY
                    )
                except Exception as api_error:
                    print(f"❌ API检查出错: {api_error}")
                    api_result = False

                dialog.api_result = api_result

                dialog.append_text("=" * 60)
                dialog.append_text("🤖 模型API检查")
                dialog.append_text("=" * 60)
                if api_result:
                    dialog.append_text("✅ 模型API检查通过")
                    dialog.append_text(f"  模型: {ZHIPU_MODEL}")
                    dialog.append_text(f"  密钥: {ZHIPU_API_KEY[:10]}...")
                else:
                    dialog.append_text("❌ 模型API检查失败")
                    dialog.append_text("  请检查API密钥或网络连接")
                dialog.append_text("")

                dialog.set_status("检查TTS功能...")

                # 检查TTS
                dialog.append_text("=" * 60)
                dialog.append_text("🎤 TTS功能检查")
                dialog.append_text("=" * 60)

                if self.task_manager.tts_manager.tts_available:
                    dialog.append_text("✅ TTS模块可用")

                    gpt_count = len(self.task_manager.tts_manager.tts_files_database["gpt"])
                    sovits_count = len(self.task_manager.tts_manager.tts_files_database["sovits"])
                    audio_count = len(self.task_manager.tts_manager.tts_files_database["audio"])
                    text_count = len(self.task_manager.tts_manager.tts_files_database["text"])

                    dialog.append_text(f"  GPT模型: {gpt_count} 个")
                    dialog.append_text(f"  SoVITS模型: {sovits_count} 个")
                    dialog.append_text(f"  参考音频: {audio_count} 个")
                    dialog.append_text(f"  参考文本: {text_count} 个")

                    if gpt_count > 0 and sovits_count > 0 and audio_count > 0 and text_count > 0:
                        dialog.append_text("  ✅ TTS资源完整")
                    else:
                        dialog.append_text("  ⚠️  TTS资源不完整")
                else:
                    dialog.append_text("❌ TTS模块不可用")
                    dialog.append_text("  请安装GPT-SoVITS并配置环境")

                dialog.append_text("")

                dialog.set_status("检查设备连接...")

                # 检查设备连接
                dialog.append_text("=" * 60)
                dialog.append_text("📱 设备连接检查")
                dialog.append_text("=" * 60)

                if self.task_manager.is_connected:
                    dialog.append_text(f"✅ 设备已连接: {self.task_manager.device_id}")
                    conn_type = self.task_manager.config.get('connection_type', '未知')
                    dialog.append_text(f"  连接类型: {conn_type}")
                else:
                    dialog.append_text("⚠️  设备未连接")
                    dialog.append_text("  请前往设备管理页面连接设备")

                dialog.append_text("")
                dialog.append_text("=" * 60)
                dialog.append_text("📋 检查结论")
                dialog.append_text("=" * 60)

                # 结论
                if tool_result and api_result:
                    dialog.append_text("🎉 系统检查通过，核心组件正常")
                    dialog.set_status("检查完成，核心组件正常")
                    dialog.set_status_color(ThemeColors.SUCCESS)
                else:
                    dialog.append_text("⚠️  系统检查发现一些问题")
                    dialog.set_status("检查完成，发现一些问题")
                    dialog.set_status_color(ThemeColors.WARNING)

            except Exception as e:
                import traceback
                traceback.print_exc()
                dialog.append_text(f"\n❌ 检查过程中发生错误: {str(e)}\n")
                dialog.set_status(f"检查出错: {str(e)[:30]}...")
                dialog.set_status_color(ThemeColors.DANGER)

        # 保存check_thread引用以便信号槽使用
        self._current_check_thread = check_thread
        self._current_check_dialog = dialog

        # 延迟启动线程，确保对话框已显示
        # 使用信号槽替代QTimer.singleShot
        QTimer.singleShot(100, self.start_check_thread_signal.emit)

        dialog.exec()

    def _on_start_check_thread(self):
        """信号槽：启动检查线程"""
        if hasattr(self, '_current_check_thread') and self._current_check_thread:
            threading.Thread(target=self._current_check_thread, daemon=True).start()

    def show_file_management(self):
        """显示文件管理"""
        try:
            # 获取当前主题颜色
            colors = self.view.colors if hasattr(self.view, 'colors') else ThemeColors
            
            info_text = f"""文件管理:

历史记录文件: {CONVERSATION_HISTORY_FILE}
日志目录: {RECORD_LOGS_DIR}
永久记忆文件: {FOREVER_MEMORY_FILE}
连接配置文件: {CONNECTION_CONFIG_FILE}

TTS相关目录:
• GPT模型目录: {self.task_manager.tts_manager.default_tts_config['gpt_model_dir']}
• SoVITS模型目录: {self.task_manager.tts_manager.default_tts_config['sovits_model_dir']}
• 参考音频目录: {self.task_manager.tts_manager.default_tts_config['ref_audio_root']}
• TTS输出目录: {self.task_manager.tts_manager.default_tts_config['output_path']}

文件状态:
• 历史记录文件: {'存在' if Path(CONVERSATION_HISTORY_FILE).exists() else '不存在'}
• 日志目录: {'存在' if Path(RECORD_LOGS_DIR).exists() else '不存在'}
• 永久记忆文件: {'存在' if FOREVER_MEMORY_FILE and Path(FOREVER_MEMORY_FILE).exists() else '不存在'}
• 连接配置文件: {'存在' if Path(CONNECTION_CONFIG_FILE).exists() else '不存在'}
"""

            dialog = QDialog(self.view)
            dialog.setWindowTitle("📁 文件管理")
            dialog.setFixedSize(DialogStyle.DIALOG_WIDTH_LARGE, DialogStyle.DIALOG_HEIGHT_MEDIUM)
            dialog.setModal(True)
            dialog.setStyleSheet(get_dialog_stylesheet(colors))

            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(
                DialogStyle.DIALOG_MARGIN, 
                DialogStyle.DIALOG_MARGIN, 
                DialogStyle.DIALOG_MARGIN, 
                DialogStyle.DIALOG_MARGIN
            )
            layout.setSpacing(DialogStyle.DIALOG_SPACING)

            title_label = QLabel("📁 文件管理")
            title_label.setFont(ThemeFonts.TITLE)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
            layout.addWidget(title_label)

            # 文件信息文本框
            info_frame = QFrame()
            info_frame.setStyleSheet(get_dialog_card_stylesheet(colors))
            info_layout = QVBoxLayout(info_frame)
            info_layout.setContentsMargins(15, 15, 15, 15)

            text_edit = QTextEdit()
            text_edit.setFont(ThemeFonts.CODE_SMALL)
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet(get_dialog_textedit_stylesheet(colors))
            text_edit.setText(info_text)
            info_layout.addWidget(text_edit)

            layout.addWidget(info_frame, 1)

            close_btn = QPushButton("关闭")
            close_btn.setFont(ThemeFonts.BODY_MEDIUM)
            close_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
            close_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
            close_btn.setStyleSheet(get_dialog_button_stylesheet("secondary", colors))
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

            dialog.exec()

        except Exception as e:
            self.controller.show_toast(f"显示文件管理失败: {str(e)}", "error")

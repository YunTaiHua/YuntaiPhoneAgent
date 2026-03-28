"""
ConnectionHandler - 设备连接管理处理器 (PyQt6 重构版)
======================================================

负责处理设备连接、检测和投屏功能。

主要组件:
    - DeviceDetectDialog: 设备检测对话框，显示检测结果
    - ConnectionHandler: 设备连接管理处理器

功能特性:
    - 设备检测（ADB/HDC）
    - USB/无线连接方式
    - 设备连接状态管理
    - 手机投屏功能（scrcpy）

使用示例:
    >>> handler = ConnectionHandler(controller)
    >>> handler.show_panel()  # 显示设备管理页面
    >>> handler.detect_devices_gui()  # 检测设备
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import threading
import pyperclip

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QCheckBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

from yuntai.gui.gui_view import GUIView
from yuntai.gui.styles import (
    ThemeColors, ThemeFonts, ThemeCorner,
    DialogStyle, get_dialog_stylesheet, get_dialog_button_stylesheet,
    get_dialog_card_stylesheet, get_dialog_textedit_stylesheet,
    get_dialog_combobox_stylesheet, get_dialog_checkbox_stylesheet
)
from yuntai.core.config import (
    DEVICE_TYPE_HARMONY,
    DEFAULT_WIRELESS_PORT,
)
from yuntai.services.connection_manager import sanitize_device_id


class DeviceDetectDialog(QDialog):
    """
    设备检测对话框 - 带信号支持
    
    显示设备检测结果，支持线程安全的UI更新。
    当检测到设备时显示设备列表，未检测到时显示故障排除指南。
    
    Attributes:
        task_manager: 任务管理器实例
        controller: 控制器实例
        devices: 检测到的设备列表
        device_type: 设备类型（android/harmony）
        device_type_display: 设备类型显示文本
        colors: 当前主题颜色
    """
    
    show_result_signal = pyqtSignal(list, str, str)  # devices, device_type, device_type_display
    
    def __init__(self, parent, task_manager, controller):
        """
        初始化设备检测对话框
        
        Args:
            parent: 父窗口
            task_manager: 任务管理器实例
            controller: 控制器实例
        """
        super().__init__(parent)
        self.task_manager = task_manager
        self.controller = controller
        self.devices = []
        self.device_type = ""
        self.device_type_display = ""
        
        # 获取当前主题颜色
        self.colors = parent.colors if hasattr(parent, 'colors') else ThemeColors
        
        self.setWindowTitle("设备检测结果")
        self.setFixedSize(DialogStyle.DIALOG_WIDTH_LARGE, DialogStyle.DIALOG_HEIGHT_LARGE)
        self.setModal(True)
        self.setStyleSheet(get_dialog_stylesheet(self.colors))
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        self.layout.setSpacing(DialogStyle.DIALOG_SPACING)

        # 标题
        self.title_label = QLabel("📱 设备检测结果")
        self.title_label.setFont(ThemeFonts.TITLE)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        self.layout.addWidget(self.title_label)

        # 设备类型
        self.type_label = QLabel("正在检测...")
        self.type_label.setFont(ThemeFonts.BODY_MEDIUM)
        self.type_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.type_label)

        # 状态标签
        self.status_label = QLabel("正在检测设备，请稍候...")
        self.status_label.setFont(ThemeFonts.SUBTITLE)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        self.layout.addWidget(self.status_label)

        # 内容区域占位
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet(get_dialog_card_stylesheet(self.colors))
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(15, 15, 15, 15)
        self.layout.addWidget(self.content_frame, 1)

        # 关闭按钮
        self.close_btn = QPushButton("关闭")
        self.close_btn.setFont(ThemeFonts.BODY_MEDIUM)
        self.close_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
        self.close_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
        self.close_btn.setStyleSheet(get_dialog_button_stylesheet("secondary", self.colors))
        self.close_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def _connect_signals(self):
        self.show_result_signal.connect(self._on_show_result)
        
    def _on_show_result(self, devices, device_type, device_type_display):
        """在主线程中显示结果"""
        self.devices = devices
        self.device_type = device_type
        self.device_type_display = device_type_display
        
        # 更新设备类型标签
        self.type_label.setText(f"设备类型: {device_type_display}")
        
        # 清除内容区域
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if devices:
            self._show_devices_found()
        else:
            self._show_no_devices()
            
    def _show_devices_found(self):
        """显示找到设备的结果"""
        self.status_label.setText(f"✅ 检测到 {len(self.devices)} 个设备")
        self.status_label.setStyleSheet(f"color: {self.colors.SUCCESS}; background: transparent; border: none;")

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar_label = QLabel("设备列表（可全选复制）:")
        toolbar_label.setFont(ThemeFonts.BODY_MEDIUM)
        toolbar_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        toolbar.addWidget(toolbar_label)
        toolbar.addStretch()

        def copy_to_clipboard():
            device_text = "\n".join([f"{i + 1}. {device}" for i, device in enumerate(self.devices)])
            pyperclip.copy(device_text)
            self.controller.show_toast("已复制到剪贴板", "success")

        copy_btn = QPushButton("📋 复制")
        copy_btn.setFont(ThemeFonts.BODY_XSMALL)
        copy_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        copy_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH_SMALL)
        copy_btn.setStyleSheet(get_dialog_button_stylesheet("primary", self.colors))
        copy_btn.clicked.connect(copy_to_clipboard)
        toolbar.addWidget(copy_btn)
        self.content_layout.addLayout(toolbar)

        # 结果文本框
        result_text = QTextEdit()
        result_text.setFont(ThemeFonts.CODE_SMALL)
        result_text.setReadOnly(True)
        result_text.setStyleSheet(get_dialog_textedit_stylesheet(self.colors))
        text_content = "设备ID列表:\n" + "=" * DialogStyle.TEXT_SEPARATOR_LENGTH + "\n\n"
        for i, device in enumerate(self.devices, 1):
            text_content += f"{i:2d}. {device}\n"
        text_content += "\n" + "=" * DialogStyle.TEXT_SEPARATOR_LENGTH + "\n"
        text_content += "💡 使用说明:\n"
        text_content += "1. 选择文本进行复制\n"
        text_content += "2. 点击上方复制按钮可复制全部\n"
        text_content += "3. 在USB连接方式下使用设备ID连接\n"
        result_text.setText(text_content)
        self.content_layout.addWidget(result_text, 1)

        self.controller.show_toast(f"检测到 {len(self.devices)} 个设备", "success")

    def _show_no_devices(self):
        """显示未找到设备的结果"""
        self.status_label.setText(f"❌ 未检测到任何设备 ({self.device_type_display})")
        self.status_label.setStyleSheet(f"color: {self.colors.DANGER}; background: transparent; border: none;")

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar_label = QLabel("故障排除指南:")
        toolbar_label.setFont(ThemeFonts.BODY_MEDIUM)
        toolbar_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        toolbar.addWidget(toolbar_label)
        toolbar.addStretch()

        tool_name = "hdc" if self.device_type == DEVICE_TYPE_HARMONY else "adb"
        troubleshooting_text = f"""请检查以下项目：
1. 手机是否已通过USB线连接电脑
2. 手机是否已开启【开发者选项】和【USB调试】
3. 连接电脑时，手机上是否点击了【允许USB调试】
4. 尝试重新插拔USB线或重启{tool_name.upper()}服务
5. 如果是无线连接，请确保IP和端口正确"""

        def copy_troubleshooting():
            pyperclip.copy(troubleshooting_text)
            self.controller.show_toast("故障排除指南已复制", "success")

        copy_btn = QPushButton("📋 复制指南")
        copy_btn.setFont(ThemeFonts.BODY_XSMALL)
        copy_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        copy_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH_SMALL + DialogStyle.BUTTON_WIDTH_OFFSET)
        copy_btn.setStyleSheet(get_dialog_button_stylesheet("warning", self.colors))
        copy_btn.clicked.connect(copy_troubleshooting)
        toolbar.addWidget(copy_btn)
        self.content_layout.addLayout(toolbar)

        # 结果文本框
        result_text = QTextEdit()
        result_text.setFont(ThemeFonts.BODY_SMALL)
        result_text.setReadOnly(True)
        result_text.setStyleSheet(get_dialog_textedit_stylesheet(self.colors))
        text_content = "请检查以下项目：\n" + "=" * DialogStyle.TEXT_SEPARATOR_LENGTH + "\n\n"
        checks = [
            "1. 📱 手机是否已通过USB线连接电脑",
            "2. ⚙️ 手机是否已开启【开发者选项】和【USB调试】",
            "3. 📲 连接电脑时，手机上是否点击了【允许USB调试】",
            f"4. 🔄 尝试重新插拔USB线或重启{tool_name.upper()}服务",
            "5. 🔌 如果是无线连接，请确保IP和端口正确"
        ]
        for check in checks:
            text_content += f"{check}\n"
        text_content += "\n" + "=" * DialogStyle.TEXT_SEPARATOR_LENGTH + "\n"
        text_content += "💡 解决方案:\n"
        text_content += "• 在手机设置中搜索【开发者选项】\n"
        text_content += "• 打开【USB调试】开关\n"
        text_content += "• 连接电脑时授权调试权限\n"
        result_text.setText(text_content)
        self.content_layout.addWidget(result_text, 1)

        self.controller.show_toast("未检测到设备", "warning")

    def show_result(self, devices, device_type, device_type_display):
        """线程安全的显示结果"""
        self.show_result_signal.emit(devices, device_type, device_type_display)


class ConnectionHandler(QObject):
    """
    设备连接管理处理器
    
    负责处理设备连接、检测和投屏功能。
    通过信号槽机制实现线程安全的UI更新。
    
    Attributes:
        controller: 控制器实例
        view: 视图实例
        task_manager: 任务管理器实例
        update_status_signal: 连接状态更新信号
    """
    
    # 定义信号用于跨线程UI更新
    update_status_signal = pyqtSignal(bool)  # connected

    def __init__(self, controller):
        """
        初始化连接处理器
        
        Args:
            controller: 控制器实例
        """
        super().__init__()
        self.controller = controller
        self.view = controller.view
        self.task_manager = controller.task_manager
        logger.debug("ConnectionHandler初始化完成")
        
        # 连接信号
        self.update_status_signal.connect(self._do_update_connection_status)

    def show_panel(self):
        """
        显示设备管理页面
        
        创建设备管理页面并绑定事件处理。
        """
        self.view.create_connection_page()
        self._bind_events()
        self._update_connection_status_gui(self.task_manager.is_connected)
        logger.debug("设备管理页面已显示")

    def _bind_events(self):
        """
        绑定连接页面事件
        
        为检测设备、连接设备、断开连接等按钮绑定事件处理函数。
        """
        # 检测设备按钮
        detect_btn = self.view.get_component("detect_devices_btn")
        if detect_btn:
            try:
                detect_btn.clicked.disconnect()
            except TypeError:
                pass
            detect_btn.clicked.connect(self.detect_devices_gui)

        # 连接设备按钮
        connect_btn = self.view.get_component("connect_device_btn")
        if connect_btn:
            try:
                connect_btn.clicked.disconnect()
            except TypeError:
                pass
            connect_btn.clicked.connect(self.connect_device_gui)

        # 断开连接按钮
        disconnect_btn = self.view.get_component("disconnect_device_btn")
        if disconnect_btn:
            try:
                disconnect_btn.clicked.disconnect()
            except TypeError:
                pass
            disconnect_btn.clicked.connect(self.disconnect_device)

        # 连接方式切换事件 - 使用 QButtonGroup
        conn_button_group = self.view.get_component("conn_button_group")
        if conn_button_group:
            try:
                conn_button_group.buttonClicked.disconnect()
            except TypeError:
                pass
            conn_button_group.buttonClicked.connect(self._on_connection_type_changed)

    def _on_connection_type_changed(self, button):
        """连接方式改变时的回调"""
        usb_frame = self.view.get_component("usb_frame")
        wireless_frame = self.view.get_component("wireless_frame")

        if usb_frame and wireless_frame:
            if "USB" in button.text():
                wireless_frame.hide()
                usb_frame.show()
            else:
                usb_frame.hide()
                wireless_frame.show()

    def _show_connection_form(self):
        """显示连接表单（保留兼容性）"""
        pass

    def _get_device_type(self) -> str:
        """获取当前选择的设备类型"""
        device_type_combo = self.view.get_component("device_type_menu")
        if device_type_combo:
            if "HarmonyOS" in device_type_combo.currentText():
                return DEVICE_TYPE_HARMONY
        return "android"

    def _get_device_type_display(self) -> str:
        """获取当前选择的设备类型显示文本"""
        device_type_combo = self.view.get_component("device_type_menu")
        if device_type_combo:
            return device_type_combo.currentText()
        return "Android (ADB)"

    def _get_connection_type(self) -> str:
        """获取当前选择的连接类型"""
        usb_option = self.view.get_component("usb_option")
        if usb_option and usb_option.isChecked():
            return "usb"
        return "wireless"

    def connect_device_gui(self):
        """
        GUI界面连接设备
        
        从UI获取连接配置，在后台线程中执行连接操作。
        连接成功后更新UI状态显示。
        """
        config = self._get_connection_config_from_ui()
        if not config:
            return

        def connect_thread():
            success, device_id, message = self.task_manager.connect_device(config)

            if success:
                self.controller.message_queue.put(("success", f"✅ {message}"))
                self._update_connection_status_gui(True)
                if hasattr(self.controller, '_sync_device_to_task_chain'):
                    self.controller._sync_device_to_task_chain()
            else:
                self.controller.message_queue.put(("error", f"❌ 连接失败: {message}"))
                self._update_connection_status_gui(False)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _get_connection_config_from_ui(self):
        """从UI获取连接配置"""
        # 获取连接类型
        connection_type = self._get_connection_type()
        
        device_type = self._get_device_type()
        device_type_display = self._get_device_type_display()

        config = {
            "connection_type": connection_type,
            "wireless_ip": "",
            "wireless_port": "5555",
            "usb_device_id": "",
            "device_type": device_type,
            "device_type_display": device_type_display
        }

        if connection_type == "usb":
            usb_entry = self.view.get_component("usb_entry")
            if usb_entry:
                device_id = usb_entry.text().strip()
                if not device_id:
                    self.controller.show_toast("请输入USB设备ID", "warning")
                    return None
                config["usb_device_id"] = device_id
        else:
            ip_entry = self.view.get_component("ip_entry")
            port_entry = self.view.get_component("port_entry")

            if ip_entry and port_entry:
                ip = ip_entry.text().strip()
                port = port_entry.text().strip()

                if not ip:
                    self.controller.show_toast("请输入IP地址", "warning")
                    return None

                config["wireless_ip"] = ip
                config["wireless_port"] = port if port else "5555"

        return config

    def detect_devices_gui(self):
        """
        GUI界面检测设备 - 弹窗显示结果
        
        创建设备检测对话框，在后台线程中执行设备检测，
        检测完成后通过信号更新对话框显示。
        """
        # 获取设备类型
        device_type = self._get_device_type()
        device_type_display = self._get_device_type_display()
        
        # 创建对话框
        dialog = DeviceDetectDialog(self.view, self.task_manager, self.controller)
        
        def detect_thread():
            try:
                # 检测设备
                devices = self.task_manager.detect_devices(device_type)
                # 通过信号显示结果
                dialog.show_result(devices, device_type, device_type_display)
            except Exception as e:
                import traceback
                traceback.print_exc()
                dialog.show_result([], device_type, device_type_display)
                self.controller.show_toast(f"检测设备出错: {str(e)}", "error")

        # 启动检测线程
        threading.Thread(target=detect_thread, daemon=True).start()
        
        # 显示对话框
        dialog.exec()

    def disconnect_device(self):
        """
        断开设备连接
        
        断开当前设备连接并更新UI状态。
        """
        self.task_manager.disconnect_device()
        self._update_connection_status_gui(False)
        self.controller.show_toast("设备已断开", "info")
        logger.info("设备已断开连接")

    def _update_connection_status_gui(self, connected):
        """更新连接状态显示 - 线程安全"""
        self.update_status_signal.emit(connected)

    def _do_update_connection_status(self, connected):
        """在GUI线程中更新连接状态"""
        connection_indicator = self.view.get_component("connection_indicator")

        if connected:
            if connection_indicator:
                connection_indicator.setText("● 已连接")
                connection_indicator.setStyleSheet(f"""
                    color: {ThemeColors.STATUS_ACTIVE}; 
                    background: transparent;
                    padding: {DialogStyle.STATUS_INDICATOR_PADDING};
                    border-radius: 4px;
                    font-weight: 500;
                """)
        else:
            if connection_indicator:
                connection_indicator.setText("● 未连接")
                connection_indicator.setStyleSheet(f"""
                    color: {ThemeColors.STATUS_INACTIVE}; 
                    background: transparent;
                    padding: {DialogStyle.STATUS_INDICATOR_PADDING};
                    border-radius: 4px;
                """)

        # 更新连接页面状态
        conn_status_label = self.view.get_component("connection_status_label")
        if conn_status_label:
            if connected:
                conn_status_label.setText("● 已连接")
                conn_status_label.setStyleSheet(
                    f"color: {ThemeColors.STATUS_ACTIVE}; "
                    f"font-size: {DialogStyle.CONNECTION_STATUS_FONT_SIZE}px; "
                    f"font-weight: bold; background: transparent;"
                )
            else:
                conn_status_label.setText("● 未连接")
                conn_status_label.setStyleSheet(
                    f"color: {ThemeColors.STATUS_INACTIVE}; "
                    f"font-size: {DialogStyle.CONNECTION_STATUS_FONT_SIZE}px; "
                    f"font-weight: bold; background: transparent;"
                )

        # 清空第二行
        conn_info_label = self.view.get_component("connection_info_label")
        if conn_info_label:
            conn_info_label.setText("")

    def show_scrcpy_popup(self):
        """显示投屏设置弹窗"""
        dialog = QDialog(self.view)
        dialog.setWindowTitle("📱 手机投屏")
        dialog.setFixedSize(DialogStyle.DIALOG_WIDTH_SMALL, DialogStyle.DIALOG_HEIGHT_SMALL)
        dialog.setModal(True)
        dialog.setStyleSheet(get_dialog_stylesheet())

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        layout.setSpacing(DialogStyle.DIALOG_SPACING)

        # 标题
        title_label = QLabel("📱 手机投屏设置")
        title_label.setFont(ThemeFonts.TITLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; background: transparent; border: none;")
        layout.addWidget(title_label)

        # 设备选择区域
        device_frame = QFrame()
        device_frame.setStyleSheet(get_dialog_card_stylesheet())
        device_layout = QVBoxLayout(device_frame)
        device_layout.setContentsMargins(
            DialogStyle.CONTENT_MARGIN, 
            DialogStyle.CONTENT_MARGIN, 
            DialogStyle.CONTENT_MARGIN, 
            DialogStyle.CONTENT_MARGIN
        )
        device_layout.setSpacing(DialogStyle.DEVICE_LAYOUT_SPACING)

        device_label = QLabel("选择设备:")
        device_label.setFont(ThemeFonts.BODY_MEDIUM)
        device_label.setStyleSheet(f"color: {ThemeColors.TEXT_PRIMARY}; background: transparent; border: none;")
        device_layout.addWidget(device_label)

        # 获取可用设备列表
        devices = self.task_manager.detect_devices()

        if devices:
            device_combo = QComboBox()
            device_combo.setFont(ThemeFonts.BODY_MEDIUM)
            device_combo.setStyleSheet(get_dialog_combobox_stylesheet())
            device_combo.addItems(devices)
            device_layout.addWidget(device_combo)
        else:
            no_device_label = QLabel("⚠️ 未检测到可用设备")
            no_device_label.setFont(ThemeFonts.BODY_MEDIUM)
            no_device_label.setStyleSheet(f"color: {ThemeColors.WARNING}; background: transparent; border: none;")
            device_layout.addWidget(no_device_label)
            device_combo = None

        layout.addWidget(device_frame)

        # 窗口置顶勾选框
        always_on_top_check = QCheckBox("窗口置顶")
        always_on_top_check.setFont(ThemeFonts.BODY_MEDIUM)
        always_on_top_check.setStyleSheet(get_dialog_checkbox_stylesheet())
        layout.addWidget(always_on_top_check)

        # 启动按钮
        def start_scrcpy():
            if not devices:
                self.controller.show_toast("没有可用设备", "warning")
                return

            if not device_combo:
                self.controller.show_toast("请选择一个设备", "warning")
                return

            selected_device = device_combo.currentText()
            if not selected_device:
                self.controller.show_toast("请选择一个设备", "warning")
                return

            try:
                safe_device = sanitize_device_id(selected_device)
            except ValueError as e:
                self.controller.show_toast(f"设备ID无效: {str(e)}", "error")
                return

            cmd = [str(self.controller.scrcpy_path), "--stay-awake"]
            cmd.append("-s")
            cmd.append(safe_device)

            if always_on_top_check.isChecked():
                cmd.append("--always-on-top")

            try:
                def run_scrcpy():
                    try:
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        self.controller.active_subprocesses.append(process)
                        self.controller.show_toast(f"手机投屏已启动 ({safe_device})", "success")
                        process.wait()
                        if process in self.controller.active_subprocesses:
                            self.controller.active_subprocesses.remove(process)
                    except Exception as e:
                        print(f"启动scrcpy失败: {e}")
                        self.controller.show_toast(f"启动失败: {str(e)}", "error")

                threading.Thread(target=run_scrcpy, daemon=True).start()
                dialog.accept()

            except Exception as e:
                self.controller.show_toast(f"启动失败: {str(e)}", "error")

        start_button = QPushButton("启动投屏")
        start_button.setFont(ThemeFonts.BODY_MEDIUM)
        start_button.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
        start_button.setFixedWidth(DialogStyle.BUTTON_WIDTH)
        start_button.setStyleSheet(get_dialog_button_stylesheet("accent"))
        start_button.clicked.connect(start_scrcpy)
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # 提示信息
        info_label = QLabel("注意：请确保手机已开启USB调试模式\n点击其他地方时窗口会自动最小化")
        info_label.setFont(ThemeFonts.BODY_XSMALL)
        info_label.setStyleSheet(f"color: {ThemeColors.TEXT_SECONDARY}; background: transparent; border: none;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        dialog.exec()

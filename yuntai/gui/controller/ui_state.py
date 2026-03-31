"""
UI 状态管理 Mixin
================

UIStateMixin 包含按钮状态管理、提示消息、TTS指示器更新等 UI 状态相关功能。
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

# 项目模块
from yuntai.gui.styles import ThemeColors


class UIStateMixin:
    """
    UI 状态管理 Mixin

    包含按钮状态管理、提示消息、TTS指示器更新等 UI 状态相关功能。
    通过 self 属性访问 ControllerCore 中初始化的实例变量。
    """

    # ============ 提示消息 ============

    def show_toast(self, message: str, msg_type: str = "info"):
        """
        显示提示消息

        Args:
            message: 消息内容
            msg_type: 消息类型（info/success/warning/error）
        """
        if hasattr(self.view, 'toast_widget'):
            self.view.toast_widget.show_toast(message, msg_type, duration=2000)

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
            logger.error("清理文件失败: %s", str(e))
            print(f"❌ 清理文件失败: {e}")

    # ============ TTS 指示器更新 ============

    def update_tts_indicator(self, enabled: bool):
        """
        更新TTS指示器状态

        Args:
            enabled: 是否启用
        """
        logger.debug("更新 TTS 指示器: %s", enabled)

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

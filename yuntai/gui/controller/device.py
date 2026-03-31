"""
设备管理 Mixin
=============

DeviceMixin 包含设备类型切换、快捷键处理等设备相关功能。
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
from yuntai.core.config import SHORTCUTS


class DeviceMixin:
    """
    设备管理 Mixin

    包含设备类型切换、快捷键处理等设备相关功能。
    通过 self 属性访问 ControllerCore 中初始化的实例变量。
    """

    # ============ 设备类型回调 ============

    def _on_device_type_changed(self, device_type: str):
        """
        设备类型改变时的回调

        Args:
            device_type: 新的设备类型
        """
        logger.info("设备类型改变: %s", device_type)
        if "HarmonyOS" in device_type or "HDC" in device_type:
            self.device_type = "harmonyos"
        else:
            self.device_type = "android"
        self.show_toast(f"已切换到 {device_type}", "info")

    # ============ 快捷键处理 ============

    def execute_shortcut(self, shortcut_key):
        """
        执行快捷键对应的应用打开命令

        Args:
            shortcut_key: 快捷键
        """
        logger.debug("执行快捷键: %s", shortcut_key)

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

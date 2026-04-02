"""
文件操作 Mixin
=============

FileOpsMixin 包含文件上传、附件管理、多模态聊天历史记录等文件相关功能。
"""
import sys
import logging
import threading
import queue
import time
import datetime
import traceback
from typing import Any
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# 项目模块
from yuntai.core.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE, SCRCPY_PATH, validate_config, print_config_summary,
    ZHIPU_CHAT_MODEL, ZHIPU_MODEL, ZHIPU_API_BASE_URL
)


class FileOpsMixin:
    """
    文件操作 Mixin

    包含文件上传、附件管理、多模态聊天历史记录等文件相关功能。
    通过 self 属性访问 ControllerCore 中初始化的实例变量。
    """

    # ============ 文件上传与附件管理 ============

    def show_file_upload(self):
        """显示文件上传对话框"""
        logger.debug("显示文件上传对话框")

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
                        file_name = Path(file_path).name
                        error_messages.append(f"{file_name}: {reason}")

                if valid_files:
                    self.attached_files.extend(valid_files)
                    self.view.show_attached_files(self.attached_files, self)
                    self.show_toast(f"已添加 {len(valid_files)} 个文件", "success")
                    logger.info("添加 %d 个文件", len(valid_files))

                if error_messages:
                    error_count = len(error_messages)
                    if error_count <= 3:
                        for msg in error_messages:
                            self.show_toast(msg, "warning")
                    else:
                        self.show_toast(f"跳过 {error_count} 个不支持的文件", "warning")

        except Exception as e:
            logger.error("文件选择失败: %s", str(e))
            self.show_toast(f"文件选择失败: {str(e)}", "error")

    def _check_file_supported(self, file_path: str) -> tuple[bool, str]:
        """
        检查文件是否支持

        Args:
            file_path: 文件路径

        Returns:
            tuple[bool, str]: (是否支持, 原因)
        """
        if not self.multimodal_processor:
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            self.multimodal_processor = MultimodalProcessor()

        file = Path(file_path)
        if not file.exists():
            return False, "文件不存在"
        if not self.multimodal_processor.is_file_supported(file_path):
            ext = file.suffix.lower()
            return False, f"不支持的文件类型: {ext}"

        size_ok, msg = self.multimodal_processor.check_file_size(file_path)
        if not size_ok:
            return False, f"文件过大: {msg}"
        return True, ""

    def clear_attached_files(self):
        """清空已选文件列表"""
        logger.debug("清空已选文件列表")

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
        """
        移除单个文件

        Args:
            file_path: 要移除的文件路径
        """
        logger.debug("移除文件: %s", file_path)

        if self.is_executing:
            self.show_toast("任务执行中，请等待完成", "warning")
            return
        if file_path in self.attached_files:
            self.attached_files.remove(file_path)
            if self.view:
                self.view.show_attached_files(self.attached_files, self)
            self.show_toast(f"已移除: {Path(file_path).name}", "info")

    # ============ 多模态聊天辅助方法 ============

    def _get_chat_history_for_multimodal(self) -> list:
        """
        获取多模态聊天的历史记录

        Returns:
            历史消息列表
        """
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
            logger.warning("获取历史记录失败: %s", str(e))
            return []

    def _save_multimodal_chat_history(self, text: str, file_paths: list, reply: str):
        """
        保存多模态聊天历史

        Args:
            text: 文本内容
            file_paths: 文件路径列表
            reply: 回复内容
        """
        try:
            file_names = [Path(f).name for f in file_paths]
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
            logger.warning("保存聊天历史失败: %s", str(e))

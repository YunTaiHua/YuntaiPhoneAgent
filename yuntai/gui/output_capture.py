"""
输出捕获模块 - v6 (主题自适应版)
================================

负责将终端输出同步到GUI显示，支持主题自适应。

主要功能:
    - 捕获标准输出和标准错误
    - 同步输出到GUI文本控件
    - 支持特定文本彩色高亮显示（如"对话开始"）
    - 浅色主题使用紫色高亮，深色主题使用金色高亮

特性说明:
    - TTS冗余输出已在gpt_sovits_custom模块中被移除
    - 此模块仅负责将终端输出同步到GUI
    - 无需复杂的过滤逻辑

使用示例:
    >>> capture = SimpleOutputCapture(text_widget, is_dark_theme=False)
    >>> capture.set_dark_theme(True)  # 切换到深色主题
    >>> capture.restore()  # 恢复原始输出流
"""

import logging
import sys
import re
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QFont

# 初始化模块日志记录器
logger = logging.getLogger(__name__)


class SimpleOutputCapture(QObject):
    """
    简化的输出捕获类 - 同步终端输出到GUI
    
    捕获标准输出和标准错误，通过信号槽机制安全地更新GUI文本控件。
    支持"对话开始"标记的彩色高亮显示。
    
    Attributes:
        text_widget: 目标文本控件
        is_dark_theme: 是否使用深色主题
        original_stdout: 原始标准输出流
        original_stderr: 原始标准错误流
        text_updated: 文本更新信号
    
    类常量:
        LIGHT_THEME_COLOR: 浅色主题高亮颜色（紫色）
        DARK_THEME_COLOR: 深色主题高亮颜色（金色）
    """

    # 定义信号用于线程安全的GUI更新
    text_updated = pyqtSignal(str)

    # 主题颜色常量
    LIGHT_THEME_COLOR = "#8B5CF6"  # 浅色主题：紫色
    DARK_THEME_COLOR = "#FFD700"   # 深色主题：金色

    def __init__(self, text_widget=None, is_dark_theme=False):
        """
        初始化输出捕获器
        
        Args:
            text_widget: 目标文本控件（QTextEdit）
            is_dark_theme: 是否使用深色主题，默认False
        """
        super().__init__()
        self.text_widget = text_widget
        self.is_dark_theme = is_dark_theme
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        logger.debug("SimpleOutputCapture初始化完成")

        # 连接信号到槽函数
        self.text_updated.connect(self._safe_update_text)

        class CustomStream:
            def __init__(self, capture, is_stdout=True):
                self.capture = capture
                self.is_stdout = is_stdout

            def write(self, text):
                if not text:
                    return 0

                # 输出到终端
                if self.is_stdout:
                    self.capture.original_stdout.write(text)
                else:
                    self.capture.original_stderr.write(text)

                # 同步到GUI（保留所有文本，包括空行）
                if self.capture.text_widget:
                    self.capture.text_updated.emit(text)

                return len(text)

            def flush(self):
                if self.is_stdout:
                    self.capture.original_stdout.flush()
                else:
                    self.capture.original_stderr.flush()

        self.custom_stdout = CustomStream(self, is_stdout=True)
        self.custom_stderr = CustomStream(self, is_stdout=False)

        sys.stdout = self.custom_stdout
        sys.stderr = self.custom_stderr

    def _safe_update_text(self, text):
        """
        安全更新文本控件（通过信号槽机制确保线程安全）
        
        Args:
            text: 要显示的文本内容
        """
        if not self.text_widget:
            return

        try:
            # PyQt6 QTextEdit 操作
            self.text_widget.setReadOnly(False)
            
            # 检测是否包含"对话开始"标记，添加高亮
            if "对话开始" in text:
                self._insert_highlighted_text(text)
            else:
                self.text_widget.insertPlainText(text)
            
            # 滚动到底部
            scrollbar = self.text_widget.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())
            self.text_widget.setReadOnly(True)
        except Exception:
            pass
    
    def _insert_highlighted_text(self, text):
        """
        插入彩色字体文本（对话开始标记）- 根据主题选择颜色
        
        匹配格式: ═════════ [2026-03-05 09:03:19 对话开始] ═════════
        
        Args:
            text: 要处理的文本内容
        """
        cursor = self.text_widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        # 根据主题选择颜色
        color = self.DARK_THEME_COLOR if self.is_dark_theme else self.LIGHT_THEME_COLOR

        # 定义彩色字体格式
        highlight_format = QTextCharFormat()
        highlight_format.setForeground(QColor(color))
        highlight_format.setFontWeight(QFont.Weight.Bold)  # 粗体
        
        # 定义普通格式
        normal_format = QTextCharFormat()
        
        # 匹配模式：═════════ [2026-03-05 09:03:19 对话开始] ═════════
        pattern = r'(═+\s*\[.*?对话开始.*?\]\s*═+)'
        
        last_end = 0
        for match in re.finditer(pattern, text):
            # 插入匹配前的普通文本
            if match.start() > last_end:
                cursor.insertText(text[last_end:match.start()], normal_format)
            
            # 插入高亮的匹配文本
            cursor.insertText(match.group(1), highlight_format)
            last_end = match.end()
        
        # 插入剩余的普通文本
        if last_end < len(text):
            cursor.insertText(text[last_end:], normal_format)

    def set_text_widget(self, text_widget):
        """
        设置文本控件
        
        Args:
            text_widget: 目标文本控件（QTextEdit）
        """
        self.text_widget = text_widget

    def set_dark_theme(self, is_dark_theme: bool):
        """
        设置主题状态
        
        Args:
            is_dark_theme: 是否使用深色主题
        """
        self.is_dark_theme = is_dark_theme
        logger.debug("输出捕获主题切换: %s", '深色' if is_dark_theme else '浅色')

    def restore(self):
        """
        恢复原来的stdout和stderr
        
        将标准输出和标准错误恢复到原始流，
        应在不再需要捕获输出时调用。
        """
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        logger.debug("输出流已恢复")

    def write(self, string):
        """写入方法，用于兼容"""
        return self.custom_stdout.write(string)

    def flush(self):
        """刷新方法"""
        self.custom_stdout.flush()

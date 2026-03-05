"""
输出捕获模块 - v5 (高亮版)
- TTS冗余输出已在gpt_sovits_custom模块中被移除
- 此模块仅负责将终端输出同步到GUI
- 无需复杂的过滤逻辑
- 支持特定文本高亮显示（如"对话开始"）
"""

import sys
import re
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QFont


class SimpleOutputCapture(QObject):
    """简化的输出捕获类：仅同步终端输出到GUI"""

    # 定义信号用于线程安全的GUI更新
    text_updated = pyqtSignal(str)

    def __init__(self, text_widget=None):
        super().__init__()
        self.text_widget = text_widget
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

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
        """安全更新文本控件（通过信号槽机制确保线程安全）"""
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
        """插入高亮文本（对话开始标记）"""
        cursor = self.text_widget.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # 定义高亮格式
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFD700"))  # 金黄色背景
        highlight_format.setForeground(QColor("#000000"))  # 黑色文字
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
        """设置文本控件"""
        self.text_widget = text_widget

    def restore(self):
        """恢复原来的stdout和stderr"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def write(self, string):
        """写入方法，用于兼容"""
        return self.custom_stdout.write(string)

    def flush(self):
        """刷新方法"""
        self.custom_stdout.flush()

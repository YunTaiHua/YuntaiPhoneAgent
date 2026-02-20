"""
输出捕获模块 - v3
- 终端：保持原始输出，不做任何过滤
- GUI：过滤TTS冗余输出 + 格式化换行
"""

import sys
import re
from contextlib import contextmanager


class SimpleOutputCapture:
    """输出捕获类：终端保持原样，GUI过滤TTS冗余输出"""

    def __init__(self, text_widget=None):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.in_tts_block = False

        class CustomStream:
            def __init__(self, capture, is_stdout=True):
                self.capture = capture
                self.is_stdout = is_stdout

            def write(self, text):
                if not text:
                    return 0

                if self.is_stdout:
                    self.capture.original_stdout.write(text)
                else:
                    self.capture.original_stderr.write(text)

                if self.capture.text_widget:
                    gui_text = self.capture._filter_for_gui(text)
                    if gui_text:
                        self.capture.text_widget.after(
                            0, self.capture._safe_update_text, gui_text
                        )

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

    def _filter_for_gui(self, text: str) -> str:
        """过滤TTS冗余输出，仅用于GUI"""
        if not text or not isinstance(text, str):
            return ""

        stripped = text.strip()

        progress_patterns = [
            r'^\s*\d+%\|',
            r'\[\d+:\d+<\d+:\d+',
            r'\d+\.?\d*it/s\]',
        ]
        for pattern in progress_patterns:
            if re.search(pattern, stripped):
                return ""

        tts_markers = [
            "实际输入的参考文本:",
            "实际输入的目标文本:",
            "实际输入的目标文本(切句后):",
            "实际输入的目标文本(每句):",
            "前端处理后的文本(每句):",
            "Skip loading CUDA",
            "更多东西被纳入可重塑的范畴",
            "libpng warning:",
        ]
        for marker in tts_markers:
            if marker in text:
                self.in_tts_block = True
                return ""

        if self.in_tts_block:
            tts_block_patterns = [
                r"^\['[^\]]+'\]$",
                r"^WARNING:",
                r"^loading sovits",
                r"^All keys matched",
            ]
            for pattern in tts_block_patterns:
                if re.search(pattern, stripped):
                    return ""

            if re.match(r'^\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+', stripped):
                self.in_tts_block = False
                return ""

            if stripped.endswith(']'):
                self.in_tts_block = False
                return ""

            return ""

        tts_init_messages = [
            "✅ 音频播放器初始化成功",
            "🔍 初始化TTS文件数据库...",
            "📁 确保目录存在:",
            "✅ 文件数据库初始化完成:",
            "📦 预加载TTS模块...",
            "📦 正在加载TTS模块...",
            "✅ BERT模型路径已设置",
            "✅ HuBERT模型路径已设置",
            "📌 默认GPT模型:",
            "📌 默认SoVITS模型:",
            "✅ TTS模块加载成功",
            "✅ TTS模块预加载成功",
            "- GPT模型:",
            "- SoVITS模型:",
            "- 参考音频:",
            "- 参考文本:",
        ]
        for msg in tts_init_messages:
            if msg in text:
                return ""

        if stripped.startswith('[') and stripped.endswith(']'):
            return ""

        text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)

        return text

    @contextmanager
    def suppress_tts_output(self):
        """上下文管理器：复用主过滤逻辑"""
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        class SuppressStream:
            def __init__(self, capture, is_stdout=True):
                self.capture = capture
                self.is_stdout = is_stdout

            def write(self, text):
                if not text:
                    return 0

                if self.is_stdout:
                    self.capture.original_stdout.write(text)
                else:
                    self.capture.original_stderr.write(text)

                if self.capture.text_widget:
                    gui_text = self.capture._filter_for_gui(text)
                    if gui_text:
                        self.capture.text_widget.after(
                            0, self.capture._safe_update_text, gui_text
                        )

                return len(text)

            def flush(self):
                pass

        sys.stdout = SuppressStream(self, is_stdout=True)
        sys.stderr = SuppressStream(self, is_stdout=False)

        try:
            yield
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    def _safe_update_text(self, text):
        """安全更新文本控件"""
        if not self.text_widget or not self.text_widget.winfo_exists():
            return

        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", text)
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except Exception:
            pass

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

"""
输出捕获模块 - 重构版
负责捕获、过滤和显示控制台输出，特别是思考过程和性能指标
"""

import sys
import re
import tkinter as tk
from contextlib import contextmanager
from typing import Optional, Callable, Any


class SimpleOutputCapture:
    """输出捕获类：过滤TTS冗余输出，同步更新GUI文本框和控制台"""

    def __init__(self, text_widget=None):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.in_tts_block = False  # 是否在TTS输出块中
        self.tts_block_content = []  # 存储TTS块内容（用于调试）

        # 创建自定义流
        class CustomStream:
            def __init__(self, capture, is_stdout=True):
                self.capture = capture
                self.is_stdout = is_stdout

            def write(self, text):
                if not text:
                    return 0

                # 处理文本，返回None表示完全过滤
                processed_text = self._process_tts_block(text)

                # 如果返回None，表示这是TTS块内的内容，完全过滤
                if processed_text is None:
                    return len(text)

                # 检查是否是空行或只有空白字符
                if not processed_text.strip():
                    return len(text)  # 不输出空行

                # 1. 输出到原来的stdout（PyCharm控制台）
                if self.is_stdout:
                    self.capture.original_stdout.write(text)
                else:
                    self.capture.original_stderr.write(text)

                # 2. 直接更新GUI文本
                if processed_text and self.capture.text_widget:
                    # 在主线程中更新GUI
                    self.capture.text_widget.after(0, self.capture._safe_update_text, processed_text)

                return len(text)

            def flush(self):
                if self.is_stdout:
                    self.capture.original_stdout.flush()
                else:
                    self.capture.original_stderr.flush()

            def _process_tts_block(self, text):
                """处理TTS输出块 - 修复版"""
                # 使用统一的处理函数
                return self.capture._process_tts_block_text(text, self.capture.in_tts_block)

        self.custom_stdout = CustomStream(self, is_stdout=True)
        self.custom_stderr = CustomStream(self, is_stdout=False)

        # 替换标准输出
        sys.stdout = self.custom_stdout
        sys.stderr = self.custom_stderr

    def _process_tts_block_text(self, text, in_tts_block):
        """统一的TTS文本处理函数"""
        if not text or not isinstance(text, str):
            return text

        # ==================== 1. 首先过滤需要完全删除的内容 ====================

        # 过滤进度条
        progress_patterns = [
            r'^\s*\d+%\|[^\[]*\[\d+:\d+<\d+:\d+,\s*\d+\.?\d*it/s\]',
            r'^\s*\d+%\|[^\[\]]*\| \d+/\d+',
            r'^\s*\d+%\|',
            r'\[\d+:\d+<\d+:\d+,\s*\d+\.?\d*it/s\]',
            r'^\s*#+\s*\d+',
            r'^\|\s*\d+/\d+\s+',
        ]

        for pattern in progress_patterns:
            if re.search(pattern, text.strip()):
                return None  # 完全过滤进度条

        # 过滤TTS块的开始
        tts_start_markers = [
            "实际输入的参考文本:",
            "实际输入的目标文本:",
            "实际输入的目标文本(切句后):",
            "实际输入的目标文本(每句):",
            "前端处理后的文本(每句):",
            "更多东西被纳入可重塑的范畴,你的付出很有成效.",
        ]

        for marker in tts_start_markers:
            if marker in text:
                self.in_tts_block = True
                return None  # 完全过滤

        # 如果在TTS块中
        if in_tts_block:
            tts_block_content = [
                "['更多东西被纳入可重塑的范畴你的付出很有成效']",
                "['zh']",
                "['嗨我们又见面啦",
                "WARNING: onnxruntime",
                "loading sovits_v2Pro",
                "All keys matched successfully",
            ]

            for content in tts_block_content:
                if content in text:
                    return None

            # 检查TTS块内的进度条
            for pattern in progress_patterns:
                if re.search(pattern, text):
                    return None

            # 检查TTS块结束标记
            if re.search(r'\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+\s+\d+\.\d+', text):
                self.in_tts_block = False
                return None

            if re.search(r'\d+\.\d+\t\d+\.\d+\t\d+\.\d+\t\d+\.\d+', text):
                self.in_tts_block = False
                return None

            if text.strip().endswith(']'):
                self.in_tts_block = False
                return None

            return None  # 仍在TTS块中，过滤

        # ==================== 2. 过滤需要替换为空的内容 ====================

        tts_init = [
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

        for pattern in tts_init:
            if pattern in text:
                return ""

        # 过滤重复的AI回复（没有标点的版本）
        if "小芸" in text:
            if text.startswith("嘿嘿") or text.startswith("嗨") or text.startswith("呀"):
                if not any(c in text for c in "，。！？"):
                    return ""

        # 过滤方括号内容
        stripped = text.strip()
        if stripped.startswith('[') and stripped.endswith(']'):
            return ""

        # ==================== 3. 处理格式（在确定要返回内容后） ====================

        # 过滤ANSI颜色代码
        text = re.sub(r'\x1b\[[0-9;]*[mK]', '', text)

        # 保留纯换行符（这个检查要放在前面）
        if not text.strip() and text == '\n':
            return text

        # ==================== 4. 修复特定的格式问题 ====================

        # 修复虚线分隔线：在 -------------------------------------------------- 后面加换行符
        if "--------------------------------------------------" in text:
            # 如果虚线后面没有换行符，就加一个
            if not text.endswith('\n'):
                text = text + '\n'
            # 确保虚线前面也有换行符（如果是单独一行）
            if not text.startswith('\n') and text.strip() == "--------------------------------------------------":
                text = '\n' + text
            return text

        # 修复性能指标格式
        # 1. 在 "首 Token 延迟 (TTFT):" 前面加换行符
        if "首 Token 延迟 (TTFT):" in text:
            if not text.startswith('\n'):
                text = '\n' + text

        # 2. 在 "思考完成延迟:" 前面加换行符
        elif "思考完成延迟:" in text:
            if not text.startswith('\n'):
                text = '\n' + text

        # 3. 在 "总推理时间:" 前面加换行符
        elif "总推理时间:" in text:
            if not text.startswith('\n'):
                text = '\n' + text + '\n'

        # 修复思考过程格式
        if "=" * 50 in text:
            # 确保分隔线有换行
            if not text.startswith('\n'):
                text = '\n' + text
            if not text.endswith('\n'):
                text = text + '\n'
            return text

        # 修复思考过程标题
        if "💭 思考过程:" in text or "⏱️  性能指标:" in text:
            # 确保标题有换行
            if not text.startswith('\n'):
                text = '\n' + text
            if not text.endswith('\n'):
                text = text + '\n'
            return text

        return text

    @contextmanager
    def suppress_tts_output(self):
        """上下文管理器：在TTS合成期间完全抑制所有输出"""
        # 保存原始输出流
        original_stdout = sys.stdout
        original_stderr = sys.stderr

        # 创建完全丢弃输出的流
        class NullWriter:
            def __init__(self, capture, is_stdout=True):
                self.capture = capture
                self.is_stdout = is_stdout

            def write(self, text):
                if not text:
                    return 0

                # 处理文本，返回None表示完全过滤
                processed_text = self._process_tts_block(text)

                # 如果返回None，表示这是TTS块内的内容，完全过滤
                if processed_text is None:
                    return len(text)

                # 检查是否是空行或只有空白字符
                if not processed_text.strip():
                    # 保留换行符
                    if '\n' in text:
                        processed_text = '\n'
                    else:
                        return len(text)

                # 1. 输出到原来的stdout（PyCharm控制台）
                if self.is_stdout:
                    self.capture.original_stdout.write(text)
                else:
                    self.capture.original_stderr.write(text)

                # 2. 直接更新GUI文本
                if processed_text and self.capture.text_widget:
                    # 确保添加换行
                    if not processed_text.endswith('\n') and '\n' not in processed_text:
                        processed_text = processed_text + '\n'

                    # 在主线程中更新GUI
                    self.capture.text_widget.after(0, self.capture._safe_update_text, processed_text)

                return len(text)

            def flush(self):
                pass

            def _process_tts_block(self, text):
                """处理TTS输出块 - 修复版"""
                # 使用统一的处理函数
                return self.capture._process_tts_block_text(text, self.capture.in_tts_block)

        null_writer_stdout = NullWriter(self, is_stdout=True)
        null_writer_stderr = NullWriter(self, is_stdout=False)

        # 重定向输出
        sys.stdout = null_writer_stdout
        sys.stderr = null_writer_stderr

        try:
            yield
        finally:
            # 恢复输出
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
            # 如果出错，忽略
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
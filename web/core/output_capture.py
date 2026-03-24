"""
output_capture.py - Web端输出捕获类
将终端输出同步到WebSocket
"""

from __future__ import annotations

import sys
import asyncio
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from .controller import WebController


class WebOutputCapture:
    """Web端输出捕获类 - 将终端输出同步到WebSocket"""

    def __init__(self, controller: WebController) -> None:
        self.controller = controller
        self.original_stdout: TextIO = sys.stdout
        self.original_stderr: TextIO = sys.stderr
        self._loop: asyncio.AbstractEventLoop | None = None
        self._enabled: bool = False
        self.custom_stdout: CustomStream
        self.custom_stderr: CustomStream

        self.custom_stdout = CustomStream(self, is_stdout=True)
        self.custom_stderr = CustomStream(self, is_stdout=False)

    def start_capture(self, loop: asyncio.AbstractEventLoop) -> None:
        """开始捕获输出"""
        self._loop = loop
        self._enabled = True
        sys.stdout = self.custom_stdout
        sys.stderr = self.custom_stderr

    def stop_capture(self) -> None:
        """停止捕获输出"""
        self._enabled = False
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class CustomStream:
    """自定义输出流，用于捕获并转发输出"""

    def __init__(self, capture: WebOutputCapture, is_stdout: bool = True) -> None:
        self.capture = capture
        self.is_stdout: bool = is_stdout

    def write(self, text: str) -> int:
        """写入文本并转发到WebSocket"""
        if not text:
            return 0

        if self.is_stdout:
            self.capture.original_stdout.write(text)
        else:
            self.capture.original_stderr.write(text)

        if self.capture._enabled and self.capture._loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.capture.controller.ws_manager.broadcast({
                        "type": "agent_output",
                        "message": text
                    }),
                    self.capture._loop
                )
            except Exception:
                pass

        return len(text)

    def flush(self) -> None:
        """刷新缓冲区"""
        if self.is_stdout:
            self.capture.original_stdout.flush()
        else:
            self.capture.original_stderr.flush()

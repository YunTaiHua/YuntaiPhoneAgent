"""
Web 端输出捕获模块
==================

将终端输出同步到 WebSocket，实现前后端输出同步。

主要组件:
    - WebOutputCapture: Web 端输出捕获类
    - CustomStream: 自定义输出流

功能特点:
    - 捕获 stdout 和 stderr
    - 异步转发到 WebSocket
    - 保持原始终端输出
"""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from .controller import WebController

logger = logging.getLogger(__name__)


class WebOutputCapture:
    """
    Web 端输出捕获类
    
    将终端输出同步到 WebSocket，实现前后端输出同步。
    
    Attributes:
        controller: WebController 实例
        original_stdout: 原始的标准输出
        original_stderr: 原始的标准错误输出
        custom_stdout: 自定义标准输出流
        custom_stderr: 自定义标准错误流
        
    Args:
        controller: WebController 实例
    """
    
    def __init__(self, controller: WebController) -> None:
        """
        初始化输出捕获器
        
        Args:
            controller: WebController 实例
        """
        self.controller = controller
        self.original_stdout: TextIO = sys.stdout
        self.original_stderr: TextIO = sys.stderr
        self._loop: asyncio.AbstractEventLoop | None = None
        self._enabled: bool = False

        self.custom_stdout = CustomStream(self, is_stdout=True)
        self.custom_stderr = CustomStream(self, is_stdout=False)
        logger.debug("WebOutputCapture 初始化完成")

    def start_capture(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        开始捕获输出
        
        替换 sys.stdout 和 sys.stderr 为自定义流。
        
        Args:
            loop: asyncio 事件循环
        """
        self._loop = loop
        self._enabled = True
        sys.stdout = self.custom_stdout
        sys.stderr = self.custom_stderr
        logger.debug("开始捕获输出")

    def stop_capture(self) -> None:
        """停止捕获输出，恢复原始输出流"""
        self._enabled = False
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        logger.debug("停止捕获输出")


class CustomStream:
    """
    自定义输出流
    
    用于捕获并转发输出到 WebSocket。
    
    Attributes:
        capture: WebOutputCapture 实例
        is_stdout: 是否为标准输出
    """
    
    def __init__(self, capture: WebOutputCapture, is_stdout: bool = True) -> None:
        """
        初始化自定义输出流
        
        Args:
            capture: WebOutputCapture 实例
            is_stdout: 是否为标准输出，默认为 True
        """
        self.capture = capture
        self.is_stdout: bool = is_stdout

    def write(self, text: str) -> int:
        """
        写入文本并转发到 WebSocket
        
        同时输出到原始流和 WebSocket。
        
        Args:
            text: 要写入的文本
            
        Returns:
            写入的字符数
        """
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

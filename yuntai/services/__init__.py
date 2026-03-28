"""
服务模块
========

本模块提供核心服务功能，包括连接管理、文件管理和任务管理。

主要组件:
    - ConnectionManager: 设备连接管理器
    - FileManager: 文件管理器
    - TaskManager: 任务管理器
    - TTSManager: TTS 语音合成管理器

功能特点:
    - 支持 USB 和无线调试两种连接方式
    - 兼容 Android (ADB) 和 HarmonyOS (HDC) 设备
    - 管理对话历史、永久记忆等文件
    - 集成 TTS 语音合成功能
"""
import logging

logger = logging.getLogger(__name__)

from .connection_manager import ConnectionManager
from .file_manager import FileManager
from .task_manager import TaskManager, TTSManager

__all__ = [
    'ConnectionManager',
    'FileManager',
    'TaskManager',
    'TTSManager',
]

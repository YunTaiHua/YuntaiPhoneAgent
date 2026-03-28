"""
Handlers 处理器模块
===================

本模块提供 GUI 控制器的各个功能处理器，分离业务逻辑以提高代码可维护性。

模块包含以下处理器：
    - ConnectionHandler: 设备连接处理器，处理设备连接、断开、状态管理
    - TTSHandler: TTS 语音合成处理器，处理语音合成相关功能
    - DynamicHandler: 动态功能处理器，处理图像/视频生成功能
    - SystemHandler: 系统管理处理器，处理历史记录、系统设置和文件管理

使用示例：
    >>> from yuntai.handlers import ConnectionHandler, TTSHandler
    >>> 
    >>> # 创建处理器
    >>> connection_handler = ConnectionHandler(controller)
    >>> tts_handler = TTSHandler(controller)
"""

from .connection_handler import ConnectionHandler
from .tts_handler import TTSHandler
from .dynamic_handler import DynamicHandler
from .system_handler import SystemHandler

# 模块公开接口
__all__ = [
    "ConnectionHandler",
    "TTSHandler",
    "DynamicHandler",
    "SystemHandler",
]

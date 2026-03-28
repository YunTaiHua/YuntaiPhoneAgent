"""
LangChain Callbacks 模块
========================

本模块提供自定义的回调处理器，用于流式输出、日志记录、性能监控等。

主要功能：
    - 流式输出：实时捕获 LLM 生成的 token 并输出
    - 日志记录：记录 LLM 调用、Chain 执行、Tool 调用等过程
    - 性能监控：监控各组件的执行时间和性能指标
    - 记忆管理：自动记录对话历史到记忆系统

类说明：
    - StreamingCallbackHandler: 基础流式输出处理器
    - QtStreamingCallbackHandler: PyQt GUI 专用流式输出处理器
    - AsyncStreamingCallbackHandler: 异步流式输出处理器
    - LoggingCallbackHandler: 日志记录处理器
    - PerformanceCallbackHandler: 性能监控处理器
    - MemoryCallbackHandler: 记忆管理处理器
    - SessionMemoryCallbackHandler: 会话记忆处理器
    - FileBasedMemoryCallbackHandler: 基于文件的记忆处理器
    - CallbackManager: 回调管理器，统一管理所有处理器

使用示例：
    >>> from yuntai.callbacks import CallbackManager, StreamingCallbackHandler
    >>> 
    >>> # 创建回调管理器
    >>> manager = CallbackManager()
    >>> 
    >>> # 创建流式输出处理器
    >>> handler = manager.create_streaming_handler(
    ...     output_callback=lambda token: print(token, end='')
    ... )
"""

from yuntai.callbacks.streaming_handler import (
    StreamingCallbackHandler,
    QtStreamingCallbackHandler,
    AsyncStreamingCallbackHandler
)
from yuntai.callbacks.logging_handler import (
    LoggingCallbackHandler,
    PerformanceCallbackHandler
)
from yuntai.callbacks.memory_handler import (
    MemoryCallbackHandler,
    SessionMemoryCallbackHandler,
    FileBasedMemoryCallbackHandler
)
from yuntai.callbacks.callback_manager import (
    CallbackManager,
    get_callback_manager,
    reset_callback_manager
)

# 模块公开接口
__all__ = [
    # 流式输出处理器
    "StreamingCallbackHandler",
    "QtStreamingCallbackHandler",
    "AsyncStreamingCallbackHandler",
    # 日志记录处理器
    "LoggingCallbackHandler",
    "PerformanceCallbackHandler",
    # 记忆管理处理器
    "MemoryCallbackHandler",
    "SessionMemoryCallbackHandler",
    "FileBasedMemoryCallbackHandler",
    # 回调管理器
    "CallbackManager",
    "get_callback_manager",
    "reset_callback_manager",
]

"""
回调管理器模块
==============

本模块实现回调管理器，统一管理所有回调处理器，提供便捷的配置和使用接口。

主要功能：
    - 处理器注册：注册和管理各类回调处理器
    - 快捷创建：提供快捷方法创建各类处理器
    - 回调配置：生成用于 invoke 调用的回调配置
    - 统计摘要：打印处理器的统计信息

类说明：
    - CallbackManager: 回调管理器类

函数说明：
    - get_callback_manager: 获取全局回调管理器单例
    - reset_callback_manager: 重置全局回调管理器

使用示例：
    >>> from yuntai.callbacks import get_callback_manager
    >>> 
    >>> # 获取回调管理器
    >>> manager = get_callback_manager()
    >>> 
    >>> # 创建流式输出处理器
    >>> handler = manager.create_streaming_handler(
    ...     output_callback=lambda token: print(token, end='')
    ... )
    >>> 
    >>> # 获取回调配置
    >>> config = manager.get_callbacks_for_invoke()
"""
import logging
from collections.abc import Callable

from langchain_core.callbacks import BaseCallbackHandler

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

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class CallbackManager:
    """
    回调管理器
    
    统一管理所有回调处理器，提供便捷的配置和使用接口。
    支持处理器的注册、注销、快捷创建和统计摘要。
    
    Attributes:
        _handlers: 处理器字典，键为名称，值为处理器实例
        _global_handlers: 全局处理器列表
    
    使用示例：
        >>> manager = CallbackManager()
        >>> handler = manager.create_streaming_handler("my_streaming")
        >>> callbacks = manager.get_callbacks()
    """

    def __init__(self) -> None:
        """
        初始化回调管理器
        
        创建空的处理器字典和全局处理器列表。
        """
        # 处理器字典：{name: handler}
        self._handlers: dict[str, BaseCallbackHandler] = {}
        # 全局处理器列表
        self._global_handlers: list[BaseCallbackHandler] = []
        
        logger.debug("CallbackManager 初始化完成")

    # ==================== 处理器注册 ====================

    def register_handler(
        self,
        name: str,
        handler: BaseCallbackHandler,
        is_global: bool = False
    ) -> None:
        """
        注册回调处理器
        
        将处理器注册到管理器，可选择是否设为全局处理器。
        
        Args:
            name: 处理器名称，用于后续获取
            handler: 回调处理器实例
            is_global: 是否设为全局处理器，默认为 False
        
        使用示例：
            >>> manager.register_handler("my_handler", handler, is_global=True)
        """
        logger.debug("注册处理器: %s (全局: %s)", name, is_global)
        
        # 如果已存在同名处理器，先注销旧的
        if name in self._handlers:
            old_handler = self._handlers[name]
            if old_handler in self._global_handlers:
                self._global_handlers.remove(old_handler)
            logger.debug("移除旧处理器: %s", name)
        
        # 注册新处理器
        self._handlers[name] = handler
        
        # 如果是全局处理器，添加到全局列表
        if is_global:
            if handler not in self._global_handlers:
                self._global_handlers.append(handler)
    
    def unregister_handler(self, name: str) -> None:
        """
        注销回调处理器
        
        从管理器中移除指定名称的处理器。
        
        Args:
            name: 处理器名称
        """
        if name in self._handlers:
            handler = self._handlers[name]
            # 从全局列表中移除
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)
            # 从字典中移除
            del self._handlers[name]
            logger.debug("注销处理器: %s", name)

    def get_handler(self, name: str) -> BaseCallbackHandler | None:
        """
        获取指定名称的处理器
        
        Args:
            name: 处理器名称
        
        Returns:
            处理器实例，如果不存在则返回 None
        """
        return self._handlers.get(name)

    def get_all_handlers(self) -> dict[str, BaseCallbackHandler]:
        """
        获取所有处理器
        
        Returns:
            处理器字典的副本
        """
        return self._handlers.copy()

    # ==================== 快捷创建方法 ====================

    def create_streaming_handler(
        self,
        name: str = "streaming",
        output_callback: Callable[[str], None] | None = None,
        complete_callback: Callable[[str], None] | None = None,
        enable_typewriter: bool = True,
        is_global: bool = False
    ) -> StreamingCallbackHandler:
        """
        创建流式输出处理器
        
        创建并注册一个流式输出回调处理器。
        
        Args:
            name: 处理器名称，默认为 "streaming"
            output_callback: token 输出回调函数
            complete_callback: 完成回调函数
            enable_typewriter: 是否启用打字机效果
            is_global: 是否为全局处理器
        
        Returns:
            StreamingCallbackHandler 实例
        
        使用示例：
            >>> handler = manager.create_streaming_handler(
            ...     output_callback=lambda token: print(token, end='')
            ... )
        """
        logger.debug("创建流式输出处理器: %s", name)
        
        # 创建处理器实例
        handler = StreamingCallbackHandler(
            output_callback=output_callback,
            complete_callback=complete_callback,
            enable_typewriter=enable_typewriter
        )
        
        # 注册处理器
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_qt_streaming_handler(
        self,
        name: str = "qt_streaming",
        append_signal: object = None,
        complete_signal: object = None,
        enable_typewriter: bool = True,
        is_global: bool = False
    ) -> QtStreamingCallbackHandler:
        """
        创建 Qt 流式输出处理器
        
        创建并注册一个专为 PyQt GUI 设计的流式输出处理器。
        
        Args:
            name: 处理器名称，默认为 "qt_streaming"
            append_signal: PyQt 追加文本信号
            complete_signal: PyQt 完成信号
            enable_typewriter: 是否启用打字机效果
            is_global: 是否为全局处理器
        
        Returns:
            QtStreamingCallbackHandler 实例
        
        使用示例：
            >>> handler = manager.create_qt_streaming_handler(
            ...     append_signal=self.append_signal
            ... )
        """
        logger.debug("创建 Qt 流式输出处理器: %s", name)
        
        # 创建处理器实例
        handler = QtStreamingCallbackHandler(
            append_signal=append_signal,
            complete_signal=complete_signal,
            enable_typewriter=enable_typewriter
        )
        
        # 注册处理器
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_logging_handler(
        self,
        name: str = "logging",
        log_file: str | None = None,
        enable_console: bool = True,
        enable_detailed: bool = True,
        is_global: bool = False
    ) -> LoggingCallbackHandler:
        """
        创建日志记录处理器
        
        创建并注册一个日志记录回调处理器。
        
        Args:
            name: 处理器名称，默认为 "logging"
            log_file: 日志文件路径
            enable_console: 是否输出到控制台
            enable_detailed: 是否记录详细信息
            is_global: 是否为全局处理器
        
        Returns:
            LoggingCallbackHandler 实例
        
        使用示例：
            >>> handler = manager.create_logging_handler(
            ...     log_file="logs/callback.log",
            ...     enable_console=True
            ... )
        """
        logger.debug("创建日志记录处理器: %s", name)
        
        # 创建处理器实例
        handler = LoggingCallbackHandler(
            log_file=log_file,
            enable_console=enable_console,
            enable_detailed=enable_detailed
        )
        
        # 注册处理器
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_performance_handler(
        self,
        name: str = "performance",
        log_file: str | None = None,
        enable_console: bool = True,
        enable_detailed: bool = True,
        is_global: bool = False
    ) -> PerformanceCallbackHandler:
        """
        创建性能监控处理器
        
        创建并注册一个性能监控回调处理器。
        
        Args:
            name: 处理器名称，默认为 "performance"
            log_file: 日志文件路径
            enable_console: 是否输出到控制台
            enable_detailed: 是否记录详细信息
            is_global: 是否为全局处理器
        
        Returns:
            PerformanceCallbackHandler 实例
        
        使用示例：
            >>> handler = manager.create_performance_handler(enable_console=True)
        """
        logger.debug("创建性能监控处理器: %s", name)
        
        # 创建处理器实例
        handler = PerformanceCallbackHandler(
            log_file=log_file,
            enable_console=enable_console,
            enable_detailed=enable_detailed
        )
        
        # 注册处理器
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_memory_handler(
        self,
        name: str = "memory",
        memory_manager: object = None,
        auto_save: bool = True,
        max_history: int = 50,
        is_global: bool = False
    ) -> MemoryCallbackHandler:
        """
        创建记忆管理处理器
        
        创建并注册一个记忆管理回调处理器。
        
        Args:
            name: 处理器名称，默认为 "memory"
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存
            max_history: 最大历史记录数
            is_global: 是否为全局处理器
        
        Returns:
            MemoryCallbackHandler 实例
        
        使用示例：
            >>> handler = manager.create_memory_handler(
            ...     memory_manager=my_memory_manager
            ... )
        """
        logger.debug("创建记忆管理处理器: %s", name)
        
        # 创建处理器实例
        handler = MemoryCallbackHandler(
            memory_manager=memory_manager,
            auto_save=auto_save,
            max_history=max_history
        )
        
        # 注册处理器
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_file_memory_handler(
        self,
        name: str = "file_memory",
        file_manager: object = None,
        memory_manager: object = None,
        auto_save: bool = True,
        max_history: int = 50,
        is_global: bool = False
    ) -> FileBasedMemoryCallbackHandler:
        """
        创建基于文件的记忆处理器
        
        创建并注册一个基于文件的记忆回调处理器。
        
        Args:
            name: 处理器名称，默认为 "file_memory"
            file_manager: 文件管理器实例
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存
            max_history: 最大历史记录数
            is_global: 是否为全局处理器
        
        Returns:
            FileBasedMemoryCallbackHandler 实例
        
        使用示例：
            >>> handler = manager.create_file_memory_handler(
            ...     file_manager=my_file_manager
            ... )
        """
        logger.debug("创建基于文件的记忆处理器: %s", name)
        
        # 创建处理器实例
        handler = FileBasedMemoryCallbackHandler(
            file_manager=file_manager,
            memory_manager=memory_manager,
            auto_save=auto_save,
            max_history=max_history
        )
        
        # 注册处理器
        self.register_handler(name, handler, is_global)
        return handler
    
    # ==================== 回调列表管理 ====================
    
    def get_callbacks(
        self,
        include_global: bool = True,
        handler_names: list[str] | None = None
    ) -> list[BaseCallbackHandler]:
        """
        获取回调处理器列表
        
        返回用于 invoke 调用的回调处理器列表。
        
        Args:
            include_global: 是否包含全局处理器，默认为 True
            handler_names: 指定处理器名称列表，可选
        
        Returns:
            回调处理器列表（已去重）
        
        使用示例：
            >>> callbacks = manager.get_callbacks(handler_names=["streaming", "logging"])
        """
        callbacks = []
        seen = set()  # 用于去重
        
        # 添加全局处理器
        if include_global:
            for handler in self._global_handlers:
                handler_id = id(handler)
                if handler_id not in seen:
                    callbacks.append(handler)
                    seen.add(handler_id)
        
        # 添加指定处理器
        if handler_names:
            for name in handler_names:
                if name in self._handlers:
                    handler = self._handlers[name]
                    handler_id = id(handler)
                    if handler_id not in seen:
                        callbacks.append(handler)
                        seen.add(handler_id)
        
        logger.debug("获取回调处理器列表，数量: %d", len(callbacks))
        return callbacks
    
    def get_callbacks_for_invoke(
        self,
        include_global: bool = True,
        handler_names: list[str] | None = None
    ) -> dict[str, list[BaseCallbackHandler]]:
        """
        获取用于 invoke 调用的回调配置
        
        返回可直接用于 model.invoke(config=...) 的配置字典。
        
        Args:
            include_global: 是否包含全局处理器
            handler_names: 指定处理器名称列表
        
        Returns:
            {"callbacks": [...]} 格式的字典
        
        使用示例：
            >>> config = manager.get_callbacks_for_invoke()
            >>> response = model.invoke(messages, config=config)
        """
        callbacks = self.get_callbacks(include_global, handler_names)
        return {"callbacks": callbacks} if callbacks else {}
    
    # ==================== 统计和摘要 ====================
    
    def print_all_statistics(self) -> None:
        """
        打印所有处理器的统计信息
        
        遍历所有处理器，打印其统计信息摘要。
        """
        print("\n" + "=" * 60)
        print("📊 回调处理器统计摘要")
        print("=" * 60)
        
        # 遍历所有处理器
        for name, handler in self._handlers.items():
            print(f"\n【{name}】")
            
            # 日志处理器统计
            if isinstance(handler, (LoggingCallbackHandler, PerformanceCallbackHandler)):
                stats = handler.get_statistics()
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            
            # 性能处理器统计
            if isinstance(handler, PerformanceCallbackHandler):
                print("\n  性能统计:")
                perf_stats = handler.get_performance_stats()
                for component, data in perf_stats.items():
                    if data['count'] > 0:
                        print(f"    {component}: 平均 {data['avg']:.2f}s, "
                              f"最小 {data['min']:.2f}s, 最大 {data['max']:.2f}s")
            
            # 记忆处理器统计
            if isinstance(handler, MemoryCallbackHandler):
                history = handler.get_conversation_history()
                print(f"  对话历史数: {len(history)}")
                
                # 会话记忆处理器的额外统计
                if isinstance(handler, SessionMemoryCallbackHandler):
                    sessions = handler.get_all_sessions()
                    print(f"  会话数: {len(sessions)}")
        
        print("\n" + "=" * 60)
    
    def reset_all_statistics(self) -> None:
        """
        重置所有处理器的统计信息
        
        遍历所有处理器，调用其重置方法。
        """
        logger.info("重置所有处理器的统计信息")
        
        for handler in self._handlers.values():
            if hasattr(handler, 'reset_statistics'):
                handler.reset_statistics()
            elif hasattr(handler, 'clear_history'):
                handler.clear_history()
    
    # ==================== 便捷方法 ====================
    
    def setup_default_handlers(
        self,
        output_callback: Callable[[str], None] | None = None,
        log_file: str | None = None,
        memory_manager: object = None,
        file_manager: object = None
    ) -> None:
        """
        设置默认的回调处理器组合
        
        一次性创建流式输出、日志记录和记忆管理的处理器组合。
        
        Args:
            output_callback: 流式输出回调函数
            log_file: 日志文件路径
            memory_manager: 记忆管理器
            file_manager: 文件管理器
        
        使用示例：
            >>> manager.setup_default_handlers(
            ...     output_callback=lambda token: print(token),
            ...     log_file="logs/app.log"
            ... )
        """
        logger.info("设置默认回调处理器组合")
        
        # 创建流式输出处理器
        if output_callback:
            self.create_streaming_handler(
                name="default_streaming",
                output_callback=output_callback,
                is_global=True
            )
        
        # 创建日志处理器
        self.create_logging_handler(
            name="default_logging",
            log_file=log_file,
            is_global=True
        )
        
        # 创建记忆处理器
        if file_manager:
            self.create_file_memory_handler(
                name="default_memory",
                file_manager=file_manager,
                memory_manager=memory_manager,
                is_global=True
            )
        elif memory_manager:
            self.create_memory_handler(
                name="default_memory",
                memory_manager=memory_manager,
                is_global=True
            )
    
    def clear_all(self) -> None:
        """
        清空所有处理器
        
        移除所有注册的处理器和全局处理器。
        """
        logger.info("清空所有处理器")
        self._handlers.clear()
        self._global_handlers.clear()


# ==================== 全局单例 ====================

# 全局回调管理器实例
_global_callback_manager: CallbackManager | None = None


def get_callback_manager() -> CallbackManager:
    """
    获取全局回调管理器单例
    
    如果全局管理器不存在则创建，否则返回现有实例。
    
    Returns:
        CallbackManager 实例
    
    使用示例：
        >>> manager = get_callback_manager()
    """
    global _global_callback_manager
    if _global_callback_manager is None:
        _global_callback_manager = CallbackManager()
        logger.debug("创建全局回调管理器单例")
    return _global_callback_manager


def reset_callback_manager() -> None:
    """
    重置全局回调管理器
    
    清空全局管理器的所有处理器并重置为 None。
    下次调用 get_callback_manager 时会创建新实例。
    
    使用示例：
        >>> reset_callback_manager()
    """
    global _global_callback_manager
    if _global_callback_manager:
        _global_callback_manager.clear_all()
    _global_callback_manager = None
    logger.debug("重置全局回调管理器")

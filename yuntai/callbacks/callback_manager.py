"""
回调管理器
统一管理所有回调处理器，提供便捷的配置和使用接口
"""
from typing import Any, Dict, List, Optional, Callable
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


class CallbackManager:
    """
    回调管理器
    
    统一管理所有回调处理器，提供：
    - 便捷的处理器创建和配置
    - 统一的回调列表管理
    - 全局和局部回调支持
    """
    
    def __init__(self):
        """初始化回调管理器"""
        self._handlers: Dict[str, BaseCallbackHandler] = {}
        self._global_handlers: List[BaseCallbackHandler] = []
        
    # ==================== 处理器注册 ====================
    
    def register_handler(
        self, 
        name: str, 
        handler: BaseCallbackHandler,
        is_global: bool = False
    ):
        """
        注册回调处理器
        
        Args:
            name: 处理器名称
            handler: 处理器实例
            is_global: 是否为全局处理器
        """
        # 如果已存在同名处理器，先注销旧的
        if name in self._handlers:
            old_handler = self._handlers[name]
            if old_handler in self._global_handlers:
                self._global_handlers.remove(old_handler)
        
        self._handlers[name] = handler
        
        if is_global:
            if handler not in self._global_handlers:
                self._global_handlers.append(handler)
    
    def unregister_handler(self, name: str):
        """注销回调处理器"""
        if name in self._handlers:
            handler = self._handlers[name]
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)
            del self._handlers[name]
    
    def get_handler(self, name: str) -> Optional[BaseCallbackHandler]:
        """获取指定名称的处理器"""
        return self._handlers.get(name)
    
    def get_all_handlers(self) -> Dict[str, BaseCallbackHandler]:
        """获取所有处理器"""
        return self._handlers.copy()
    
    # ==================== 快捷创建方法 ====================
    
    def create_streaming_handler(
        self,
        name: str = "streaming",
        output_callback: Optional[Callable[[str], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        enable_typewriter: bool = True,
        is_global: bool = False
    ) -> StreamingCallbackHandler:
        """
        创建流式输出处理器
        
        Args:
            name: 处理器名称
            output_callback: token 输出回调
            complete_callback: 完成回调
            enable_typewriter: 是否启用打字机效果
            is_global: 是否为全局处理器
        
        Returns:
            StreamingCallbackHandler 实例
        """
        handler = StreamingCallbackHandler(
            output_callback=output_callback,
            complete_callback=complete_callback,
            enable_typewriter=enable_typewriter
        )
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_qt_streaming_handler(
        self,
        name: str = "qt_streaming",
        append_signal=None,
        complete_signal=None,
        enable_typewriter: bool = True,
        is_global: bool = False
    ) -> QtStreamingCallbackHandler:
        """
        创建 Qt 流式输出处理器
        
        Args:
            name: 处理器名称
            append_signal: PyQt 追加文本信号
            complete_signal: PyQt 完成信号
            enable_typewriter: 是否启用打字机效果
            is_global: 是否为全局处理器
        
        Returns:
            QtStreamingCallbackHandler 实例
        """
        handler = QtStreamingCallbackHandler(
            append_signal=append_signal,
            complete_signal=complete_signal,
            enable_typewriter=enable_typewriter
        )
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_logging_handler(
        self,
        name: str = "logging",
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_detailed: bool = True,
        is_global: bool = False
    ) -> LoggingCallbackHandler:
        """
        创建日志记录处理器
        
        Args:
            name: 处理器名称
            log_file: 日志文件路径
            enable_console: 是否输出到控制台
            enable_detailed: 是否记录详细信息
            is_global: 是否为全局处理器
        
        Returns:
            LoggingCallbackHandler 实例
        """
        handler = LoggingCallbackHandler(
            log_file=log_file,
            enable_console=enable_console,
            enable_detailed=enable_detailed
        )
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_performance_handler(
        self,
        name: str = "performance",
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_detailed: bool = True,
        is_global: bool = False
    ) -> PerformanceCallbackHandler:
        """
        创建性能监控处理器
        
        Args:
            name: 处理器名称
            log_file: 日志文件路径
            enable_console: 是否输出到控制台
            enable_detailed: 是否记录详细信息
            is_global: 是否为全局处理器
        
        Returns:
            PerformanceCallbackHandler 实例
        """
        handler = PerformanceCallbackHandler(
            log_file=log_file,
            enable_console=enable_console,
            enable_detailed=enable_detailed
        )
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_memory_handler(
        self,
        name: str = "memory",
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50,
        is_global: bool = False
    ) -> MemoryCallbackHandler:
        """
        创建记忆管理处理器
        
        Args:
            name: 处理器名称
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存
            max_history: 最大历史记录数
            is_global: 是否为全局处理器
        
        Returns:
            MemoryCallbackHandler 实例
        """
        handler = MemoryCallbackHandler(
            memory_manager=memory_manager,
            auto_save=auto_save,
            max_history=max_history
        )
        self.register_handler(name, handler, is_global)
        return handler
    
    def create_file_memory_handler(
        self,
        name: str = "file_memory",
        file_manager=None,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50,
        is_global: bool = False
    ) -> FileBasedMemoryCallbackHandler:
        """
        创建基于文件的记忆处理器
        
        Args:
            name: 处理器名称
            file_manager: 文件管理器实例
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存
            max_history: 最大历史记录数
            is_global: 是否为全局处理器
        
        Returns:
            FileBasedMemoryCallbackHandler 实例
        """
        handler = FileBasedMemoryCallbackHandler(
            file_manager=file_manager,
            memory_manager=memory_manager,
            auto_save=auto_save,
            max_history=max_history
        )
        self.register_handler(name, handler, is_global)
        return handler
    
    # ==================== 回调列表管理 ====================
    
    def get_callbacks(
        self, 
        include_global: bool = True,
        handler_names: Optional[List[str]] = None
    ) -> List[BaseCallbackHandler]:
        """
        获取回调处理器列表
        
        Args:
            include_global: 是否包含全局处理器
            handler_names: 指定处理器名称列表（可选）
        
        Returns:
            回调处理器列表（去重）
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
        
        return callbacks
    
    def get_callbacks_for_invoke(
        self,
        include_global: bool = True,
        handler_names: Optional[List[str]] = None
    ) -> Dict[str, List[BaseCallbackHandler]]:
        """
        获取用于 invoke 调用的回调配置
        
        Args:
            include_global: 是否包含全局处理器
            handler_names: 指定处理器名称列表
        
        Returns:
            {"callbacks": [...]} 格式的字典
        """
        callbacks = self.get_callbacks(include_global, handler_names)
        return {"callbacks": callbacks} if callbacks else {}
    
    # ==================== 统计和摘要 ====================
    
    def print_all_statistics(self):
        """打印所有处理器的统计信息"""
        print("\n" + "=" * 60)
        print("📊 回调处理器统计摘要")
        print("=" * 60)
        
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
                
                if isinstance(handler, SessionMemoryCallbackHandler):
                    sessions = handler.get_all_sessions()
                    print(f"  会话数: {len(sessions)}")
        
        print("\n" + "=" * 60)
    
    def reset_all_statistics(self):
        """重置所有处理器的统计信息"""
        for handler in self._handlers.values():
            if hasattr(handler, 'reset_statistics'):
                handler.reset_statistics()
            elif hasattr(handler, 'clear_history'):
                handler.clear_history()
    
    # ==================== 便捷方法 ====================
    
    def setup_default_handlers(
        self,
        output_callback: Optional[Callable[[str], None]] = None,
        log_file: Optional[str] = None,
        memory_manager=None,
        file_manager=None
    ):
        """
        设置默认的回调处理器组合
        
        Args:
            output_callback: 流式输出回调
            log_file: 日志文件路径
            memory_manager: 记忆管理器
            file_manager: 文件管理器
        """
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
    
    def clear_all(self):
        """清空所有处理器"""
        self._handlers.clear()
        self._global_handlers.clear()


# 全局单例
_global_callback_manager: Optional[CallbackManager] = None


def get_callback_manager() -> CallbackManager:
    """获取全局回调管理器单例"""
    global _global_callback_manager
    if _global_callback_manager is None:
        _global_callback_manager = CallbackManager()
    return _global_callback_manager


def reset_callback_manager():
    """重置全局回调管理器"""
    global _global_callback_manager
    if _global_callback_manager:
        _global_callback_manager.clear_all()
    _global_callback_manager = None

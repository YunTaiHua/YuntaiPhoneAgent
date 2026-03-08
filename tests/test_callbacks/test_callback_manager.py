"""
CallbackManager 测试
测试回调管理器的各种功能
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from yuntai.callbacks.callback_manager import (
    CallbackManager,
    get_callback_manager,
    reset_callback_manager
)
from yuntai.callbacks.streaming_handler import StreamingCallbackHandler
from yuntai.callbacks.logging_handler import LoggingCallbackHandler, PerformanceCallbackHandler
from yuntai.callbacks.memory_handler import MemoryCallbackHandler, SessionMemoryCallbackHandler


class TestCallbackManagerInit:
    """测试 CallbackManager 初始化"""

    def test_init(self):
        """测试初始化"""
        manager = CallbackManager()
        assert manager._handlers == {}
        assert manager._global_handlers == []


class TestCallbackManagerRegister:
    """测试处理器注册"""

    def test_register_handler(self):
        """测试注册处理器"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler)

        assert "test" in manager._handlers
        assert manager._handlers["test"] == handler

    def test_register_handler_global(self):
        """测试注册全局处理器"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler, is_global=True)

        assert handler in manager._global_handlers

    def test_register_handler_not_global(self):
        """测试注册非全局处理器"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler, is_global=False)

        assert handler not in manager._global_handlers

    def test_register_handler_replace_existing(self):
        """测试替换已存在的处理器"""
        manager = CallbackManager()
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("test", handler1, is_global=True)
        manager.register_handler("test", handler2, is_global=True)

        assert manager._handlers["test"] == handler2
        assert handler1 not in manager._global_handlers
        assert handler2 in manager._global_handlers

    def test_unregister_handler(self):
        """测试注销处理器"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler, is_global=True)
        manager.unregister_handler("test")

        assert "test" not in manager._handlers
        assert handler not in manager._global_handlers

    def test_unregister_nonexistent_handler(self):
        """测试注销不存在的处理器"""
        manager = CallbackManager()

        # 不应该抛出异常
        manager.unregister_handler("nonexistent")

    def test_get_handler(self):
        """测试获取处理器"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler)
        result = manager.get_handler("test")

        assert result == handler

    def test_get_handler_nonexistent(self):
        """测试获取不存在的处理器"""
        manager = CallbackManager()
        result = manager.get_handler("nonexistent")

        assert result is None

    def test_get_all_handlers(self):
        """测试获取所有处理器"""
        manager = CallbackManager()
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("test1", handler1)
        manager.register_handler("test2", handler2)

        all_handlers = manager.get_all_handlers()

        assert len(all_handlers) == 2
        assert all_handlers["test1"] == handler1
        assert all_handlers["test2"] == handler2


class TestCallbackManagerCreateHandlers:
    """测试创建各种处理器"""

    def test_create_streaming_handler(self):
        """测试创建流式输出处理器"""
        manager = CallbackManager()

        handler = manager.create_streaming_handler(
            name="streaming",
            output_callback=lambda x: None,
            complete_callback=lambda x: None,
            enable_typewriter=True,
            is_global=True
        )

        assert isinstance(handler, StreamingCallbackHandler)
        assert "streaming" in manager._handlers
        assert handler in manager._global_handlers

    def test_create_qt_streaming_handler(self):
        """测试创建 Qt 流式输出处理器"""
        manager = CallbackManager()
        append_signal = Mock()
        complete_signal = Mock()

        from yuntai.callbacks.streaming_handler import QtStreamingCallbackHandler
        handler = manager.create_qt_streaming_handler(
            name="qt_streaming",
            append_signal=append_signal,
            complete_signal=complete_signal,
            enable_typewriter=True,
            is_global=False
        )

        assert isinstance(handler, QtStreamingCallbackHandler)
        assert "qt_streaming" in manager._handlers

    def test_create_logging_handler(self):
        """测试创建日志处理器"""
        manager = CallbackManager()

        handler = manager.create_logging_handler(
            name="logging",
            log_file=None,
            enable_console=True,
            enable_detailed=True,
            is_global=True
        )

        assert isinstance(handler, LoggingCallbackHandler)
        assert "logging" in manager._handlers
        assert handler in manager._global_handlers

    def test_create_performance_handler(self):
        """测试创建性能监控处理器"""
        manager = CallbackManager()

        handler = manager.create_performance_handler(
            name="performance",
            log_file=None,
            enable_console=False,
            enable_detailed=True,
            is_global=False
        )

        assert isinstance(handler, PerformanceCallbackHandler)
        assert "performance" in manager._handlers

    def test_create_memory_handler(self):
        """测试创建记忆处理器"""
        manager = CallbackManager()
        memory_manager = Mock()

        handler = manager.create_memory_handler(
            name="memory",
            memory_manager=memory_manager,
            auto_save=True,
            max_history=50,
            is_global=True
        )

        assert isinstance(handler, MemoryCallbackHandler)
        assert "memory" in manager._handlers

    def test_create_file_memory_handler(self):
        """测试创建基于文件的记忆处理器"""
        manager = CallbackManager()
        file_manager = Mock()
        memory_manager = Mock()

        from yuntai.callbacks.memory_handler import FileBasedMemoryCallbackHandler
        handler = manager.create_file_memory_handler(
            name="file_memory",
            file_manager=file_manager,
            memory_manager=memory_manager,
            auto_save=True,
            max_history=50,
            is_global=False
        )

        assert isinstance(handler, FileBasedMemoryCallbackHandler)
        assert "file_memory" in manager._handlers


class TestCallbackManagerGetCallbacks:
    """测试获取回调列表"""

    def test_get_callbacks_include_global(self):
        """测试获取回调包含全局处理器"""
        manager = CallbackManager()
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("global", handler1, is_global=True)
        manager.register_handler("local", handler2, is_global=False)

        callbacks = manager.get_callbacks(include_global=True)

        assert handler1 in callbacks
        assert handler2 not in callbacks

    def test_get_callbacks_exclude_global(self):
        """测试获取回调不包含全局处理器"""
        manager = CallbackManager()
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("global", handler1, is_global=True)
        manager.register_handler("local", handler2, is_global=False)

        callbacks = manager.get_callbacks(include_global=False)

        assert handler1 not in callbacks
        assert handler2 not in callbacks

    def test_get_callbacks_with_handler_names(self):
        """测试获取指定名称的回调"""
        manager = CallbackManager()
        handler1 = Mock()
        handler2 = Mock()

        manager.register_handler("handler1", handler1)
        manager.register_handler("handler2", handler2)

        callbacks = manager.get_callbacks(
            include_global=False,
            handler_names=["handler1"]
        )

        assert handler1 in callbacks
        assert handler2 not in callbacks

    def test_get_callbacks_deduplication(self):
        """测试回调去重"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler, is_global=True)

        callbacks = manager.get_callbacks(
            include_global=True,
            handler_names=["test"]
        )

        # 应该只出现一次
        assert callbacks.count(handler) == 1

    def test_get_callbacks_for_invoke(self):
        """测试获取用于 invoke 的回调配置"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler, is_global=True)

        result = manager.get_callbacks_for_invoke(include_global=True)

        assert "callbacks" in result
        assert handler in result["callbacks"]

    def test_get_callbacks_for_invoke_empty(self):
        """测试空回调配置"""
        manager = CallbackManager()

        result = manager.get_callbacks_for_invoke(include_global=False)

        assert result == {}


class TestCallbackManagerStatistics:
    """测试统计功能"""

    def test_print_all_statistics(self, capsys):
        """测试打印所有统计信息"""
        manager = CallbackManager()

        # 创建日志处理器
        handler = LoggingCallbackHandler(enable_console=False)
        manager.register_handler("logging", handler)

        # 模拟一些调用
        handler.on_llm_start({}, ["test"])
        from langchain_core.outputs import LLMResult, ChatGeneration
        from langchain_core.messages import AIMessage
        generation = ChatGeneration(message=AIMessage(content="test"))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        manager.print_all_statistics()

        captured = capsys.readouterr()
        assert "回调处理器统计摘要" in captured.out

    def test_reset_all_statistics(self):
        """测试重置所有统计信息"""
        manager = CallbackManager()

        # 创建日志处理器
        handler = LoggingCallbackHandler(enable_console=False)
        manager.register_handler("logging", handler)

        # 模拟一些调用
        handler.on_llm_start({}, ["test"])
        from langchain_core.outputs import LLMResult, ChatGeneration
        from langchain_core.messages import AIMessage
        generation = ChatGeneration(message=AIMessage(content="test"))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        stats = handler.get_statistics()
        assert stats['llm_calls'] == 1

        manager.reset_all_statistics()

        stats = handler.get_statistics()
        assert stats['llm_calls'] == 0


class TestCallbackManagerSetup:
    """测试便捷设置方法"""

    def test_setup_default_handlers_with_output_callback(self):
        """测试设置默认处理器带输出回调"""
        manager = CallbackManager()

        manager.setup_default_handlers(
            output_callback=lambda x: None,
            log_file=None
        )

        assert "default_streaming" in manager._handlers
        assert "default_logging" in manager._handlers

    def test_setup_default_handlers_with_memory_manager(self):
        """测试设置默认处理器带记忆管理器"""
        manager = CallbackManager()
        memory_manager = Mock()

        manager.setup_default_handlers(
            memory_manager=memory_manager
        )

        assert "default_memory" in manager._handlers

    def test_setup_default_handlers_with_file_manager(self):
        """测试设置默认处理器带文件管理器"""
        manager = CallbackManager()
        file_manager = Mock()
        memory_manager = Mock()

        manager.setup_default_handlers(
            file_manager=file_manager,
            memory_manager=memory_manager
        )

        assert "default_memory" in manager._handlers

    def test_clear_all(self):
        """测试清空所有处理器"""
        manager = CallbackManager()
        handler = Mock()

        manager.register_handler("test", handler, is_global=True)
        manager.clear_all()

        assert manager._handlers == {}
        assert manager._global_handlers == []


class TestGlobalCallbackManager:
    """测试全局回调管理器"""

    def test_get_callback_manager_singleton(self):
        """测试获取全局单例"""
        reset_callback_manager()

        manager1 = get_callback_manager()
        manager2 = get_callback_manager()

        assert manager1 is manager2

    def test_reset_callback_manager(self):
        """测试重置全局管理器"""
        manager1 = get_callback_manager()
        handler = Mock()
        manager1.register_handler("test", handler)

        reset_callback_manager()

        manager2 = get_callback_manager()
        assert manager1 is not manager2
        assert manager2.get_handler("test") is None

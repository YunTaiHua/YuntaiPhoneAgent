from yuntai.callbacks.callback_manager import (
    CallbackManager,
    get_callback_manager,
    reset_callback_manager,
)
from yuntai.callbacks.logging_handler import LoggingCallbackHandler, PerformanceCallbackHandler
from yuntai.callbacks.memory_handler import MemoryCallbackHandler, SessionMemoryCallbackHandler


def test_print_all_statistics_and_singleton_reset(capsys, tmp_path):
    manager = CallbackManager()
    manager.register_handler("log", LoggingCallbackHandler(log_file=str(tmp_path / "l.log"), enable_console=False))
    manager.register_handler("perf", PerformanceCallbackHandler(log_file=str(tmp_path / "p.log"), enable_console=False))

    mem = MemoryCallbackHandler(memory_manager=None, auto_save=False)
    mem._conversation_history = [{"user": "u", "assistant": "a", "timestamp": "t"}]
    manager.register_handler("mem", mem)

    smem = SessionMemoryCallbackHandler(memory_manager=None, auto_save=False)
    smem.set_session("s1")
    smem._sessions["s1"] = [{"user": "u", "assistant": "a", "timestamp": "t"}]
    manager.register_handler("smem", smem)

    manager.print_all_statistics()
    out = capsys.readouterr().out
    assert "回调处理器统计摘要" in out
    assert "性能统计" in out
    assert "对话历史数" in out
    assert "会话数" in out

    reset_callback_manager()
    a = get_callback_manager()
    b = get_callback_manager()
    assert a is b
    reset_callback_manager()
    c = get_callback_manager()
    assert c is not a


def test_create_qt_and_memory_handlers():
    manager = CallbackManager()

    h_qt = manager.create_qt_streaming_handler(name="q1")
    h_mem = manager.create_memory_handler(name="m1", auto_save=False)

    assert manager.get_handler("q1") is h_qt
    assert manager.get_handler("m1") is h_mem

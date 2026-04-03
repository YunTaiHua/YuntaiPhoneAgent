from langchain_core.callbacks import BaseCallbackHandler

from yuntai.callbacks.callback_manager import (
    CallbackManager,
    get_callback_manager,
    reset_callback_manager,
)


class _DummyHandler(BaseCallbackHandler):
    pass


def test_register_unregister_and_get_callbacks_deduplicates():
    manager = CallbackManager()
    h1 = _DummyHandler()
    h2 = _DummyHandler()

    manager.register_handler("a", h1, is_global=True)
    manager.register_handler("b", h1, is_global=False)
    manager.register_handler("c", h2, is_global=True)

    callbacks = manager.get_callbacks(include_global=True, handler_names=["a", "b", "c"])
    assert callbacks.count(h1) == 1
    assert callbacks.count(h2) == 1

    manager.unregister_handler("a")
    assert manager.get_handler("a") is None


def test_get_callbacks_for_invoke_returns_empty_or_callbacks():
    manager = CallbackManager()
    assert manager.get_callbacks_for_invoke() == {}

    h = _DummyHandler()
    manager.register_handler("x", h, is_global=True)
    cfg = manager.get_callbacks_for_invoke()
    assert "callbacks" in cfg
    assert h in cfg["callbacks"]


def test_setup_default_handlers_selects_memory_type(monkeypatch):
    manager = CallbackManager()
    calls = []

    monkeypatch.setattr(manager, "create_streaming_handler", lambda **kwargs: calls.append(("stream", kwargs)))
    monkeypatch.setattr(manager, "create_logging_handler", lambda **kwargs: calls.append(("log", kwargs)))
    monkeypatch.setattr(manager, "create_file_memory_handler", lambda **kwargs: calls.append(("file_mem", kwargs)))
    monkeypatch.setattr(manager, "create_memory_handler", lambda **kwargs: calls.append(("mem", kwargs)))

    manager.setup_default_handlers(output_callback=lambda x: None, file_manager=object(), memory_manager=object())
    assert any(x[0] == "stream" for x in calls)
    assert any(x[0] == "log" for x in calls)
    assert any(x[0] == "file_mem" for x in calls)

    calls.clear()
    manager.setup_default_handlers(output_callback=None, file_manager=None, memory_manager=object())
    assert any(x[0] == "mem" for x in calls)


def test_reset_all_statistics_and_clear_all():
    manager = CallbackManager()

    class _WithReset(BaseCallbackHandler):
        def __init__(self):
            self.reset_called = 0

        def reset_statistics(self):
            self.reset_called += 1

    class _WithClear(BaseCallbackHandler):
        def __init__(self):
            self.clear_called = 0

        def clear_history(self):
            self.clear_called += 1

    h1 = _WithReset()
    h2 = _WithClear()
    manager.register_handler("h1", h1)
    manager.register_handler("h2", h2)

    manager.reset_all_statistics()
    assert h1.reset_called == 1
    assert h2.clear_called == 1

    manager.clear_all()
    assert manager.get_all_handlers() == {}


def test_factory_methods_and_singleton(monkeypatch):
    manager = CallbackManager()

    class _FakeHandler:
        pass

    import yuntai.callbacks.callback_manager as mod

    monkeypatch.setattr(mod, "StreamingCallbackHandler", lambda **_k: _FakeHandler())
    monkeypatch.setattr(mod, "QtStreamingCallbackHandler", lambda **_k: _FakeHandler())
    monkeypatch.setattr(mod, "LoggingCallbackHandler", lambda **_k: _FakeHandler())
    monkeypatch.setattr(mod, "PerformanceCallbackHandler", lambda **_k: _FakeHandler())
    monkeypatch.setattr(mod, "MemoryCallbackHandler", lambda **_k: _FakeHandler())
    monkeypatch.setattr(mod, "FileBasedMemoryCallbackHandler", lambda **_k: _FakeHandler())

    s = manager.create_streaming_handler(name="s", output_callback=lambda _t: None, is_global=True)
    qs = manager.create_qt_streaming_handler(name="qs")
    lg = manager.create_logging_handler(name="lg")
    pf = manager.create_performance_handler(name="pf")
    mem = manager.create_memory_handler(name="mem")
    fmem = manager.create_file_memory_handler(name="fmem")

    assert isinstance(s, _FakeHandler)
    assert isinstance(qs, _FakeHandler)
    assert isinstance(lg, _FakeHandler)
    assert isinstance(pf, _FakeHandler)
    assert isinstance(mem, _FakeHandler)
    assert isinstance(fmem, _FakeHandler)

    reset_callback_manager()
    one = get_callback_manager()
    two = get_callback_manager()
    assert one is two

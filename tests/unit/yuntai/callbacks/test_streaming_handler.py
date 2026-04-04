import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from langchain_core.outputs import LLMResult

from yuntai.callbacks.streaming_handler import (
    AsyncStreamingCallbackHandler,
    QtStreamingCallbackHandler,
    StreamingCallbackHandler,
)


class _Signal:
    def __init__(self):
        self.values = []

    def emit(self, value):
        self.values.append(value)


def test_streaming_handler_token_and_complete_callbacks():
    out = []
    done = []
    h = StreamingCallbackHandler(output_callback=lambda t: out.append(t), complete_callback=lambda s: done.append(s))

    h.on_llm_start({}, ["prompt"])
    h.on_llm_new_token("a")
    h.on_llm_new_token("b")
    h.on_llm_end(LLMResult(generations=[]))

    assert out == ["a", "b"]
    assert done == ["ab"]
    assert h.get_current_response() == "ab"


def test_streaming_handler_error_resets_and_ignores_tokens_before_start():
    h = StreamingCallbackHandler()
    h.on_llm_new_token("x")
    assert h.get_current_response() == ""

    h.on_llm_start({}, ["p"])
    h.on_llm_new_token("x")
    h.on_llm_error(RuntimeError("boom"))
    assert h._is_streaming is False


def test_qt_streaming_handler_emits_signals():
    append = _Signal()
    complete = _Signal()
    h = QtStreamingCallbackHandler(append_signal=append, complete_signal=complete)

    h.on_llm_start({}, ["p"])
    h.on_llm_new_token("你")
    h.on_llm_new_token("好")
    h.on_llm_end(LLMResult(generations=[]))

    assert append.values == ["你", "好"]
    assert complete.values == ["你好"]


def test_async_streaming_handler_supports_sync_and_async_callbacks():
    sync_tokens = []
    h_sync = AsyncStreamingCallbackHandler(output_callback=lambda t: sync_tokens.append(t))
    h_sync.on_llm_start({}, ["p"])
    asyncio.run(h_sync.on_llm_new_token_async("a"))
    assert sync_tokens == ["a"]

    async_tokens = []

    async def cb(token):
        async_tokens.append(token)

    h_async = AsyncStreamingCallbackHandler(output_callback=cb)
    h_async.on_llm_start({}, ["p"])
    asyncio.run(h_async.on_llm_new_token_async("b"))
    assert async_tokens == ["b"]
    assert h_async.get_current_response() == "b"


class TestStreamingHandlerCoverageGaps:
    def test_output_callback_exception(self):
        handler = StreamingCallbackHandler()
        handler._is_streaming = True
        handler.output_callback = lambda t: (_ for _ in ()).throw(RuntimeError("cb boom"))
        handler.on_llm_new_token("test", run=MagicMock())

    def test_complete_callback_exception(self):
        handler = StreamingCallbackHandler()
        handler._is_streaming = True
        handler._current_response = "some response"
        handler.complete_callback = lambda t: (_ for _ in ()).throw(RuntimeError("cb boom"))
        handler.on_llm_end(MagicMock(), run=MagicMock())

    def test_reset_method(self):
        handler = StreamingCallbackHandler()
        handler._current_response = "old"
        handler._is_streaming = True
        handler.reset()
        assert handler._current_response == ""
        assert handler._is_streaming is False

    def test_qt_handler_not_streaming_early_return(self):
        handler = QtStreamingCallbackHandler()
        handler._is_streaming = False
        handler.on_llm_new_token("test", run=MagicMock())

    def test_qt_handler_signal_exception(self):
        handler = QtStreamingCallbackHandler()
        handler._is_streaming = True
        handler.append_signal = SimpleNamespace(emit=lambda t: (_ for _ in ()).throw(RuntimeError("signal boom")))
        handler.on_llm_new_token("test", run=MagicMock())

    def test_qt_handler_complete_signal_exception(self):
        handler = QtStreamingCallbackHandler()
        handler._is_streaming = True
        handler._current_response = "resp"
        handler.complete_signal = SimpleNamespace(emit=lambda t: (_ for _ in ()).throw(RuntimeError("signal boom")))
        handler.on_llm_end(MagicMock(), run=MagicMock())

    def test_async_handler_not_streaming_early_return(self):
        handler = AsyncStreamingCallbackHandler()
        handler._is_streaming = False
        asyncio.run(handler.on_llm_new_token_async("test", run=MagicMock()))

    def test_async_handler_callback_exception(self, monkeypatch):
        import builtins
        handler = AsyncStreamingCallbackHandler()
        handler._is_streaming = True
        handler.output_callback = lambda t: (_ for _ in ()).throw(RuntimeError("async boom"))
        real_print = builtins.print
        monkeypatch.setattr(builtins, "print", lambda *a, **k: None)
        asyncio.run(handler.on_llm_new_token_async("test", run=MagicMock()))

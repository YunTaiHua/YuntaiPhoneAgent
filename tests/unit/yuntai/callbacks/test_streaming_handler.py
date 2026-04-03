import asyncio

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

from yuntai.tools import callback_utils


class _Manager:
    def __init__(self):
        self.calls = []

    def get_callbacks(self, include_global=False):
        self.calls.append(include_global)
        return ["g1", "g2"]


def test_prepare_callbacks_includes_global_streaming_and_custom(monkeypatch):
    manager = _Manager()

    class _Streaming:
        def __init__(self, output_callback=None, complete_callback=None):
            self.output_callback = output_callback
            self.complete_callback = complete_callback

    monkeypatch.setattr(callback_utils, "StreamingCallbackHandler", _Streaming)
    monkeypatch.setattr(callback_utils, "get_callback_manager", lambda: manager)

    result = callback_utils.prepare_callbacks(
        callbacks=["user"],
        streaming_callback=lambda _x: None,
        complete_callback=lambda _x: None,
        enable_streaming=True,
    )

    assert manager.calls == [True]
    assert result[0:2] == ["g1", "g2"]
    assert isinstance(result[2], _Streaming)
    assert result[3] == "user"


def test_prepare_callbacks_without_streaming(monkeypatch):
    manager = _Manager()
    monkeypatch.setattr(callback_utils, "get_callback_manager", lambda: manager)

    result = callback_utils.prepare_callbacks(enable_streaming=False)
    assert result == ["g1", "g2"]


def test_prepare_callbacks_with_manager_and_get_global(monkeypatch):
    manager = _Manager()

    class _Streaming:
        def __init__(self, output_callback=None, complete_callback=None):
            self.output_callback = output_callback
            self.complete_callback = complete_callback

    monkeypatch.setattr(callback_utils, "StreamingCallbackHandler", _Streaming)

    merged = callback_utils.prepare_callbacks_with_manager(
        manager,
        callbacks=["x"],
        streaming_callback=lambda _x: None,
        complete_callback=None,
        enable_streaming=True,
    )
    assert merged[0:2] == ["g1", "g2"]
    assert isinstance(merged[2], _Streaming)
    assert merged[3] == "x"

    globals_only = callback_utils.get_global_callbacks(callback_manager=manager)
    assert globals_only == ["g1", "g2"]

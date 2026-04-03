from types import SimpleNamespace

from yuntai.agents.chat_agent import ChatAgent


class _FakeModel:
    def __init__(self, reply_text="  默认回复  ", stream_chunks=None, boom=False):
        self.reply_text = reply_text
        self.stream_chunks = stream_chunks or ["A", "B"]
        self.boom = boom
        self.invocations = []

    def invoke(self, messages, config=None):
        if self.boom:
            raise RuntimeError("boom")
        self.invocations.append((messages, config))
        return SimpleNamespace(content=self.reply_text)

    def stream(self, messages, config=None):
        if self.boom:
            raise RuntimeError("stream-boom")
        self.invocations.append((messages, config))
        for chunk in self.stream_chunks:
            yield SimpleNamespace(content=chunk)


class _FakeFileManager:
    def __init__(self):
        self.saved = []

    def read_forever_memory(self):
        return "长期记忆"

    def get_recent_free_chats(self, limit=0):
        return [{"user_input": "u1", "assistant_reply": "a1"}]

    def save_conversation_history(self, data):
        self.saved.append(data)


def test_chat_success_saves_history_and_triggers_tts(monkeypatch):
    timer_calls = []
    callback_calls = []

    class _Timer:
        def __init__(self, delay, fn):
            timer_calls.append(delay)
            self._fn = fn

        def start(self):
            self._fn()

    monkeypatch.setattr("yuntai.agents.chat_agent.get_zhipu_client", lambda: object())
    monkeypatch.setattr("yuntai.agents.chat_agent.threading.Timer", _Timer)
    monkeypatch.setattr(
        "yuntai.agents.chat_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: ["cb"],
    )

    model = _FakeModel(reply_text="  这是一条足够长的回复内容  ")
    fm = _FakeFileManager()
    tts = SimpleNamespace(tts_enabled=True, speak_text_intelligently=lambda text: callback_calls.append(text))
    manager = SimpleNamespace(get_callbacks=lambda include_global=True: [])

    agent = ChatAgent(model=model, file_manager=fm, tts_manager=tts, callback_manager=manager)
    result = agent.chat("你好", include_memory=True)

    assert result == "这是一条足够长的回复内容"
    assert fm.saved and fm.saved[0]["type"] == "free_chat"
    assert callback_calls == ["这是一条足够长的回复内容"]
    assert len(timer_calls) == 1
    _, config = model.invocations[0]
    assert config == {"callbacks": ["cb"]}


def test_chat_returns_error_string_on_model_exception(monkeypatch):
    monkeypatch.setattr("yuntai.agents.chat_agent.get_zhipu_client", lambda: object())
    monkeypatch.setattr(
        "yuntai.agents.chat_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: [],
    )

    agent = ChatAgent(model=_FakeModel(boom=True), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    result = agent.chat("hello")
    assert result == "聊天失败: boom"


def test_chat_with_history_uses_recent_history_window(monkeypatch):
    monkeypatch.setattr("yuntai.agents.chat_agent.get_zhipu_client", lambda: object())
    monkeypatch.setattr(
        "yuntai.agents.chat_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: [],
    )
    model = _FakeModel(reply_text=" ok ")
    agent = ChatAgent(model=model, callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))

    history = [{"role": "user", "content": f"u{i}"} for i in range(20)]
    result = agent.chat_with_history("latest", history)

    assert result == "ok"
    messages, _ = model.invocations[0]
    assert messages[0].content == agent.system_prompt
    assert messages[-1].content == "latest"
    assert len(messages) == 1 + 10 + 1


def test_chat_stream_yields_tokens_and_error(monkeypatch):
    monkeypatch.setattr("yuntai.agents.chat_agent.get_zhipu_client", lambda: object())
    monkeypatch.setattr(
        "yuntai.agents.chat_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: [],
    )

    ok_agent = ChatAgent(model=_FakeModel(stream_chunks=["你", "好"]), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    assert list(ok_agent.chat_stream("hi", include_memory=False)) == ["你", "好"]

    err_agent = ChatAgent(model=_FakeModel(boom=True), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    assert list(err_agent.chat_stream("hi", include_memory=False)) == ["聊天失败: stream-boom"]

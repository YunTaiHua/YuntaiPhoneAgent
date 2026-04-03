import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from yuntai.memory.conversation_memory import (
    ChatSessionMemory,
    ConversationMemoryManager,
    FreeChatMemory,
)


def test_conversation_memory_add_get_context_and_clear(monkeypatch):
    class _CallbackManager:
        def __init__(self):
            self.registered = []

        def register_handler(self, **kwargs):
            self.registered.append(kwargs)

        def get_callbacks(self, **kwargs):
            return ["cb"]

    cbm = _CallbackManager()
    monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: cbm)

    m = ConversationMemoryManager(max_history_length=3)
    m.add_message("user", "hello")
    m.add_message("assistant", "world")

    msgs = m.get_messages(limit=10)
    assert isinstance(msgs[0], HumanMessage)
    assert isinstance(msgs[1], AIMessage)
    assert "用户: hello" in m.get_history_context(limit=10)
    assert "助手: world" in m.get_history_context(limit=10)
    assert m.get_callbacks() == ["cb"]

    m.clear()
    assert m.get_messages() == []


def test_conversation_memory_load_forever_and_save_file_trim(tmp_path, monkeypatch):
    class _CallbackManager:
        def register_handler(self, **kwargs):
            return None

        def get_callbacks(self, **kwargs):
            return []

    monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())

    forever = tmp_path / "forever.txt"
    forever.write_text("line1", encoding="utf-8")
    m = ConversationMemoryManager(forever_memory_file=str(forever), max_history_length=2)
    assert m.get_forever_memory() == "line1"

    out = tmp_path / "history.json"
    m.save_to_file({"i": 1}, str(out))
    m.save_to_file({"i": 2}, str(out))
    m.save_to_file({"i": 3}, str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert [x["i"] for x in data] == [2, 3]


def test_free_chat_memory_and_chat_session_memory():
    calls = []
    fm = SimpleNamespace(
        get_recent_free_chats=lambda limit=5: [{"assistant_reply": "a"}],
        save_conversation_history=lambda data: calls.append(data),
        get_recent_conversation_history=lambda app, obj, limit=5: [{"target_app": app, "target_object": obj}],
    )

    free = FreeChatMemory(file_manager=fm)
    assert free.get_recent_chats(limit=1)[0]["assistant_reply"] == "a"
    free.save_chat("u", "r")
    assert calls[-1]["type"] == "free_chat"

    session = ChatSessionMemory(file_manager=fm)
    recent = session.get_recent_session("wx", "alice", limit=1)
    assert recent[0]["target_app"] == "wx"
    session.save_session("wx", "alice", "reply", ["m1"], cycle=2)
    assert calls[-1]["type"] == "chat_session"
    assert calls[-1]["cycle"] == 2

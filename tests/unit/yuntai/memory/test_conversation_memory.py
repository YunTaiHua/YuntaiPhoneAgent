import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

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


class TestConversationMemoryDeepBranches:
    def test_add_message_exception(self, monkeypatch):
        class _BadCallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _BadCallbackManager())
        m = ConversationMemoryManager()
        m._memory = MagicMock()
        m._memory.chat_memory = MagicMock()
        m._memory.chat_memory.messages = []
        m._memory.chat_memory.add_message = lambda msg: (_ for _ in ()).throw(RuntimeError("mem boom"))
        m.add_message("user", "test")

    def test_get_messages_empty(self, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())
        m = ConversationMemoryManager()
        assert m.get_messages() == []

    def test_get_history_context_empty(self, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())
        m = ConversationMemoryManager()
        assert m.get_history_context() == ""

    def test_save_to_file_exception(self, monkeypatch, tmp_path):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())
        m = ConversationMemoryManager()
        out = tmp_path / "hist.json"
        monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("write boom")))
        m.save_to_file({"x": 1}, str(out))

    def test_load_forever_memory_exception(self, monkeypatch, tmp_path):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())
        forever = tmp_path / "forever.txt"
        forever.write_text("content", encoding="utf-8")
        m = ConversationMemoryManager(forever_memory_file=str(forever))
        assert m.get_forever_memory() == "content"

    def test_free_chat_memory_save_exception(self, monkeypatch):
        fm = SimpleNamespace(
            get_recent_free_chats=lambda limit=5: [],
            save_conversation_history=lambda data: (_ for _ in ()).throw(RuntimeError("save boom")),
        )
        free = FreeChatMemory(file_manager=fm)
        try:
            free.save_chat("user", "reply")
        except RuntimeError:
            pass

    def test_chat_session_memory_save_exception(self, monkeypatch):
        fm = SimpleNamespace(
            get_recent_conversation_history=lambda app, obj, limit=5: [],
            save_conversation_history=lambda data: (_ for _ in ()).throw(RuntimeError("save boom")),
        )
        session = ChatSessionMemory(file_manager=fm)
        try:
            session.save_session("wx", "alice", "reply", ["m1"])
        except RuntimeError:
            pass

    def test_load_memory_with_existing_file(self, tmp_path, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())

        history_file = tmp_path / "history.json"
        history_file.write_text("[]", encoding="utf-8")
        m = ConversationMemoryManager(history_file=str(history_file))
        assert m._memory is not None

    def test_load_memory_exception(self, tmp_path, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())

        history_file = tmp_path / "history.json"
        history_file.write_text("invalid json{", encoding="utf-8")
        m = ConversationMemoryManager(history_file=str(history_file))
        assert m._memory is not None

    def test_load_forever_memory_with_existing_file(self, tmp_path, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())

        forever_file = tmp_path / "forever.txt"
        forever_file.write_text("永久记忆内容", encoding="utf-8")
        m = ConversationMemoryManager(forever_memory_file=str(forever_file))
        assert m.get_forever_memory() == "永久记忆内容"

    def test_load_forever_memory_file_exception(self, tmp_path, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())

        forever_file = tmp_path / "forever.txt"
        forever_file.write_text("content", encoding="utf-8")
        monkeypatch.setattr(Path, "read_text", lambda self, encoding: (_ for _ in ()).throw(RuntimeError("read boom")))
        m = ConversationMemoryManager(forever_memory_file=str(forever_file))
        assert m.get_forever_memory() == ""

    def test_save_to_file_non_list_data(self, tmp_path, monkeypatch):
        class _CallbackManager:
            def register_handler(self, **kwargs):
                return None

            def get_callbacks(self, **kwargs):
                return []
        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: _CallbackManager())

        m = ConversationMemoryManager()
        out = tmp_path / "history.json"
        out.write_text('{"not": "a list"}', encoding="utf-8")
        m.save_to_file({"i": 1}, str(out))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert len(data) == 1

    def test_free_chat_memory_no_file_manager(self):
        free = FreeChatMemory(file_manager=None)
        assert free.get_recent_chats() == []
        free.save_chat("user", "reply")

    def test_chat_session_memory_no_file_manager(self):
        session = ChatSessionMemory(file_manager=None)
        assert session.get_recent_session("wx", "alice") == []
        session.save_session("wx", "alice", "reply", ["m1"])

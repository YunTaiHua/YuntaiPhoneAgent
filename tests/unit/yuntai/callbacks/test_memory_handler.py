from types import SimpleNamespace

from yuntai.callbacks.memory_handler import (
    FileBasedMemoryCallbackHandler,
    MemoryCallbackHandler,
    SessionMemoryCallbackHandler,
)


def _result(text: str):
    return SimpleNamespace(generations=[[SimpleNamespace(text=text)]])


def test_memory_callback_save_and_history_trim():
    calls = []
    memory_manager = SimpleNamespace(add_message=lambda role, content: calls.append((role, content)))
    handler = MemoryCallbackHandler(memory_manager=memory_manager, auto_save=True, max_history=1)

    handler.on_llm_start({}, ["user1"])
    handler.on_llm_end(_result("ai1"))
    handler.on_llm_start({}, ["user2"])
    handler.on_llm_end(_result("ai2"))

    assert calls[0] == ("user", "user1")
    assert calls[1] == ("assistant", "ai1")
    assert len(handler.get_conversation_history(10)) == 1
    assert handler.get_conversation_history(1)[0]["user"] == "user2"


def test_memory_callback_auto_save_disabled_and_clear():
    handler = MemoryCallbackHandler(memory_manager=object(), auto_save=False)
    handler.on_llm_start({}, ["u"])
    handler.on_llm_end(_result("a"))
    assert handler.get_conversation_history() == []

    handler._conversation_history = [{"timestamp": "t", "user": "u", "assistant": "a"}]
    handler.clear_history()
    assert handler.get_conversation_history() == []


def test_session_memory_handler_session_ops():
    handler = SessionMemoryCallbackHandler(memory_manager=object(), auto_save=True, max_history=2)
    handler.set_session("s1")
    handler.on_llm_start({}, ["u1"])
    handler.on_llm_end(_result("a1"))
    handler.on_llm_start({}, ["u2"])
    handler.on_llm_end(_result("a2"))
    handler.on_llm_start({}, ["u3"])
    handler.on_llm_end(_result("a3"))

    session = handler.get_session_history("s1", limit=10)
    assert len(session) == 2
    assert session[-1]["assistant"] == "a3"

    handler.clear_session("s1")
    assert handler.get_session_history("s1") == []
    handler.clear_all_sessions()
    assert handler.get_all_sessions() == {}


def test_file_based_memory_handler_calls_file_manager(monkeypatch):
    saved = []
    file_manager = SimpleNamespace(save_conversation_history=lambda data: saved.append(data))
    handler = FileBasedMemoryCallbackHandler(
        file_manager=file_manager,
        memory_manager=object(),
        auto_save=True,
    )

    def fake_super_save(self):
        return None
    monkeypatch.setattr(MemoryCallbackHandler, "_save_to_memory", fake_super_save)

    handler.on_llm_start({}, ["hello"])
    handler.on_llm_end(_result("world"))

    assert saved
    assert saved[0]["type"] == "free_chat"
    assert saved[0]["user_input"] == "hello"
    assert saved[0]["assistant_reply"] == "world"


class TestMemoryHandlerCoverageGaps:
    def test_save_to_memory_empty_input_returns(self):
        handler = MemoryCallbackHandler()
        handler._current_user_input = ""
        handler._current_ai_response = "resp"
        handler._save_to_memory()

    def test_save_to_memory_exception(self):
        handler = MemoryCallbackHandler()
        handler._current_user_input = "user"
        handler._current_ai_response = "ai"
        handler._memory = SimpleNamespace(
            append=lambda item: (_ for _ in ()).throw(RuntimeError("mem boom"))
        )
        handler._save_to_memory()

    def test_get_messages_for_langchain(self):
        handler = MemoryCallbackHandler()
        handler._conversation_history = [
            {"user": "hello", "assistant": "hi"},
            {"user": "bye", "assistant": "bye"},
        ]
        messages = handler.get_messages_for_langchain(limit=10)
        assert len(messages) == 4
        assert messages[0].content == "hello"
        assert messages[1].content == "hi"

    def test_session_handler_empty_input_returns(self):
        handler = SessionMemoryCallbackHandler()
        handler._current_user_input = ""
        handler._current_ai_response = "resp"
        handler._save_to_memory()

    def test_session_handler_new_session_init(self):
        handler = SessionMemoryCallbackHandler()
        handler._current_session_id = "sess1"
        handler._current_user_input = "user"
        handler._current_ai_response = "ai"
        handler._save_to_memory()
        assert "sess1" in handler._sessions
        assert len(handler._sessions["sess1"]) == 1

    def test_session_handler_get_current_session(self):
        handler = SessionMemoryCallbackHandler()
        handler._current_session_id = "sess1"
        assert handler.get_current_session() == "sess1"

    def test_session_handler_get_session_history_empty(self):
        handler = SessionMemoryCallbackHandler()
        assert handler.get_session_history("") == []
        assert handler.get_session_history("nonexistent") == []

    def test_file_handler_empty_input_returns(self):
        handler = FileBasedMemoryCallbackHandler(file_manager=SimpleNamespace(
            save_conversation_history=lambda x: None
        ))
        handler._current_user_input = ""
        handler._current_ai_response = "resp"
        handler._save_to_memory()

    def test_file_handler_save_exception(self):
        handler = FileBasedMemoryCallbackHandler(file_manager=SimpleNamespace(
            save_conversation_history=lambda x: (_ for _ in ()).throw(RuntimeError("file boom"))
        ))
        handler._current_user_input = "user"
        handler._current_ai_response = "ai"
        handler._save_to_memory()

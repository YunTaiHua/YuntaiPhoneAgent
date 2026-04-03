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

    # Keep current prompt/response values intact after parent save path.
    def fake_super_save(self):
        return None
    monkeypatch.setattr(MemoryCallbackHandler, "_save_to_memory", fake_super_save)

    handler.on_llm_start({}, ["hello"])
    handler.on_llm_end(_result("world"))

    assert saved
    assert saved[0]["type"] == "free_chat"
    assert saved[0]["user_input"] == "hello"
    assert saved[0]["assistant_reply"] == "world"

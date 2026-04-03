import json

from yuntai.services.file_manager import FileManager


def test_safe_read_json_file_returns_default_for_missing_or_invalid(tmp_path):
    manager = FileManager()
    missing = tmp_path / "missing.json"
    assert manager.safe_read_json_file(str(missing), {"x": 1}) == {"x": 1}

    bad = tmp_path / "bad.json"
    bad.write_text("{invalid", encoding="utf-8")
    assert manager.safe_read_json_file(str(bad), [1]) == [1]


def test_safe_write_json_file_creates_parent_and_writes(tmp_path):
    manager = FileManager()
    path = tmp_path / "a" / "b" / "history.json"

    ok = manager.safe_write_json_file(str(path), {"k": "v"})

    assert ok is True
    assert json.loads(path.read_text(encoding="utf-8")) == {"k": "v"}


def test_save_conversation_history_trims_to_max(monkeypatch):
    manager = FileManager()
    monkeypatch.setattr("yuntai.services.file_manager.MAX_HISTORY_LENGTH", 2)

    state = {"sessions": [], "free_chats": []}

    def fake_read(_filepath, _default):
        return {
            "sessions": list(state["sessions"]),
            "free_chats": list(state["free_chats"]),
        }

    def fake_write(_filepath, data):
        state.clear()
        state.update(data)
        return True

    monkeypatch.setattr(manager, "safe_read_json_file", fake_read)
    monkeypatch.setattr(manager, "safe_write_json_file", fake_write)

    manager.save_conversation_history({"type": "chat_session", "timestamp": "1", "target_app": "a", "target_object": "b"})
    manager.save_conversation_history({"type": "chat_session", "timestamp": "2", "target_app": "a", "target_object": "b"})
    manager.save_conversation_history({"type": "chat_session", "timestamp": "3", "target_app": "a", "target_object": "b"})

    assert [x["timestamp"] for x in state["sessions"]] == ["2", "3"]


def test_get_recent_conversation_history_filters_and_sorts(monkeypatch):
    manager = FileManager()
    history = {
        "sessions": [
            {"target_app": "wx", "target_object": "alice", "timestamp": "2026-01-01 10:00:00"},
            {"target_app": "wx", "target_object": "bob", "timestamp": "2026-01-01 10:01:00"},
            {"target_app": "wx", "target_object": "alice", "timestamp": "2026-01-01 10:02:00"},
        ],
        "free_chats": [],
    }
    monkeypatch.setattr(manager, "safe_read_json_file", lambda *_: history)

    result = manager.get_recent_conversation_history("wx", "alice", limit=5)
    assert [x["timestamp"] for x in result] == ["2026-01-01 10:02:00", "2026-01-01 10:00:00"]


def test_get_recent_free_chats_sorted_desc(monkeypatch):
    manager = FileManager()
    history = {
        "sessions": [],
        "free_chats": [
            {"timestamp": "2026-01-01 10:00:00", "assistant_reply": "a"},
            {"timestamp": "2026-01-01 10:02:00", "assistant_reply": "b"},
        ],
    }
    monkeypatch.setattr(manager, "safe_read_json_file", lambda *_: history)

    result = manager.get_recent_free_chats(limit=1)
    assert result[0]["assistant_reply"] == "b"

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

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


class TestFileManagerDeepBranches:
    def test_safe_read_json_file_with_valid_json(self, tmp_path):
        manager = FileManager()
        valid = tmp_path / "valid.json"
        valid.write_text('{"key": "value"}', encoding="utf-8")
        result = manager.safe_read_json_file(str(valid), {})
        assert result == {"key": "value"}

    def test_safe_write_json_file_creates_dirs(self, tmp_path):
        manager = FileManager()
        path = tmp_path / "deep" / "nested" / "dir" / "file.json"
        ok = manager.safe_write_json_file(str(path), {"test": 1})
        assert ok is True
        assert path.exists()

    def test_get_recent_conversation_history_empty(self, monkeypatch):
        manager = FileManager()
        monkeypatch.setattr(manager, "safe_read_json_file", lambda *a: {"sessions": [], "free_chats": []})
        result = manager.get_recent_conversation_history("wx", "alice")
        assert result == []

    def test_get_recent_free_chats_empty(self, monkeypatch):
        manager = FileManager()
        monkeypatch.setattr(manager, "safe_read_json_file", lambda *a: {"sessions": [], "free_chats": []})
        result = manager.get_recent_free_chats()
        assert result == []

    def test_save_conversation_history_free_chat(self, monkeypatch):
        manager = FileManager()
        saved = []
        monkeypatch.setattr(manager, "safe_read_json_file", lambda *a: {"sessions": [], "free_chats": []})
        monkeypatch.setattr(manager, "safe_write_json_file", lambda p, d: saved.append(d) or True)
        manager.save_conversation_history({"type": "free_chat", "user_input": "test"})
        assert len(saved) == 1

    def test_init_file_system_creates_dirs(self, tmp_path, monkeypatch):
        manager = FileManager()
        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", tmp_path / "temp")
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", tmp_path / "logs")
        monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", tmp_path / "history.json")
        monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", tmp_path / "config.json")
        manager.init_file_system()
        assert (tmp_path / "temp").exists()
        assert (tmp_path / "logs").exists()

    def test_init_file_system_with_empty_json_file(self, tmp_path, monkeypatch):
        manager = FileManager()
        history_file = tmp_path / "history.json"
        history_file.write_text("", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", tmp_path / "temp")
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", tmp_path / "logs")
        monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", history_file)
        monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", tmp_path / "config.json")
        manager.init_file_system()
        content = json.loads(history_file.read_text(encoding="utf-8"))
        assert content == {"sessions": [], "free_chats": []}

    def test_init_file_system_with_invalid_json_file(self, tmp_path, monkeypatch):
        manager = FileManager()
        history_file = tmp_path / "history.json"
        history_file.write_text("{invalid json", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", tmp_path / "temp")
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", tmp_path / "logs")
        monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", history_file)
        monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", tmp_path / "config.json")
        manager.init_file_system()
        content = json.loads(history_file.read_text(encoding="utf-8"))
        assert content == {"sessions": [], "free_chats": []}
        backup_files = list(tmp_path.glob("history.backup_*.json"))
        assert len(backup_files) == 1

    def test_init_file_system_exception(self, tmp_path, monkeypatch):
        manager = FileManager()
        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", tmp_path / "temp")
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", tmp_path / "logs")
        monkeypatch.setattr(Path, "exists", lambda self: (_ for _ in ()).throw(RuntimeError("init boom")))
        manager.init_file_system()

    def test_cleanup_record_files_success(self, tmp_path, monkeypatch):
        manager = FileManager()
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "record_1.txt").write_text("log", encoding="utf-8")
        (logs_dir / "other.txt").write_text("other", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", logs_dir)
        manager.cleanup_record_files()
        assert not (logs_dir / "record_1.txt").exists()
        assert (logs_dir / "other.txt").exists()

    def test_cleanup_record_files_exception(self, tmp_path, monkeypatch):
        manager = FileManager()
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", logs_dir)
        monkeypatch.setattr(Path, "iterdir", lambda self: (_ for _ in ()).throw(RuntimeError("cleanup boom")))
        manager.cleanup_record_files()

    def test_read_forever_memory_with_content(self, tmp_path, monkeypatch):
        manager = FileManager()
        forever_file = tmp_path / "forever.txt"
        forever_file.write_text("line1\nline2\n", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", forever_file)
        result = manager.read_forever_memory()
        assert "永久记忆" in result
        assert "line1" in result

    def test_read_forever_memory_empty_file(self, tmp_path, monkeypatch):
        manager = FileManager()
        forever_file = tmp_path / "forever.txt"
        forever_file.write_text("", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", forever_file)
        result = manager.read_forever_memory()
        assert result == ""

    def test_read_forever_memory_file_not_found(self, tmp_path, monkeypatch):
        manager = FileManager()
        forever_file = tmp_path / "nonexistent.txt"
        monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", forever_file)
        result = manager.read_forever_memory()
        assert result == ""

    def test_read_forever_memory_exception(self, tmp_path, monkeypatch):
        manager = FileManager()
        forever_file = tmp_path / "forever.txt"
        forever_file.write_text("content", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", forever_file)
        monkeypatch.setattr(Path, "read_text", lambda self, encoding: (_ for _ in ()).throw(RuntimeError("read boom")))
        result = manager.read_forever_memory()
        assert result == ""

    def test_safe_read_json_file_empty_content(self, tmp_path):
        manager = FileManager()
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("", encoding="utf-8")
        result = manager.safe_read_json_file(str(empty_file), {"default": 1})
        assert result == {"default": 1}

    def test_safe_write_json_file_exception(self, tmp_path, monkeypatch):
        manager = FileManager()
        path = tmp_path / "out.json"
        monkeypatch.setattr(Path, "write_text", lambda self, content, encoding: (_ for _ in ()).throw(RuntimeError("write boom")))
        result = manager.safe_write_json_file(str(path), {"x": 1})
        assert result is False

    def test_save_conversation_history_write_failure(self, monkeypatch):
        manager = FileManager()
        monkeypatch.setattr(manager, "safe_read_json_file", lambda *a: {"sessions": [], "free_chats": []})
        monkeypatch.setattr(manager, "safe_write_json_file", lambda p, d: False)
        manager.save_conversation_history({"type": "chat_session", "timestamp": "1"})

    def test_save_conversation_history_exception(self, monkeypatch):
        manager = FileManager()
        monkeypatch.setattr(manager, "safe_read_json_file", lambda *a: (_ for _ in ()).throw(RuntimeError("read boom")))
        manager.save_conversation_history({"type": "chat_session", "timestamp": "1"})

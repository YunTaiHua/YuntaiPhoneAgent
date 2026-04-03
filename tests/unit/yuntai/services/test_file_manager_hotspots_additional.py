import json
from pathlib import Path

from yuntai.services.file_manager import FileManager


def test_init_file_system_rebuild_invalid_history_and_create_connection(tmp_path, monkeypatch):
    temp_dir = tmp_path / "temp"
    logs_dir = temp_dir / "record_logs"
    hist_file = temp_dir / "history.json"
    conn_file = temp_dir / "connection.json"

    temp_dir.mkdir(parents=True)
    hist_file.write_text("{broken", encoding="utf-8")

    monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", temp_dir)
    monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", logs_dir)
    monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", hist_file)
    monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", conn_file)

    FileManager().init_file_system()

    history = json.loads(hist_file.read_text(encoding="utf-8"))
    assert history == {"sessions": [], "free_chats": []}
    assert conn_file.exists()
    assert logs_dir.exists()
    backups = list(hist_file.parent.glob("history.backup_*.json"))
    assert backups


def test_cleanup_record_files_and_read_forever_memory(tmp_path, monkeypatch):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    (logs_dir / "record_a.txt").write_text("x", encoding="utf-8")
    (logs_dir / "record_b.log").write_text("x", encoding="utf-8")
    (logs_dir / "other.txt").write_text("x", encoding="utf-8")

    monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", logs_dir)
    FileManager().cleanup_record_files()
    assert not (logs_dir / "record_a.txt").exists()
    assert (logs_dir / "record_b.log").exists()
    assert (logs_dir / "other.txt").exists()

    forever = tmp_path / "forever.txt"
    forever.write_text("line1\n\n line2 ", encoding="utf-8")
    monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", forever)
    text = FileManager().read_forever_memory()
    assert "永久记忆" in text
    assert "1. line1" in text
    assert "3. line2" in text


def test_save_record_to_log_success_and_exception(tmp_path, monkeypatch):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", logs_dir)

    f = FileManager().save_record_to_log(3, "hello", "wx", "alice")
    assert f.startswith("record_")
    assert (logs_dir / f).exists()

    class _BadPath:
        def __truediv__(self, _other):
            raise RuntimeError("bad")

    monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", _BadPath())
    assert FileManager().save_record_to_log(1, "x", "a", "b") == ""


def test_safe_read_write_and_recent_error_paths(monkeypatch, tmp_path):
    fm = FileManager()

    class _BadReadPath:
        def exists(self):
            return True

        def read_text(self, **_kwargs):
            raise UnicodeDecodeError("utf-8", b"x", 0, 1, "bad")

    monkeypatch.setattr("yuntai.services.file_manager.Path", lambda *_args, **_kwargs: _BadReadPath())
    assert fm.safe_read_json_file("x.json", {"d": 1}) == {"d": 1}

    class _BadMove:
        @staticmethod
        def move(*_args, **_kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr("yuntai.services.file_manager.shutil", _BadMove)
    assert fm.safe_write_json_file(str(tmp_path / "a.json"), {"x": 1}) is False

    monkeypatch.setattr(fm, "safe_read_json_file", lambda *_: (_ for _ in ()).throw(RuntimeError("boom")))
    assert fm.get_recent_conversation_history("a", "b") == []
    assert fm.get_recent_free_chats() == []


def test_save_conversation_history_write_failed(monkeypatch):
    fm = FileManager()
    state = {"sessions": [], "free_chats": []}
    monkeypatch.setattr(fm, "safe_read_json_file", lambda *_: state)
    monkeypatch.setattr(fm, "safe_write_json_file", lambda *_: False)

    fm.save_conversation_history({"type": "free_chat", "timestamp": "t"})
    assert state["free_chats"]

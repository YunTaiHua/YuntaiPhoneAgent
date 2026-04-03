from pathlib import Path

import pytest

from yuntai.managers.tts_database import TTSDatabaseManager


def _config(tmp_path):
    return {
        "gpt_model_dir": str(tmp_path / "gpt"),
        "sovits_model_dir": str(tmp_path / "sovits"),
        "ref_audio_root": str(tmp_path / "audio"),
        "ref_text_root": str(tmp_path / "text"),
        "output_path": str(tmp_path / "out"),
    }


def test_init_tts_files_database_scans_files_and_creates_dirs(tmp_path):
    cfg = _config(tmp_path)
    Path(cfg["gpt_model_dir"]).mkdir(parents=True)
    Path(cfg["sovits_model_dir"]).mkdir(parents=True)
    Path(cfg["ref_audio_root"]).mkdir(parents=True)
    Path(cfg["ref_text_root"]).mkdir(parents=True)

    (Path(cfg["gpt_model_dir"]) / "a.ckpt").write_bytes(b"x")
    (Path(cfg["sovits_model_dir"]) / "b.pth").write_bytes(b"x")
    (Path(cfg["ref_audio_root"]) / "c.wav").write_bytes(b"x")
    (Path(cfg["ref_audio_root"]) / "d.mp3").write_bytes(b"x")
    (Path(cfg["ref_text_root"]) / "e.txt").write_text("hello", encoding="utf-8")

    manager = TTSDatabaseManager(cfg)

    assert manager.init_tts_files_database() is True
    assert "a.ckpt" in manager.tts_files_database["gpt"]
    assert "b.pth" in manager.tts_files_database["sovits"]
    assert "c.wav" in manager.tts_files_database["audio"]
    assert "d.mp3" in manager.tts_files_database["audio"]
    assert "e.txt" in manager.tts_files_database["text"]


def test_get_cached_text_caches_result_and_raises_io_error(tmp_path, monkeypatch):
    cfg = _config(tmp_path)
    manager = TTSDatabaseManager(cfg)
    text_file = tmp_path / "a.txt"
    text_file.write_text(" first ", encoding="utf-8")

    assert manager.get_cached_text(str(text_file)) == "first"

    text_file.write_text("second", encoding="utf-8")
    assert manager.get_cached_text(str(text_file)) == "first"

    def _raise(*args, **kwargs):
        raise IOError("boom")

    monkeypatch.setattr(Path, "read_text", _raise)
    with pytest.raises(IOError):
        manager.get_cached_text(str(tmp_path / "missing.txt"))


def test_set_get_model_filename_and_synthesized_files_flow(tmp_path):
    cfg = _config(tmp_path)
    out = Path(cfg["output_path"])
    out.mkdir(parents=True)
    (out / "b.wav").write_bytes(b"x")
    (out / "a.wav").write_bytes(b"x")
    (out / "x.txt").write_text("ignore", encoding="utf-8")

    manager = TTSDatabaseManager(cfg)
    manager.tts_files_database = {
        "gpt": {"g.ckpt": "/abs/g.ckpt"},
        "sovits": {"s.pth": "/abs/s.pth"},
        "audio": {"r.wav": "/abs/r.wav"},
        "text": {"r.txt": "/abs/r.txt"},
    }

    assert manager.set_current_model("gpt", "g.ckpt") is True
    assert manager.set_current_model("sovits", "s.pth") is True
    assert manager.set_current_model("audio", "r.wav") is True
    assert manager.set_current_model("text", "r.txt") is True
    assert manager.set_current_model("gpt", "missing.ckpt") is False
    assert manager.set_current_model("unknown", "x") is False

    assert manager.get_current_model("gpt") == "/abs/g.ckpt"
    assert manager.get_current_model("unknown") is None
    assert manager.get_model_filename("gpt") == "g.ckpt"
    assert manager.get_model_filename("unknown") == "未选择"

    loaded = manager.load_synthesized_files()
    assert {name for _, name in loaded} == {"b.wav", "a.wav"}

    manager.add_synthesized_file(str(out / "new.wav"))
    assert manager.tts_synthesized_files[-1][1] == "new.wav"

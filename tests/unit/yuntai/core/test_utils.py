import importlib.util
import subprocess
from pathlib import Path


UTILS_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "core" / "utils.py"


def _load_utils_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, UTILS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_system_requirements_passes_with_adb(monkeypatch):
    module = _load_utils_module("test_utils_requirements_ok")

    monkeypatch.setattr(module.shutil, "which", lambda _: "adb")

    class _Result:
        returncode = 0

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: _Result())

    assert module.Utils().check_system_requirements() is True


def test_check_system_requirements_fails_when_no_adb(monkeypatch):
    module = _load_utils_module("test_utils_requirements_no_adb")
    monkeypatch.setattr(module.shutil, "which", lambda _: None)

    assert module.Utils().check_system_requirements() is False


def test_check_hdc_handles_timeout(monkeypatch):
    module = _load_utils_module("test_utils_hdc_timeout")
    monkeypatch.setattr(module.shutil, "which", lambda _: "hdc")

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["hdc", "-v"], timeout=1)

    monkeypatch.setattr(module.subprocess, "run", _raise_timeout)

    assert module.Utils().check_hdc() is False


def test_check_model_api_success_and_failure(monkeypatch):
    module = _load_utils_module("test_utils_model_api")

    class _ClientOK:
        def __init__(self, **kwargs):
            class _Chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        return type("Resp", (), {"choices": [object()]})()

            self.chat = _Chat()

    monkeypatch.setattr(module.openai, "OpenAI", _ClientOK)
    assert module.Utils().check_model_api("http://x", "m", "k") is True

    class _ClientBoom:
        def __init__(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(module.openai, "OpenAI", _ClientBoom)
    assert module.Utils().check_model_api("http://x", "m", "k") is False


def test_tts_state_manager_singleton_and_status():
    module = _load_utils_module("test_utils_tts_singleton")
    module.TTSStateManager._instance = None
    module._tts_state_manager = None

    a = module.TTSStateManager()
    b = module.TTSStateManager()
    assert a is b

    a.tts_page_synthesizing = True
    a.is_tts_synthesizing = True
    a.is_playing_audio = True
    a.add_synthesized_file("/tmp/a.wav", "a.wav")

    status = a.get_status_dict()
    assert status["tts_page_synthesizing"] is True
    assert status["is_tts_synthesizing"] is True
    assert status["is_playing_audio"] is True
    assert status["tts_synthesized_files_count"] == 1


def test_load_synthesized_files_and_cleanup(tmp_path):
    module = _load_utils_module("test_utils_load_files")
    module.TTSStateManager._instance = None
    module._tts_state_manager = None

    (tmp_path / "b.wav").write_bytes(b"x")
    (tmp_path / "a.wav").write_bytes(b"x")
    (tmp_path / "note.txt").write_text("ignore", encoding="utf-8")

    files = module.load_synthesized_files(str(tmp_path))
    assert [name for _, name in files] == ["b.wav", "a.wav"]

    module.cleanup_tts_resources()
    status = module.get_current_tts_status()
    assert status["tts_page_synthesizing"] is False
    assert status["tts_synthesized_files_count"] == 0

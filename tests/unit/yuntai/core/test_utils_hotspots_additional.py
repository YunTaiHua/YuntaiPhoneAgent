import importlib.util
import subprocess
from pathlib import Path


UTILS_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "core" / "utils.py"


def _load_utils_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, UTILS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_enable_windows_color_and_adb_failure_paths(monkeypatch):
    module = _load_utils_module("test_utils_hot_more1")
    monkeypatch.setattr(module.sys, "platform", "win32")

    class _K:
        @staticmethod
        def GetStdHandle(_x):
            return 1

        @staticmethod
        def SetConsoleMode(_h, _m):
            return 1

    class _Ctypes:
        windll = type("W", (), {"kernel32": _K})

    monkeypatch.setattr(module, "ctypes", _Ctypes, raising=False)
    module.Utils().enable_windows_color()

    monkeypatch.setattr(module.shutil, "which", lambda _: "adb")
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 1})())
    assert module.Utils().check_system_requirements() is False

    def _raise_timeout(*_a, **_k):
        raise subprocess.TimeoutExpired(cmd=["adb"], timeout=1)

    monkeypatch.setattr(module.subprocess, "run", _raise_timeout)
    assert module.Utils().check_system_requirements() is False


def test_hdc_and_model_api_edge_paths(monkeypatch):
    module = _load_utils_module("test_utils_hot_more2")

    monkeypatch.setattr(module.shutil, "which", lambda _: "hdc")
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 1})())
    assert module.Utils().check_hdc() is False

    def _raise_fnf(*_a, **_k):
        raise FileNotFoundError("hdc")

    monkeypatch.setattr(module.subprocess, "run", _raise_fnf)
    assert module.Utils().check_hdc() is False

    class _ClientNoChoices:
        def __init__(self, **_kwargs):
            class _Chat:
                class completions:
                    @staticmethod
                    def create(**_kwargs):
                        return type("Resp", (), {"choices": []})()

            self.chat = _Chat()

    monkeypatch.setattr(module.openai, "OpenAI", _ClientNoChoices)
    assert module.Utils().check_model_api("http://x", "m", "k") is False


def test_tts_state_manager_helpers_more(tmp_path):
    module = _load_utils_module("test_utils_hot_more3")
    module.TTSStateManager._instance = None
    module._tts_state_manager = None

    manager = module.get_tts_state_manager()
    assert manager is module.get_tts_state_manager()

    manager.set_synthesized_files([("/a.wav", "a.wav")])
    assert manager.get_synthesized_files_count() == 1
    assert manager.get_synthesized_files()[0][1] == "a.wav"

    manager.clear_synthesized_files()
    assert manager.get_synthesized_files_count() == 0

    files = module.load_synthesized_files(str(tmp_path / "missing"))
    assert files == []

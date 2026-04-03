import importlib.util
from pathlib import Path

import pytest


CONFIG_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "core" / "config.py"


def _load_config_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, CONFIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_import_raises_when_api_key_missing(monkeypatch):
    original_getenv = __import__("os").getenv

    def _fake_getenv(key, default=None):
        if key == "ZHIPU_API_KEY":
            return None
        return original_getenv(key, default)

    monkeypatch.setattr("os.getenv", _fake_getenv)

    with pytest.raises(ValueError, match="ZHIPU_API_KEY"):
        _load_config_module("test_config_missing_key")


def test_import_builds_paths_and_defaults(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key-123456")
    monkeypatch.delenv("PHONE_AGENT_DEVICE_TYPE", raising=False)

    module = _load_config_module("test_config_defaults")

    assert module.APP_VERSION
    assert module.TEMP_DIR.name == "temp"
    assert module.DEFAULT_DEVICE_TYPE == module.DEVICE_TYPE_ANDROID
    assert module.CONVERSATION_HISTORY_FILE.name == "conversation_history.json"


def test_validate_config_returns_false_on_invalid_paths_or_short_key(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key-123456")
    module = _load_config_module("test_config_validate_false")

    module.GPT_SOVITS_ROOT = Path("/does/not/exist")
    module.ZHIPU_API_KEY = "short"

    assert module.validate_config() is False


def test_validate_config_returns_true_when_checks_pass(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key-123456")
    module = _load_config_module("test_config_validate_true")

    module.GPT_SOVITS_ROOT = None
    module.SCRCPY_PATH = None
    module.GPT_MODEL_DIR = None
    module.SOVITS_MODEL_DIR = None
    module.REF_AUDIO_ROOT = None
    module.ZHIPU_API_KEY = "valid-long-api-key"

    assert module.validate_config() is True


def test_check_required_env_vars_raises_for_missing_required(monkeypatch):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key-123456")
    module = _load_config_module("test_config_required_env")

    monkeypatch.delenv("ZHIPU_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ZHIPU_API_KEY"):
        module.check_required_env_vars()


def test_print_config_summary_outputs_expected_lines(monkeypatch, capsys):
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key-123456")
    module = _load_config_module("test_config_print_summary")

    module.print_config_summary()
    out = capsys.readouterr().out

    assert "配置摘要" in out
    assert "项目根目录" in out
    assert module.ZHIPU_MODEL in out

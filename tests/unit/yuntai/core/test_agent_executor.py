import importlib.util
import os
import sys
import threading
import types
from pathlib import Path

import pytest

AGENT_EXECUTOR_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "core" / "agent_executor.py"


def _load_agent_executor_module(module_name: str):
    fake_phone_agent = types.ModuleType("phone_agent")
    fake_phone_agent_model = types.ModuleType("phone_agent.model")
    fake_phone_agent_agent = types.ModuleType("phone_agent.agent")
    fake_config = types.ModuleType("yuntai.core.config")
    fake_prompt = types.ModuleType("yuntai.prompts.agent_executor_prompt")

    class _ModelConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class _AgentConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class _PhoneAgent:
        def __init__(self, model_config, agent_config):
            self.model_config = model_config
            self.agent_config = agent_config

        def run(self, task):
            return task

        def reset(self):
            return None

    fake_phone_agent.PhoneAgent = _PhoneAgent
    fake_phone_agent_model.ModelConfig = _ModelConfig
    fake_phone_agent_agent.AgentConfig = _AgentConfig
    fake_config.DEVICE_TYPE_ANDROID = "android"
    fake_prompt.CHAT_MESSAGE_PROMPT = "PROMPT"

    original = {
        "phone_agent": sys.modules.get("phone_agent"),
        "phone_agent.model": sys.modules.get("phone_agent.model"),
        "phone_agent.agent": sys.modules.get("phone_agent.agent"),
        "yuntai.core.config": sys.modules.get("yuntai.core.config"),
        "yuntai.prompts.agent_executor_prompt": sys.modules.get("yuntai.prompts.agent_executor_prompt"),
    }
    sys.modules["phone_agent"] = fake_phone_agent
    sys.modules["phone_agent.model"] = fake_phone_agent_model
    sys.modules["phone_agent.agent"] = fake_phone_agent_agent
    sys.modules["yuntai.core.config"] = fake_config
    sys.modules["yuntai.prompts.agent_executor_prompt"] = fake_prompt

    try:
        spec = importlib.util.spec_from_file_location(module_name, AGENT_EXECUTOR_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in original.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


@pytest.fixture
def agent_executor_module():
    return _load_agent_executor_module("test_agent_executor_shared")


@pytest.fixture(autouse=True)
def _reset_agent_executor_state(agent_executor_module):
    cls = agent_executor_module.AgentExecutor
    cls._cleanup_stdin_pipe()
    cls._stdin_read = None
    cls._stdin_write = None
    cls._original_stdin = None
    cls._user_confirmation_event.clear()
    cls._is_waiting_for_confirmation.clear()

    yield

    cls._cleanup_stdin_pipe()
    cls._stdin_read = None
    cls._stdin_write = None
    cls._original_stdin = None
    cls._user_confirmation_event.clear()
    cls._is_waiting_for_confirmation.clear()


def test_user_confirm_without_pipe_returns_false_and_sets_event(agent_executor_module):
    module = agent_executor_module
    module.AgentExecutor._stdin_write = None
    module.AgentExecutor._user_confirmation_event.clear()
    module.AgentExecutor._is_waiting_for_confirmation.set()

    ok = module.AgentExecutor.user_confirm()

    assert ok is False
    assert module.AgentExecutor._user_confirmation_event.is_set()
    assert not module.AgentExecutor._is_waiting_for_confirmation.is_set()


def test_pipe_setup_and_cleanup_restores_stdin(agent_executor_module):
    module = agent_executor_module
    original_stdin = sys.stdin

    module.AgentExecutor._cleanup_stdin_pipe()
    module.AgentExecutor._setup_stdin_pipe()

    assert module.AgentExecutor.is_pipe_ready() is True
    assert module.AgentExecutor._stdin_write is not None

    module.AgentExecutor._cleanup_stdin_pipe()

    assert module.AgentExecutor.is_pipe_ready() is False
    assert sys.stdin is original_stdin


def test_execute_agent_handles_empty_task(agent_executor_module):
    module = agent_executor_module
    executor = module.AgentExecutor()

    class _Agent:
        def run(self, task):
            raise AssertionError("should not run")

        def reset(self):
            return None

    result, logs = executor._execute_agent("   ", _Agent())
    assert result == "指令为空"
    assert logs == ["指令为空"]


def test_execute_agent_adds_prompt_and_filters_output(agent_executor_module):
    module = agent_executor_module
    executor = module.AgentExecutor()
    captured = {"task": None, "reset": False}

    raw = (
        "prefix\n"
        "==================================================\n"
        "💭 思考过程:\n"
        "--------------------------------------------------\n"
        "thinking\n"
        "==================================================\n"
        "middle\n"
        "==================================================\n"
        "⏱️  性能指标:\n"
        "--------------------------------------------------\n"
        "metrics\n"
        "==================================================\n"
        "\n\n\nend"
    )

    class _Agent:
        def run(self, task):
            captured["task"] = task
            return raw

        def reset(self):
            captured["reset"] = True

    filtered, logs = executor._execute_agent("聊天任务", _Agent())

    assert "PROMPT" in captured["task"]
    assert captured["reset"] is True
    assert "prefix" in filtered
    assert "middle" in filtered
    assert filtered.endswith("end")
    assert "思考过程" not in filtered
    assert "性能指标" not in filtered
    assert "thinking" not in filtered
    assert "metrics" not in filtered
    assert logs == [raw, filtered]


def test_phone_agent_exec_returns_error_on_exception(monkeypatch, agent_executor_module):
    module = agent_executor_module
    executor = module.AgentExecutor()

    class _Args:
        base_url = "http://x"
        model = "m"
        apikey = "k"
        lang = "cn"
        max_steps = 3

    monkeypatch.setattr(executor, "_exec_android_agent", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    result, logs = executor.phone_agent_exec("task", _Args(), "chat", "device-1")

    assert "任务执行失败" in result
    assert logs == ["boom"]
    assert module.AgentExecutor.is_pipe_ready() is False


class TestAgentExecutorCoverageGaps:
    def test_set_device_type(self, agent_executor_module):
        executor = agent_executor_module.AgentExecutor()
        executor.set_device_type("harmony")
        assert executor.device_type == "harmony"

    def test_cleanup_stdin_pipe_oserror(self, monkeypatch, agent_executor_module):
        module = agent_executor_module
        module.AgentExecutor._stdin_write = 99
        module.AgentExecutor._stdin_read = 98
        monkeypatch.setattr(os, "close", lambda fd: (_ for _ in ()).throw(OSError("bad fd")))
        module.AgentExecutor._cleanup_stdin_pipe()
        assert module.AgentExecutor._stdin_write is None
        assert module.AgentExecutor._stdin_read is None

    def test_user_confirm_with_pipe(self, monkeypatch, agent_executor_module):
        module = agent_executor_module
        write_fd = []
        monkeypatch.setattr(os, "write", lambda fd, data: write_fd.append(fd))
        module.AgentExecutor._stdin_write = 42
        module.AgentExecutor._user_confirmation_event = threading.Event()
        module.AgentExecutor._is_waiting_for_confirmation = threading.Event()
        result = module.AgentExecutor.user_confirm()
        assert result is True
        assert write_fd == [42]
        module.AgentExecutor._stdin_write = None

    def test_user_confirm_write_oserror(self, monkeypatch, agent_executor_module):
        module = agent_executor_module
        monkeypatch.setattr(os, "write", lambda fd, data: (_ for _ in ()).throw(OSError("pipe closed")))
        module.AgentExecutor._stdin_write = 42
        module.AgentExecutor._user_confirmation_event = threading.Event()
        module.AgentExecutor._is_waiting_for_confirmation = threading.Event()
        result = module.AgentExecutor.user_confirm()
        assert result is False
        module.AgentExecutor._stdin_write = None

    def test_user_confirm_no_pipe(self, monkeypatch, agent_executor_module):
        module = agent_executor_module
        module.AgentExecutor._stdin_write = None
        module.AgentExecutor._user_confirmation_event = threading.Event()
        module.AgentExecutor._is_waiting_for_confirmation = threading.Event()
        result = module.AgentExecutor.user_confirm()
        assert result is False

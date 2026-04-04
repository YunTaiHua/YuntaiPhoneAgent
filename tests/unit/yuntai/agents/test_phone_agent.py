from types import SimpleNamespace
from unittest.mock import MagicMock

from yuntai.agents.phone_agent import PhoneAgent, PhoneAgentWrapper


def test_wrapper_execute_success_and_keyword_failure(monkeypatch):
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_OPERATION_PROMPT", "PROMPT")
    calls = []

    class _Agent:
        def __init__(self, result):
            self._result = result

        def run(self, task):
            calls.append(task)
            return self._result

        def reset(self):
            calls.append("reset")

    wrapper = PhoneAgentWrapper(device_id="dev-1")
    wrapper._setup_pipe = lambda: calls.append("setup")
    wrapper._cleanup_pipe = lambda: calls.append("cleanup")
    wrapper._get_agent = lambda: _Agent("执行完成")
    wrapper._reset_agent = lambda: calls.append("wrapper_reset")

    success, result = wrapper.execute("打开微信")
    assert success is True
    assert result == "执行完成"
    assert any("PROMPT" in x for x in calls if isinstance(x, str))

    calls.clear()
    wrapper._get_agent = lambda: _Agent("出现错误")
    success, result = wrapper.execute("打开QQ")
    assert success is False
    assert result == "出现错误"
    assert "cleanup" in calls


def test_wrapper_execute_exception_path(monkeypatch):
    wrapper = PhoneAgentWrapper(device_id="dev-1")
    touched = []
    wrapper._setup_pipe = lambda: touched.append("setup")
    wrapper._cleanup_pipe = lambda: touched.append("cleanup")
    wrapper._get_agent = lambda: (_ for _ in ()).throw(RuntimeError("boom"))

    success, result = wrapper.execute("task")
    assert success is False
    assert result == "执行失败: boom"
    assert touched == ["setup", "cleanup"]


def test_wrapper_extract_and_send_message_paths(monkeypatch):
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_EXTRACT_TASK_PROMPT", "extract:{app_name}:{chat_object}:{extra_prompt}")
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_EXTRACT_CHAT_PROMPT", "EXTRACT_PROMPT")
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_SEND_TASK_QQ", "qq:{message}")
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_SEND_TASK_WECHAT", "wx:{message}")
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_SEND_TASK_DEFAULT", "default:{message}")
    monkeypatch.setattr("yuntai.agents.phone_agent.PHONE_SUCCESS_KEYWORDS", ["发送成功"])

    class _Agent:
        def __init__(self, result):
            self.result = result
            self.last_task = None

        def run(self, task):
            self.last_task = task
            return self.result

        def reset(self):
            return None

    wrapper = PhoneAgentWrapper(device_id="dev")
    wrapper._setup_pipe = lambda: None
    wrapper._cleanup_pipe = lambda: None
    wrapper._reset_agent = lambda: None

    extract_agent = _Agent("记录内容")
    wrapper._get_agent = lambda: extract_agent
    ok, data = wrapper.extract_chat_records("微信", "张三")
    assert ok is True
    assert data == "记录内容"
    assert "EXTRACT_PROMPT" in extract_agent.last_task

    wrapper._get_agent = lambda: (_ for _ in ()).throw(RuntimeError("x"))
    ok, data = wrapper.extract_chat_records("微信", "张三")
    assert ok is False
    assert data == "提取失败: x"

    send_agent = _Agent("已发送，发送成功")
    wrapper._get_agent = lambda: send_agent
    ok, _ = wrapper.send_message("QQ", "张三", "你好")
    assert ok is True
    assert send_agent.last_task == "qq:你好"

    send_agent2 = _Agent("未发送")
    wrapper._get_agent = lambda: send_agent2
    ok, _ = wrapper.send_message("微信", "李四", "hi")
    assert ok is False
    assert send_agent2.last_task == "wx:hi"


def test_phone_agent_delegation_and_state_cache(monkeypatch):
    created = []

    class _Wrapper:
        def __init__(self, device_id):
            created.append(device_id)

        def execute(self, task):
            return True, f"exec:{task}"

        def open_app(self, app_name):
            return True, f"open:{app_name}"

        def extract_chat_records(self, app_name, chat_object):
            return True, f"records:{app_name}:{chat_object}"

        def send_message(self, app_name, chat_object, msg):
            return True, f"send:{app_name}:{chat_object}:{msg}"

    monkeypatch.setattr("yuntai.agents.phone_agent.PhoneAgentWrapper", _Wrapper)

    agent = PhoneAgent("d1")
    assert agent.execute_operation("任务")[1] == "exec:任务"
    assert agent.open_app("微信")[1] == "open:微信"
    ok, rec = agent.extract_chat_records("QQ", "张三")
    assert ok is True and rec == "records:QQ:张三"
    assert agent._last_extract_result == (True, "records:QQ:张三")
    assert agent.send_message("QQ", "张三", "hello")[1] == "send:QQ:张三:hello"

    agent.set_device_id("d2")
    assert agent.device_id == "d2"
    assert agent._wrapper is None
    agent.open_app("抖音")
    assert created == ["d1", "d2"]


class TestPhoneAgentCoverageGaps:
    def _make_wrapper(self, monkeypatch):
        import yuntai.agents.phone_agent as mod
        monkeypatch.setattr(mod, "ModelConfig", lambda **kw: SimpleNamespace(**kw))
        monkeypatch.setattr(mod, "AgentConfig", lambda **kw: SimpleNamespace(**kw))
        monkeypatch.setattr(mod, "ExternalPhoneAgent", MagicMock())
        wrapper = mod.PhoneAgentWrapper(device_id="test_dev", max_steps=10)
        return wrapper

    def test_create_agent(self, monkeypatch):
        wrapper = self._make_wrapper(monkeypatch)
        agent = wrapper._create_agent()
        assert agent is not None

    def test_get_agent_lazy_creation(self, monkeypatch):
        wrapper = self._make_wrapper(monkeypatch)
        agent = wrapper._get_agent()
        assert agent is not None
        agent2 = wrapper._get_agent()
        assert agent2 is agent

    def test_reset_agent(self, monkeypatch):
        wrapper = self._make_wrapper(monkeypatch)
        wrapper._get_agent()
        wrapper._reset_agent()
        assert wrapper._agent is None

    def test_setup_pipe(self, monkeypatch):
        import yuntai.agents.phone_agent as mod
        called = []
        monkeypatch.setattr(mod.AgentExecutor, "_setup_stdin_pipe", lambda: called.append(True))
        wrapper = self._make_wrapper(monkeypatch)
        wrapper._setup_pipe()
        assert called == [True]

    def test_cleanup_pipe(self, monkeypatch):
        import yuntai.agents.phone_agent as mod
        called = []
        monkeypatch.setattr(mod.AgentExecutor, "_cleanup_stdin_pipe", lambda: called.append(True))
        wrapper = self._make_wrapper(monkeypatch)
        wrapper._cleanup_pipe()
        assert called == [True]

    def test_open_app(self, monkeypatch):
        wrapper = self._make_wrapper(monkeypatch)
        wrapper.execute = MagicMock(return_value=True)
        result = wrapper.open_app("微信")
        assert result is True
        wrapper.execute.assert_called_once_with("打开微信")

    def test_send_message_default_template(self, monkeypatch):
        wrapper = self._make_wrapper(monkeypatch)
        mock_agent = MagicMock()
        mock_agent.run.return_value = "消息已成功发送"
        wrapper._setup_pipe = MagicMock()
        wrapper._get_agent = MagicMock(return_value=mock_agent)
        wrapper._reset_agent = MagicMock()
        ok, result = wrapper.send_message("微博", "friend", "hello")
        assert ok is True

    def test_send_message_exception(self, monkeypatch):
        wrapper = self._make_wrapper(monkeypatch)
        mock_agent = MagicMock()
        mock_agent.run.side_effect = RuntimeError("exec boom")
        wrapper._setup_pipe = MagicMock()
        wrapper._get_agent = MagicMock(return_value=mock_agent)
        wrapper._reset_agent = MagicMock()
        ok, msg = wrapper.send_message("微信", "friend", "hello")
        assert ok is False
        assert "发送失败" in msg

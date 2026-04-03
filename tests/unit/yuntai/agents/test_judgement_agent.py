from types import SimpleNamespace

from yuntai.agents.judgement_agent import JudgementAgent
from yuntai.prompts import (
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_COMPLEX_OPERATION,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_SINGLE_REPLY,
)


class _FakeModel:
    def __init__(self, content="", boom=False):
        self.content = content
        self.boom = boom

    def invoke(self, messages, config=None):
        if self.boom:
            raise RuntimeError("judge-boom")
        return SimpleNamespace(content=self.content)


def test_judge_empty_input_returns_default():
    agent = JudgementAgent(model=_FakeModel("{}"), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    result = agent.judge("   ")
    assert result.task_type == TASK_TYPE_FREE_CHAT
    assert result.target_app == ""


def test_judge_parses_json_wrapped_text(monkeypatch):
    monkeypatch.setattr(
        "yuntai.agents.judgement_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: ["cb"],
    )
    model = _FakeModel('prefix {"task_type":"single_reply","target_app":"微信","target_object":"张三","is_auto":false,"specific_content":"你好"} suffix')
    agent = JudgementAgent(model=model, callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))

    result = agent.judge("打开微信给张三发消息")
    assert result.task_type == "single_reply"
    assert result.target_app == "微信"
    assert result.target_object == "张三"
    assert result.specific_content == "你好"


def test_judge_falls_back_on_json_error(monkeypatch):
    monkeypatch.setattr(
        "yuntai.agents.judgement_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: [],
    )
    agent = JudgementAgent(model=_FakeModel("{bad json}"), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))

    result = agent.judge('打开微信给张三发消息："你好"')
    assert result.task_type == TASK_TYPE_COMPLEX_OPERATION
    assert result.target_app == "微信"
    assert result.target_object == "张三"
    assert result.specific_content == "你好"


def test_judge_falls_back_on_model_exception(monkeypatch):
    monkeypatch.setattr(
        "yuntai.agents.judgement_agent.prepare_callbacks_with_manager",
        lambda *args, **kwargs: [],
    )
    agent = JudgementAgent(model=_FakeModel(boom=True), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))

    result = agent.judge("打开QQ")
    assert result.task_type == TASK_TYPE_BASIC_OPERATION
    assert result.target_app == "qq"


def test_fallback_paths_cover_boundaries():
    agent = JudgementAgent(model=_FakeModel("{}"), callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))

    assert agent._fallback_judge("请auto 持续 打开微信发消息给李四").task_type == TASK_TYPE_CONTINUOUS_REPLY
    assert agent._fallback_judge("打开微信给王五发消息").task_type == TASK_TYPE_SINGLE_REPLY
    assert agent._fallback_judge("打开抖音").task_type == TASK_TYPE_BASIC_OPERATION
    assert agent._fallback_judge("今天天气如何").task_type == TASK_TYPE_FREE_CHAT
    assert agent._extract_object("给 张三 发消息") == ""
    assert agent._extract_content("提醒我 12:30") == ""

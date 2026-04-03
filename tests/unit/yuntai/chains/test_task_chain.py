from types import SimpleNamespace

import pytest

from yuntai.agents.judgement_agent import TaskJudgementResult
from yuntai.chains.task_chain import TaskChain
from yuntai.prompts import (
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_COMPLEX_OPERATION,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_SINGLE_REPLY,
)


def _jr(task_type, app="", obj="", content="", is_auto=False):
    return TaskJudgementResult(
        task_type=task_type,
        target_app=app,
        target_object=obj,
        is_auto=is_auto,
        specific_content=content,
    )


def _build_chain(judgement_result, events):
    return TaskChain(
        judgement_agent=SimpleNamespace(judge=lambda *a, **k: judgement_result),
        chat_agent=SimpleNamespace(chat=lambda text, callbacks=None: f"chat:{text}:{callbacks}"),
        phone_agent=SimpleNamespace(
            execute_operation=lambda task: (False, "bad") if "复杂" in task else (True, "ok"),
            set_device_id=lambda d: events.append(("set_phone", d)),
        ),
        reply_chain=SimpleNamespace(
            single_reply=lambda app, obj, callbacks=None: (True, f"reply:{app}:{obj}:{callbacks}"),
            set_device_id=lambda d: events.append(("set_reply", d)),
            stop=lambda: events.append(("stop", None)),
        ),
        callback_manager=SimpleNamespace(get_callbacks=lambda **k: []),
    )


def test_process_empty_and_shortcut_paths(monkeypatch):
    monkeypatch.setattr("yuntai.chains.task_chain.prepare_callbacks_with_manager", lambda *a, **k: [])
    monkeypatch.setattr("yuntai.chains.task_chain.emit_agent_event", lambda *a, **k: None)

    phone = SimpleNamespace(execute_operation=lambda task: (True, "done"), set_device_id=lambda d: None)
    chain = TaskChain(
        phone_agent=phone,
        judgement_agent=SimpleNamespace(judge=lambda *a, **k: _jr(TASK_TYPE_FREE_CHAT)),
        chat_agent=SimpleNamespace(chat=lambda *a, **k: "chat"),
        reply_chain=SimpleNamespace(single_reply=lambda *a, **k: (True, "reply"), set_device_id=lambda d: None, stop=lambda: None),
        callback_manager=SimpleNamespace(get_callbacks=lambda **k: []),
    )

    assert chain.process("   ") == ("输入为空", {})

    result, info = chain.process("w")
    assert result == "✅ 操作完成"
    assert info == {}


@pytest.mark.parametrize(
    ("judgement_result", "user_input", "expected"),
    [
        (_jr(TASK_TYPE_FREE_CHAT), "自由聊", "chat:"),
        (_jr(TASK_TYPE_BASIC_OPERATION, app="微信"), "打开微信", "✅ 操作完成"),
        (_jr(TASK_TYPE_SINGLE_REPLY, app="微信", obj="张三"), "回复", "reply:微信:张三"),
        (_jr(TASK_TYPE_CONTINUOUS_REPLY, app="QQ", obj="李四"), "持续", "❌ 设备未连接"),
        (_jr(TASK_TYPE_COMPLEX_OPERATION), "复杂任务", "❌ 操作失败: bad"),
        (_jr("unknown"), "未知", "chat:"),
    ],
)
def test_process_dispatches_each_task_type(monkeypatch, judgement_result, user_input, expected):
    events = []
    monkeypatch.setattr("yuntai.chains.task_chain.prepare_callbacks_with_manager", lambda *a, **k: ["cb"])
    monkeypatch.setattr("yuntai.chains.task_chain.emit_agent_event", lambda *a, **k: events.append((a, k)))

    chain = _build_chain(judgement_result, events)
    result, info = chain.process(user_input)

    if expected.startswith("chat:") or expected.startswith("reply:"):
        assert result.startswith(expected)
    else:
        assert result == expected
    assert info["task_type"] == judgement_result.task_type
    assert events and events[0][0][0] == "task_type"


@pytest.mark.parametrize(
    "judgement_result",
    [
        _jr(TASK_TYPE_SINGLE_REPLY, app="", obj=""),
        _jr(TASK_TYPE_CONTINUOUS_REPLY, app="", obj=""),
    ],
)
def test_process_returns_message_when_app_or_object_missing(monkeypatch, judgement_result):
    monkeypatch.setattr("yuntai.chains.task_chain.prepare_callbacks_with_manager", lambda *a, **k: ["cb"])
    monkeypatch.setattr("yuntai.chains.task_chain.emit_agent_event", lambda *a, **k: None)

    chain = _build_chain(judgement_result, events=[])
    result, _ = chain.process("缺少参数")

    assert result == "无法识别 APP 或聊天对象"


def test_task_chain_setters_and_continuous_branch(monkeypatch):
    timers = []

    class _Timer:
        def __init__(self, delay, fn):
            timers.append(delay)
            self.fn = fn

        def start(self):
            self.fn()

    monkeypatch.setattr("yuntai.chains.task_chain.threading.Timer", _Timer)
    monkeypatch.setattr("yuntai.chains.task_chain.prepare_callbacks_with_manager", lambda *a, **k: [])
    monkeypatch.setattr("yuntai.chains.task_chain.emit_agent_event", lambda *a, **k: None)

    spoken = []
    tts = SimpleNamespace(tts_enabled=True, speak_text_intelligently=lambda text: spoken.append(text))
    phone = SimpleNamespace(execute_operation=lambda task: (True, "完成内容"), set_device_id=lambda d: spoken.append(f"phone:{d}"))
    reply = SimpleNamespace(single_reply=lambda *a, **k: (True, "ok"), set_device_id=lambda d: spoken.append(f"reply:{d}"), stop=lambda: spoken.append("stopped"))

    chain = TaskChain(
        device_id="dev",
        tts_manager=tts,
        phone_agent=phone,
        reply_chain=reply,
        judgement_agent=SimpleNamespace(judge=lambda *a, **k: _jr(TASK_TYPE_CONTINUOUS_REPLY, app="微信", obj="张三")),
        chat_agent=SimpleNamespace(chat=lambda *a, **k: "chat"),
        callback_manager=SimpleNamespace(get_callbacks=lambda **k: []),
    )

    assert chain._handle_continuous_reply("微信", "张三") == "🔄CONTINUOUS_REPLY:微信:张三"
    assert chain._handle_basic_operation("task") == "✅ 操作完成"
    assert chain._handle_complex_operation("复杂task") == "✅ 操作完成"
    assert timers
    assert spoken and "完成内容" in spoken

    chain.set_device_id("new-dev")
    assert chain.device_id == "new-dev"
    chain.set_tts_manager(None)
    assert chain.tts_manager is None
    chain.stop_continuous_reply()
    assert "stopped" in spoken

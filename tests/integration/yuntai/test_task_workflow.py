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


pytestmark = pytest.mark.integration


def _judgement(task_type, app="", obj=""):
    return TaskJudgementResult(
        task_type=task_type,
        target_app=app,
        target_object=obj,
        is_auto=False,
        specific_content="",
    )


def test_task_chain_dispatches_workflow_steps_and_outputs(monkeypatch):
    events = []
    calls = []

    monkeypatch.setattr("yuntai.chains.task_chain.prepare_callbacks_with_manager", lambda *a, **k: ["cb-flow"])
    monkeypatch.setattr(
        "yuntai.chains.task_chain.emit_agent_event",
        lambda name, payload, source=None, level=None: events.append((name, payload, source, level)),
    )

    results = [
        _judgement(TASK_TYPE_FREE_CHAT),
        _judgement(TASK_TYPE_BASIC_OPERATION, app="微信"),
        _judgement(TASK_TYPE_SINGLE_REPLY, app="微信", obj="张三"),
        _judgement(TASK_TYPE_COMPLEX_OPERATION),
        _judgement(TASK_TYPE_CONTINUOUS_REPLY, app="QQ", obj="李四"),
    ]
    judgement_agent = SimpleNamespace(judge=lambda *a, **k: results.pop(0))

    chain = TaskChain(
        device_id="device-1",
        judgement_agent=judgement_agent,
        chat_agent=SimpleNamespace(
            chat=lambda text, callbacks=None: calls.append(("chat", text, callbacks)) or f"chat:{text}"
        ),
        phone_agent=SimpleNamespace(
            execute_operation=lambda task: calls.append(("phone", task)) or (True, "done"),
            set_device_id=lambda device_id: calls.append(("set_phone", device_id)),
        ),
        reply_chain=SimpleNamespace(
            single_reply=lambda app, obj, callbacks=None: calls.append(("reply", app, obj, callbacks)) or (True, "reply-ok"),
            set_device_id=lambda device_id: calls.append(("set_reply", device_id)),
            stop=lambda: calls.append(("stop_reply", None)),
        ),
        callback_manager=SimpleNamespace(get_callbacks=lambda **k: []),
    )

    free_text, free_info = chain.process("随便聊聊")
    basic_text, basic_info = chain.process("打开微信")
    reply_text, reply_info = chain.process("帮我回复")
    complex_text, complex_info = chain.process("复杂任务")
    cont_text, cont_info = chain.process("持续回复")

    assert free_text == "chat:随便聊聊"
    assert basic_text == "✅ 操作完成"
    assert reply_text == "reply-ok"
    assert complex_text == "✅ 操作完成"
    assert cont_text == "🔄CONTINUOUS_REPLY:QQ:李四"

    assert free_info["task_type"] == TASK_TYPE_FREE_CHAT
    assert basic_info["task_type"] == TASK_TYPE_BASIC_OPERATION
    assert reply_info["task_type"] == TASK_TYPE_SINGLE_REPLY
    assert complex_info["task_type"] == TASK_TYPE_COMPLEX_OPERATION
    assert cont_info["task_type"] == TASK_TYPE_CONTINUOUS_REPLY

    assert calls == [
        ("chat", "随便聊聊", ["cb-flow"]),
        ("phone", "打开微信"),
        ("reply", "微信", "张三", ["cb-flow"]),
        ("phone", "复杂任务"),
    ]
    assert [name for name, *_ in events] == ["task_type"] * 5


def test_task_chain_continuous_reply_requires_connected_device(monkeypatch):
    monkeypatch.setattr("yuntai.chains.task_chain.prepare_callbacks_with_manager", lambda *a, **k: [])
    monkeypatch.setattr("yuntai.chains.task_chain.emit_agent_event", lambda *a, **k: None)

    chain = TaskChain(
        device_id="",
        judgement_agent=SimpleNamespace(judge=lambda *a, **k: _judgement(TASK_TYPE_CONTINUOUS_REPLY, app="微信", obj="王五")),
        chat_agent=SimpleNamespace(chat=lambda *a, **k: "unused"),
        phone_agent=SimpleNamespace(execute_operation=lambda *a, **k: (True, "unused"), set_device_id=lambda d: None),
        reply_chain=SimpleNamespace(single_reply=lambda *a, **k: (True, "unused"), set_device_id=lambda d: None, stop=lambda: None),
        callback_manager=SimpleNamespace(get_callbacks=lambda **k: []),
    )

    result, info = chain.process("持续回复微信王五")

    assert result == "❌ 设备未连接"
    assert info["task_type"] == TASK_TYPE_CONTINUOUS_REPLY

from types import SimpleNamespace

import pytest

from yuntai.graphs.reply_graph import ReplyGraph


pytestmark = pytest.mark.integration


def test_reply_graph_happy_path_runs_all_workflow_steps(monkeypatch):
    steps = []

    def fake_extract(state):
        steps.append("extract")
        return {"extracted_records": "records", "cycle_count": state["cycle_count"] + 1}

    def fake_parse(state):
        steps.append("parse")
        return {
            "parse_success": True,
            "parsed_messages": [{"content": "新消息", "position": "左侧有头像", "color": "白色"}],
        }

    def fake_ownership(state):
        steps.append("ownership")
        return {
            "other_messages": ["新消息"],
            "my_messages": ["我方历史"],
            "current_other_messages": ["新消息"],
            "current_my_messages": ["我方历史"],
        }

    def fake_check_new(state):
        steps.append("check_new")
        return {"is_new_message": True, "latest_message": "新消息", "seen_other_messages": ["新消息"]}

    def fake_reply(state):
        steps.append("reply")
        return {"generated_reply": "收到，稍后处理。"}

    def fake_send(state):
        steps.append("send")
        return {"send_success": True, "last_sent_reply": state["generated_reply"]}

    def fake_memory(state):
        steps.append("memory")
        return {"result_message": "saved"}

    def fake_wait(state):
        steps.append("wait")
        return {}

    def fake_continue(state):
        steps.append("check_continue")
        return {"should_continue": False}

    monkeypatch.setattr("yuntai.graphs.reply_graph.emit_agent_event", lambda *a, **k: None)
    monkeypatch.setattr("yuntai.graphs.reply_graph.extract_records", fake_extract)
    monkeypatch.setattr("yuntai.graphs.reply_graph.parse_messages", fake_parse)
    monkeypatch.setattr("yuntai.graphs.reply_graph.determine_ownership", fake_ownership)
    monkeypatch.setattr("yuntai.graphs.reply_graph.check_new_message", fake_check_new)
    monkeypatch.setattr("yuntai.graphs.reply_graph.generate_reply", fake_reply)
    monkeypatch.setattr("yuntai.graphs.reply_graph.send_message", fake_send)
    monkeypatch.setattr("yuntai.graphs.reply_graph.update_memory", fake_memory)
    monkeypatch.setattr("yuntai.graphs.reply_graph.do_wait", fake_wait)
    monkeypatch.setattr("yuntai.graphs.reply_graph.check_continue", fake_continue)

    graph = ReplyGraph(file_manager=SimpleNamespace(), tts_manager=SimpleNamespace())
    success, result = graph.run(app_name="微信", chat_object="张三", device_id="dev-1", max_cycles=3)

    assert success is True
    assert "达到最大循环次数 3" in result
    assert steps == [
        "extract",
        "parse",
        "ownership",
        "check_new",
        "reply",
        "send",
        "memory",
        "wait",
        "check_continue",
    ]


def test_reply_graph_routes_to_wait_when_terminated_before_reply(monkeypatch):
    steps = []

    monkeypatch.setattr("yuntai.graphs.reply_graph.emit_agent_event", lambda *a, **k: None)
    monkeypatch.setattr("yuntai.graphs.reply_graph.extract_records", lambda state: steps.append("extract") or {"cycle_count": 1})
    monkeypatch.setattr("yuntai.graphs.reply_graph.parse_messages", lambda state: steps.append("parse") or {"parse_success": True, "parsed_messages": []})
    monkeypatch.setattr(
        "yuntai.graphs.reply_graph.determine_ownership",
        lambda state: steps.append("ownership") or {"current_other_messages": ["新消息"]},
    )
    monkeypatch.setattr(
        "yuntai.graphs.reply_graph.check_new_message",
        lambda state: steps.append("check_new") or {"is_new_message": True, "terminate_flag": True, "latest_message": "新消息"},
    )
    monkeypatch.setattr("yuntai.graphs.reply_graph.generate_reply", lambda state: steps.append("reply") or {"generated_reply": "不会执行"})
    monkeypatch.setattr("yuntai.graphs.reply_graph.send_message", lambda state: steps.append("send") or {"send_success": True})
    monkeypatch.setattr("yuntai.graphs.reply_graph.update_memory", lambda state: steps.append("memory") or {})
    monkeypatch.setattr("yuntai.graphs.reply_graph.do_wait", lambda state: steps.append("wait") or {})
    monkeypatch.setattr("yuntai.graphs.reply_graph.check_continue", lambda state: steps.append("check_continue") or {"should_continue": False})

    graph = ReplyGraph()
    success, _ = graph.run(app_name="微信", chat_object="李四", device_id="dev-2", max_cycles=2)

    assert success is True
    assert steps == ["extract", "parse", "ownership", "check_new", "wait", "check_continue"]

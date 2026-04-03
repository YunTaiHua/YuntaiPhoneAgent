import os

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


def test_send_message_skips_when_reply_empty():
    from yuntai.graphs.nodes.send import send_message

    state = {
        "app_name": "微信",
        "chat_object": "对象",
        "device_id": "d1",
        "generated_reply": "",
        "terminate_flag": False,
    }
    assert send_message(state) == {"send_success": False}


def test_send_message_skips_when_terminate_flag():
    from yuntai.graphs.nodes.send import send_message

    state = {
        "app_name": "微信",
        "chat_object": "对象",
        "device_id": "d1",
        "generated_reply": "你好",
        "terminate_flag": True,
    }
    assert send_message(state) == {"send_success": False}


def test_send_message_success_path(monkeypatch):
    from yuntai.graphs.nodes.send import send_message

    captured = {}

    class FakeAgent:
        def send_message(self, app_name, chat_object, reply):
            captured["app_name"] = app_name
            captured["chat_object"] = chat_object
            captured["reply"] = reply
            return True, "ok"

    monkeypatch.setattr("yuntai.graphs.nodes.send.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.send._get_phone_agent", lambda device_id: FakeAgent())

    state = {
        "app_name": "微信",
        "chat_object": "对象",
        "device_id": "d1",
        "generated_reply": "你好",
        "terminate_flag": False,
    }
    assert send_message(state) == {"send_success": True}
    assert captured == {"app_name": "微信", "chat_object": "对象", "reply": "你好"}


def test_send_message_failure_path(monkeypatch):
    from yuntai.graphs.nodes.send import send_message

    class FakeAgent:
        def send_message(self, app_name, chat_object, reply):
            return False, "network error"

    monkeypatch.setattr("yuntai.graphs.nodes.send.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.send._get_phone_agent", lambda device_id: FakeAgent())

    state = {
        "app_name": "微信",
        "chat_object": "对象",
        "device_id": "d1",
        "generated_reply": "你好",
        "terminate_flag": False,
    }
    assert send_message(state) == {"send_success": False}

import os

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


def test_update_memory_returns_empty_when_send_failed():
    from yuntai.graphs.nodes.memory import update_memory

    assert update_memory({"send_success": False}) == {}


def test_update_memory_saves_history_and_schedules_tts(monkeypatch):
    from yuntai.graphs.nodes import memory

    class FakeFileManager:
        def __init__(self):
            self.saved = []

        def save_conversation_history(self, data):
            self.saved.append(data)

    class FakeTTS:
        tts_enabled = True

        def __init__(self):
            self.spoken = []

        def speak_text_intelligently(self, text):
            self.spoken.append(text)

    class FakeTimer:
        def __init__(self, delay, fn):
            self.delay = delay
            self.fn = fn

        def start(self):
            self.fn()

    fake_file = FakeFileManager()
    fake_tts = FakeTTS()
    memory.set_managers(fake_file, fake_tts)
    monkeypatch.setattr(memory.threading, "Timer", FakeTimer)

    state = {
        "send_success": True,
        "generated_reply": "好的",
        "latest_message": "你好",
        "current_other_messages": ["你好"],
        "current_my_messages": ["好的"],
        "app_name": "微信",
        "chat_object": "对象",
        "cycle_count": 2,
    }

    result = memory.update_memory(state)

    assert result == {"last_sent_reply": "好的", "previous_latest_message": "你好"}
    assert fake_file.saved
    assert fake_file.saved[0]["target_app"] == "微信"
    assert fake_tts.spoken == ["好的"]


def test_update_memory_without_managers(monkeypatch):
    from yuntai.graphs.nodes import memory

    memory.set_managers(None, None)
    result = memory.update_memory(
        {
            "send_success": True,
            "generated_reply": "ok",
            "latest_message": "hi",
            "current_other_messages": ["hi"],
            "current_my_messages": ["ok"],
            "app_name": "app",
            "chat_object": "obj",
            "cycle_count": 1,
        }
    )
    assert result == {"last_sent_reply": "ok", "previous_latest_message": "hi"}


def test_prune_messages_limits_to_50():
    from yuntai.graphs.nodes.memory import prune_messages

    other = [f"o{i}" for i in range(60)]
    my = [f"m{i}" for i in range(40)]
    result = prune_messages({"other_messages": other, "my_messages": my})

    assert len(result["other_messages"]) == 50
    assert result["other_messages"][0] == "o10"
    assert result["my_messages"] == my

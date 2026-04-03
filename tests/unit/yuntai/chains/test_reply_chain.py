from types import SimpleNamespace

from yuntai.chains.reply_chain import ReplyChain


class _FakePhoneAgent:
    def __init__(self, device_id):
        self.device_id = device_id

    def extract_chat_records(self, app_name, chat_object):
        return True, "聊天记录"

    def send_message(self, app_name, chat_object, reply):
        return True, f"sent:{reply}"


def test_single_reply_success_with_tts_and_persistence(monkeypatch):
    saves = []
    speaks = []

    class _Timer:
        def __init__(self, delay, fn):
            self.fn = fn

        def start(self):
            self.fn()

    monkeypatch.setattr("yuntai.chains.reply_chain.prepare_callbacks_with_manager", lambda *a, **k: ["cb"])
    monkeypatch.setattr("yuntai.chains.reply_chain.PhoneAgent", _FakePhoneAgent)
    monkeypatch.setattr("yuntai.chains.reply_chain.get_zhipu_client", lambda: object())
    monkeypatch.setattr(
        "yuntai.chains.reply_chain.parse_messages",
        lambda records, client: [
            {"content": "我发过", "position": "右侧有头像"},
            {"content": "对方消息", "position": "左侧有头像"},
        ],
    )
    monkeypatch.setattr("yuntai.chains.reply_chain.generate_reply", lambda latest, history, client: "这是回复")
    monkeypatch.setattr("yuntai.chains.reply_chain.threading.Timer", _Timer)

    fm = SimpleNamespace(
        save_record_to_log=lambda *args: saves.append(("log", args)),
        save_conversation_history=lambda data: saves.append(("history", data)),
    )
    tts = SimpleNamespace(tts_enabled=True, speak_text_intelligently=lambda text: speaks.append(text))
    chain = ReplyChain(device_id="d1", file_manager=fm, tts_manager=tts, callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))

    success, result = chain.single_reply("微信", "张三")
    assert success is True
    assert result.startswith("回复已发送")
    assert any(kind == "log" for kind, _ in saves)
    assert any(kind == "history" for kind, _ in saves)
    assert speaks == ["这是回复"]


def test_single_reply_error_branches(monkeypatch):
    monkeypatch.setattr("yuntai.chains.reply_chain.prepare_callbacks_with_manager", lambda *a, **k: [])

    class _FailExtractPhoneAgent:
        def __init__(self, device_id):
            pass

        def extract_chat_records(self, app_name, chat_object):
            return False, "nope"

    monkeypatch.setattr("yuntai.chains.reply_chain.PhoneAgent", _FailExtractPhoneAgent)
    chain = ReplyChain(callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    ok, msg = chain.single_reply("微信", "张三")
    assert ok is False and "提取聊天记录失败" in msg

    class _NoOtherPhoneAgent:
        def __init__(self, device_id):
            pass

        def extract_chat_records(self, app_name, chat_object):
            return True, "records"

    monkeypatch.setattr("yuntai.chains.reply_chain.PhoneAgent", _NoOtherPhoneAgent)
    monkeypatch.setattr("yuntai.chains.reply_chain.get_zhipu_client", lambda: object())
    monkeypatch.setattr("yuntai.chains.reply_chain.parse_messages", lambda records, client: [{"content": "我", "position": "右侧有头像"}])
    ok, msg = chain.single_reply("微信", "张三")
    assert ok is False and msg == "没有发现对方消息"


def test_single_reply_invalid_generated_or_send_failure(monkeypatch):
    monkeypatch.setattr("yuntai.chains.reply_chain.prepare_callbacks_with_manager", lambda *a, **k: [])
    monkeypatch.setattr("yuntai.chains.reply_chain.get_zhipu_client", lambda: object())

    class _PhoneAgentSendFail:
        def __init__(self, device_id):
            pass

        def extract_chat_records(self, app_name, chat_object):
            return True, "records"

        def send_message(self, app_name, chat_object, reply):
            return False, "send-fail"

    monkeypatch.setattr("yuntai.chains.reply_chain.PhoneAgent", _PhoneAgentSendFail)
    monkeypatch.setattr("yuntai.chains.reply_chain.parse_messages", lambda records, client: [{"content": "对方", "position": "左侧有头像"}])
    monkeypatch.setattr("yuntai.chains.reply_chain.generate_reply", lambda latest, history, client: "x")

    chain = ReplyChain(callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    ok, msg = chain.single_reply("微信", "张三")
    assert ok is False and msg == "未能生成有效回复"

    monkeypatch.setattr("yuntai.chains.reply_chain.generate_reply", lambda latest, history, client: "有效回复")
    ok, msg = chain.single_reply("微信", "张三")
    assert ok is False and "回复发送失败" in msg


def test_continuous_async_and_runtime_controls(monkeypatch):
    events = []

    class _Graph:
        def __init__(self):
            self.running = True
            self.stop_called = False

        def run(self, **kwargs):
            events.append(("run", kwargs))
            return True, "ok"

        def stop(self):
            self.stop_called = True
            self.running = False
            events.append(("stop", None))

        def is_running(self):
            return self.running

    graph = _Graph()
    chain = ReplyChain(callback_manager=SimpleNamespace(get_callbacks=lambda **k: []))
    chain._reply_graph = graph

    ok, msg = chain.continuous_reply("微信", "张三", max_cycles=7)
    assert (ok, msg) == (True, "ok")
    assert events[0][1]["max_cycles"] == 7

    done = []
    chain.start_continuous_reply_async("微信", "李四", callback=lambda s, r: done.append((s, r)), max_cycles=2)
    chain._continuous_thread.join(timeout=1)
    assert done == [(True, "ok")]

    chain.stop()
    assert graph.stop_called is True
    assert chain.is_running() is False
    chain.clear_messages()

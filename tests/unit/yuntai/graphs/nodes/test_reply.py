import os
from types import SimpleNamespace

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


def test_generate_reply_returns_empty_for_invalid_latest_message(monkeypatch):
    from yuntai.graphs.nodes.reply import generate_reply

    monkeypatch.setattr("yuntai.graphs.nodes.reply.emit_agent_event", lambda *args, **kwargs: None)
    result = generate_reply(
        {
            "latest_message": "",
            "current_other_messages": [],
            "last_sent_reply": "",
        }
    )
    assert result == {"generated_reply": ""}


def test_generate_reply_success_first_sentence_and_history(monkeypatch):
    from yuntai.graphs.nodes.reply import generate_reply

    captured = {"messages": None, "config": None}

    class FakeModel:
        def invoke(self, messages, config=None):
            captured["messages"] = messages
            captured["config"] = config
            return SimpleNamespace(content="第一句。第二句")

    monkeypatch.setattr("yuntai.graphs.nodes.reply.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.reply.prepare_callbacks", lambda callbacks: ["cb"])
    monkeypatch.setattr("yuntai.graphs.nodes.reply.get_chat_model", lambda: FakeModel())
    monkeypatch.setattr("yuntai.graphs.nodes.reply.is_similar", lambda *args, **kwargs: False)

    state = {
        "latest_message": "最新问题",
        "current_other_messages": ["h1", "h2", "h3", "latest"],
        "last_sent_reply": "上一次回复",
    }
    result = generate_reply(state)

    assert result == {"generated_reply": "第一句。"}
    assert captured["config"] == {"callbacks": ["cb"]}
    human_content = captured["messages"][1].content
    assert "=== 历史对话 ===" in human_content
    assert "最新问题" in human_content
    assert "h1" in human_content


def test_generate_reply_skips_when_similar_to_last(monkeypatch):
    from yuntai.graphs.nodes.reply import generate_reply

    class FakeModel:
        def invoke(self, messages, config=None):
            return SimpleNamespace(content="几乎一样的回复")

    monkeypatch.setattr("yuntai.graphs.nodes.reply.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.reply.prepare_callbacks", lambda callbacks: [])
    monkeypatch.setattr("yuntai.graphs.nodes.reply.get_chat_model", lambda: FakeModel())
    monkeypatch.setattr("yuntai.graphs.nodes.reply.is_similar", lambda *args, **kwargs: True)

    result = generate_reply(
        {
            "latest_message": "消息",
            "current_other_messages": ["消息"],
            "last_sent_reply": "上一条",
        }
    )
    assert result == {"generated_reply": ""}


def test_generate_reply_returns_empty_on_model_exception(monkeypatch):
    from yuntai.graphs.nodes.reply import generate_reply

    class BoomModel:
        def invoke(self, messages, config=None):
            raise RuntimeError("boom")

    monkeypatch.setattr("yuntai.graphs.nodes.reply.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.reply.prepare_callbacks", lambda callbacks: [])
    monkeypatch.setattr("yuntai.graphs.nodes.reply.get_chat_model", lambda: BoomModel())

    result = generate_reply(
        {
            "latest_message": "消息",
            "current_other_messages": ["消息"],
            "last_sent_reply": "",
        }
    )
    assert result == {"generated_reply": ""}

import os

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


def test_check_new_message_returns_false_when_no_messages(monkeypatch):
    from yuntai.graphs.nodes.check_new import check_new_message

    events = []
    monkeypatch.setattr(
        "yuntai.graphs.nodes.check_new.emit_agent_event",
        lambda name, payload, source=None, level=None: events.append((name, payload, source, level)),
    )

    result = check_new_message({"current_other_messages": [], "seen_other_messages": []})

    assert result["is_new_message"] is False
    assert result["latest_message"] == ""
    assert events[-1][0] == "status"


def test_check_new_message_detects_latest_new_and_updates_seen(monkeypatch):
    from yuntai.graphs.nodes.check_new import check_new_message

    monkeypatch.setattr("yuntai.graphs.nodes.check_new.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "yuntai.graphs.nodes.check_new.is_similar",
        lambda msg, seen, threshold: msg == seen,
    )

    state = {
        "current_other_messages": ["old-1", "new-1", "new-2"],
        "seen_other_messages": ["old-1"],
    }

    result = check_new_message(state)

    assert result["is_new_message"] is True
    assert result["latest_message"] == "new-2"
    assert "new-1" in result["seen_other_messages"]
    assert "new-2" in result["seen_other_messages"]


def test_check_new_message_returns_not_new_when_all_similar(monkeypatch):
    from yuntai.graphs.nodes.check_new import check_new_message

    monkeypatch.setattr("yuntai.graphs.nodes.check_new.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.check_new.is_similar", lambda *args, **kwargs: True)

    result = check_new_message(
        {
            "current_other_messages": ["m1", "m2"],
            "seen_other_messages": ["s1"],
        }
    )

    assert result["is_new_message"] is False
    assert result["latest_message"] == ""
    assert result["seen_other_messages"] == ["s1", "m1", "m2"]

import os

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


def test_determine_ownership_empty_input_returns_empty_lists():
    from yuntai.graphs.nodes.ownership import determine_ownership

    result = determine_ownership({"parsed_messages": [], "other_messages": [], "my_messages": []})

    assert result == {"current_other_messages": [], "current_my_messages": []}


def test_determine_ownership_priority_and_boundary(monkeypatch):
    from yuntai.graphs.nodes import ownership

    monkeypatch.setattr(ownership, "emit_agent_event", lambda *args, **kwargs: None)

    known_my = "我发过的"
    known_other = "对方发过的"

    def fake_similar(content, known, threshold):
        if content == "命中我方相似" and known == known_my:
            return True
        if content == "命中对方相似" and known == known_other:
            return True
        return False

    monkeypatch.setattr(ownership, "is_similar", fake_similar)

    state = {
        "parsed_messages": [
            {"content": "a", "position": "左侧有头像", "color": "白色"},
            {"content": "命中我方相似", "position": "左侧有头像", "color": "白色"},
            {"content": "命中对方相似", "position": "右侧有头像", "color": "红色"},
            {"content": "按头像左侧", "position": "左侧有头像", "color": "红色"},
            {"content": "按头像右侧", "position": "右侧有头像", "color": "白色"},
            {"content": "按白色气泡", "position": "未知", "color": "白色"},
            {"content": "按彩色气泡", "position": "未知", "color": "蓝色"},
            {"content": "默认归对方", "position": "未知", "color": "未知"},
        ],
        "other_messages": [known_other],
        "my_messages": [known_my],
    }

    result = ownership.determine_ownership(state)

    assert result["current_other_messages"] == [
        "命中对方相似",
        "按头像左侧",
        "按白色气泡",
        "默认归对方",
    ]
    assert result["current_my_messages"] == [
        "命中我方相似",
        "按头像右侧",
        "按彩色气泡",
    ]

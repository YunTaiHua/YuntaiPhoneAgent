import os

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


class _Chunk:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": content})()})()]


def make_stream(parts):
    for part in parts:
        yield _Chunk(part)


def test_parse_messages_returns_empty_for_short_records(monkeypatch):
    from yuntai.graphs.nodes.parse import parse_messages

    monkeypatch.setattr("yuntai.graphs.nodes.parse.emit_agent_event", lambda *args, **kwargs: None)
    result = parse_messages({"extracted_records": "短"})
    assert result == {"parse_success": False, "parsed_messages": []}


def test_parse_messages_success(monkeypatch):
    from yuntai.graphs.nodes.parse import parse_messages

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return make_stream(
                        [
                            "```json",
                            '{"messages":[{"content":" 你好 ","position":"左","color":"白"},{"content":"x","position":"右","color":"红"},{"invalid":1}]}',
                            "```",
                        ]
                    )

    monkeypatch.setattr("yuntai.graphs.nodes.parse.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.parse.get_zhipu_client", lambda: FakeClient())

    result = parse_messages({"extracted_records": "A: 你好\nB: 在吗"})

    assert result["parse_success"] is True
    assert result["parsed_messages"] == [
        {"content": "你好", "position": "左侧有头像", "color": "白色"}
    ]


def test_parse_messages_fallback_on_json_error(monkeypatch):
    from yuntai.graphs.nodes.parse import parse_messages

    class BadClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return make_stream(["not-json"])

    monkeypatch.setattr("yuntai.graphs.nodes.parse.emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr("yuntai.graphs.nodes.parse.get_zhipu_client", lambda: BadClient())

    result = parse_messages({"extracted_records": "A: hello。B: world"})

    assert result["parse_success"] is False
    assert result["parsed_messages"] == [
        {"content": "A hello", "position": "左侧有头像", "color": "白色"},
        {"content": "B world", "position": "左侧有头像", "color": "白色"},
    ]


def test_standardize_helpers_and_emergency_extract():
    from yuntai.graphs.nodes.parse import _standardize_color, _standardize_position, _emergency_extract

    assert _standardize_position("左边") == "左侧有头像"
    assert _standardize_position("右侧") == "右侧有头像"
    assert _standardize_position("") == "未知"

    assert _standardize_color("粉红气泡") == "粉色"
    assert _standardize_color("蓝") == "蓝色"
    assert _standardize_color("未知色") == "未知"

    msgs = _emergency_extract("思考过程:123\n你好呀。芸苔加油💪。~" )
    assert any(m["position"] == "左侧有头像" for m in msgs)
    assert any(m["position"] == "右侧有头像" for m in msgs)

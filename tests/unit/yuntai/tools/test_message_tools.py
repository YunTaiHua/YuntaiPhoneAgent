import importlib.util
import json
import sys
import types
from pathlib import Path


MESSAGE_TOOLS_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "tools" / "message_tools.py"


class _Chunk:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"delta": type("Delta", (), {"content": content})()})()]


def _make_stream(parts):
    for part in parts:
        yield _Chunk(part)


def _load_message_tools_module(module_name: str):
    fake_zhipuai = types.ModuleType("zhipuai")
    fake_zhipuai.ZhipuAI = object

    fake_similarity = types.ModuleType("yuntai.tools.similarity")
    fake_similarity.is_similar = lambda a, b, threshold=0.6: a == b

    fake_config = types.ModuleType("yuntai.core.config")
    fake_config.ZHIPU_CHAT_MODEL = "glm-test"
    fake_config.SIMILARITY_THRESHOLD = 0.6
    fake_config.SIMILARITY_CHECK_NEW_THRESHOLD = 0.5
    fake_config.PARSE_MAX_TOKENS = 2000
    fake_config.REPLY_MAX_TOKENS = 500
    fake_config.REPLY_TEMPERATURE = 0.7
    fake_config.REPLY_HISTORY_LIMIT = 5
    fake_config.MIN_MESSAGE_LENGTH = 2

    fake_prompts = types.ModuleType("yuntai.prompts")
    fake_prompts.PARSE_MESSAGES_SYSTEM_PROMPT = "sys"
    fake_prompts.PARSE_MESSAGES_PROMPT = "records={records}"
    fake_prompts.PARSE_MESSAGES_MAX_LENGTH = 2000
    fake_prompts.REPLY_NODE_SYSTEM_PROMPT = "reply-sys"
    fake_prompts.REPLY_NODE_USER_PROMPT = "latest={latest_message}|history={history_prompt}"

    original = {
        "zhipuai": sys.modules.get("zhipuai"),
        "yuntai.tools.similarity": sys.modules.get("yuntai.tools.similarity"),
        "yuntai.core.config": sys.modules.get("yuntai.core.config"),
        "yuntai.prompts": sys.modules.get("yuntai.prompts"),
    }
    sys.modules["zhipuai"] = fake_zhipuai
    sys.modules["yuntai.tools.similarity"] = fake_similarity
    sys.modules["yuntai.core.config"] = fake_config
    sys.modules["yuntai.prompts"] = fake_prompts

    try:
        spec = importlib.util.spec_from_file_location(module_name, MESSAGE_TOOLS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in original.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


def test_parse_messages_short_record_returns_empty():
    module = _load_message_tools_module("test_message_tools_parse_short")
    assert module.parse_messages("短", object()) == []


def test_parse_messages_success_dedup_and_standardize():
    module = _load_message_tools_module("test_message_tools_parse_ok")

    payload = {
        "messages": [
            {"content": " 你好 ", "position": "左", "color": "白"},
            {"content": "你好", "position": "右", "color": "红"},
            {"content": "x", "position": "右", "color": "红"},
            "invalid",
        ]
    }

    class _Client:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return _make_stream(["```json", json.dumps(payload, ensure_ascii=False), "```"])

    result = module.parse_messages("A: 你好\nB: 在吗", _Client())
    assert result == [{"content": "你好", "position": "左侧有头像", "color": "白色"}]


def test_parse_messages_fallback_on_json_error():
    module = _load_message_tools_module("test_message_tools_parse_bad_json")

    class _Client:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return _make_stream(["not-json"])

    result = module.parse_messages("A: hello。B: world", _Client())
    assert isinstance(result, list)
    assert result == [
        {"content": "A hello", "position": "左侧有头像", "color": "白色"},
        {"content": "B world", "position": "左侧有头像", "color": "白色"},
    ]


def test_standardize_and_emergency_extract_helpers():
    module = _load_message_tools_module("test_message_tools_helpers")

    assert module._standardize_position("左边") == "左侧有头像"
    assert module._standardize_position("右侧") == "右侧有头像"
    assert module._standardize_position("") == "未知"

    assert module._standardize_color("粉红气泡") == "粉色"
    assert module._standardize_color("蓝") == "蓝色"
    assert module._standardize_color("未知色") == "未知"

    messages = module._emergency_extract("思考过程:123\n你好呀。芸苔加油💪。~")
    assert any(msg["position"] == "左侧有头像" for msg in messages)
    assert any(msg["position"] == "右侧有头像" for msg in messages)


def test_determine_message_ownership_paths(monkeypatch):
    module = _load_message_tools_module("test_message_tools_ownership")

    mapping = {
        ("和我一致", "我历史"): True,
        ("和他一致", "他历史"): True,
    }

    monkeypatch.setattr(
        module,
        "is_similar",
        lambda a, b, threshold=0.6: mapping.get((a, b), False),
    )

    messages = [
        {"content": "和我一致", "position": "左侧有头像", "color": "白色"},
        {"content": "和他一致", "position": "右侧有头像", "color": "红色"},
        {"content": "按位置左", "position": "左侧有头像", "color": "未知"},
        {"content": "按位置右", "position": "右侧有头像", "color": "未知"},
        {"content": "按颜色白", "position": "未知", "color": "白色"},
        {"content": "按颜色红", "position": "未知", "color": "红色"},
    ]

    other, mine = module.determine_message_ownership(messages, ["我历史"], ["他历史"])
    assert "和我一致" in mine
    assert "和他一致" in other
    assert "按位置左" in other
    assert "按位置右" in mine
    assert "按颜色白" in other
    assert "按颜色红" in mine


def test_generate_reply_behaviors(monkeypatch):
    module = _load_message_tools_module("test_message_tools_reply")

    assert module.generate_reply("", [], object()) == ""

    captured = {"messages": None}

    class _Client:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    captured["messages"] = kwargs["messages"]
                    return _make_stream(["第一句。第二句"])

    reply = module.generate_reply("最新问题", ["h1", "h2", "h3", "h4", "h5", "h6"], _Client(), system_prompt="custom")
    assert reply == "第一句。"
    assert captured["messages"][0]["content"] == "custom"
    assert "h2" in captured["messages"][1]["content"]
    assert "h1" not in captured["messages"][1]["content"]

    class _BoomClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    raise RuntimeError("boom")

    assert module.generate_reply("x", [], _BoomClient()) == ""


def test_check_new_messages_filters_existing_and_my_messages(monkeypatch):
    module = _load_message_tools_module("test_message_tools_check_new")

    mapping = {
        ("旧消息", "旧消息"): True,
        ("我的消息", "我的消息"): True,
    }
    monkeypatch.setattr(
        module,
        "is_similar",
        lambda a, b, threshold=0.5: mapping.get((a, b), False),
    )

    has_new, new_msgs = module.check_new_messages(
        ["旧消息", "我的消息", "全新消息"],
        ["旧消息"],
        ["我的消息"],
    )
    assert has_new is True
    assert new_msgs == ["全新消息"]

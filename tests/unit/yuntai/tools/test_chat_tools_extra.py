from yuntai.tools import chat_tools


class _FileManager:
    def __init__(self, with_data=True):
        self.with_data = with_data

    def get_recent_conversation_history(self, target_app, target_object, limit=5):
        if not self.with_data:
            return []
        return [{"content": f"{target_app}-{target_object}-hello"}]

    def get_recent_free_chats(self, limit=5):
        if not self.with_data:
            return []
        return [{"user_input": "u1", "assistant_reply": "a1"}]

    def read_forever_memory(self):
        return "remember me" if self.with_data else ""


def test_get_current_time_info_delegates(monkeypatch):
    monkeypatch.setattr(chat_tools.TimeTool, "get_time_info", staticmethod(lambda: "NOW"))
    assert chat_tools.get_current_time_info() == "NOW"


def test_get_history_context_with_all_sections():
    text = chat_tools.get_history_context(_FileManager(True), target_app="QQ", target_object="Alice", limit=2)
    assert "最近聊天记录" in text
    assert "最近自由对话" in text
    assert "永久记忆" in text


def test_get_history_context_without_data_is_empty():
    assert chat_tools.get_history_context(_FileManager(False)) == ""


def test_build_chat_system_prompt_time_memory_toggles(monkeypatch):
    monkeypatch.setattr(chat_tools, "get_current_time_info", lambda: "TIME-INFO")

    prompt = chat_tools.build_chat_system_prompt(
        include_time=True,
        include_memory=True,
        forever_memory_content="abc",
    )
    assert "TIME-INFO" in prompt
    assert "永久记忆" in prompt

    prompt2 = chat_tools.build_chat_system_prompt(
        include_time=False,
        include_memory=True,
        forever_memory_content="",
    )
    assert "TIME-INFO" not in prompt2
    assert "永久记忆" not in prompt2

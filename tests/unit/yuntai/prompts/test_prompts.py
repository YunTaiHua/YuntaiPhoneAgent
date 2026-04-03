import importlib.util
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[4] / "yuntai" / "prompts"


def _load_prompt_module(filename: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, PROMPTS_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_judgement_prompt_constants_and_exports():
    m = _load_prompt_module("judgement_prompt.py", "test_prompts_judgement")

    expected = {
        "TASK_JUDGEMENT_PROMPT",
        "TASK_TYPE_FREE_CHAT",
        "TASK_TYPE_BASIC_OPERATION",
        "TASK_TYPE_SINGLE_REPLY",
        "TASK_TYPE_CONTINUOUS_REPLY",
        "TASK_TYPE_COMPLEX_OPERATION",
    }
    assert expected.issubset(set(m.__all__))
    assert m.TASK_TYPE_FREE_CHAT == "free_chat"
    assert "JSON" in m.TASK_JUDGEMENT_PROMPT


def test_chat_prompt_templates_have_required_placeholders():
    m = _load_prompt_module("chat_prompt.py", "test_prompts_chat")

    assert "{time_info}" in m.CHAT_WITH_CONTEXT_PROMPT
    assert "{forever_memory}" in m.CHAT_WITH_CONTEXT_PROMPT
    assert "{chat_history}" in m.CHAT_WITH_CONTEXT_PROMPT
    assert "{user_input}" in m.CHAT_WITH_CONTEXT_PROMPT
    assert m.CHAT_FINAL_INSTRUCTION.strip().startswith("请基于")
    assert "小芸" in m.CHAT_SYSTEM_PROMPT


def test_phone_prompt_templates_and_variants():
    m = _load_prompt_module("phone_prompt.py", "test_prompts_phone")

    assert "{app_name}" in m.PHONE_SEND_MESSAGE_PROMPT
    assert "{chat_object}" in m.PHONE_SEND_MESSAGE_PROMPT
    assert "{message}" in m.PHONE_SEND_MESSAGE_PROMPT
    assert "{extra_prompt}" in m.PHONE_EXTRACT_TASK_PROMPT
    assert "右下角" in m.PHONE_SEND_TASK_QQ
    assert "右侧" in m.PHONE_SEND_TASK_WECHAT
    assert "发送按钮" in m.PHONE_SEND_TASK_DEFAULT


def test_reply_prompt_templates():
    m = _load_prompt_module("reply_prompt.py", "test_prompts_reply")

    assert "{latest_message}" in m.REPLY_GENERATION_PROMPT
    assert "{history_context}" in m.REPLY_GENERATION_PROMPT
    assert "has_new_message" in m.REPLY_JUDGEMENT_PROMPT
    assert "{latest_message}" in m.REPLY_NODE_USER_PROMPT
    assert "{history_prompt}" in m.REPLY_NODE_USER_PROMPT


def test_parse_and_agent_executor_prompt_content():
    parse = _load_prompt_module("parse_prompt.py", "test_prompts_parse")
    agent = _load_prompt_module("agent_executor_prompt.py", "test_prompts_agent")

    assert parse.PARSE_MESSAGES_MAX_LENGTH == 2000
    assert "{records}" in parse.PARSE_MESSAGES_PROMPT
    assert "JSON" in parse.PARSE_MESSAGES_SYSTEM_PROMPT
    assert "头像位置" in agent.CHAT_MESSAGE_PROMPT
    assert "Back" in agent.CHAT_MESSAGE_PROMPT

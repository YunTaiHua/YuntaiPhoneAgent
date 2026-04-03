import importlib.util
import sys
import types
from pathlib import Path


PHONE_TOOLS_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "tools" / "phone_tools.py"


def _load_phone_tools_module(module_name: str):
    fake_phone_agent_module = types.ModuleType("yuntai.agents.phone_agent")

    class _FakePhoneAgent:
        def __init__(self, device_id):
            self.device_id = device_id

        def open_app(self, app_name):
            return True, f"open:{self.device_id}:{app_name}"

        def execute_operation(self, task):
            return True, f"operate:{self.device_id}:{task}"

        def extract_chat_records(self, app_name, chat_object):
            return True, f"extract:{self.device_id}:{app_name}:{chat_object}"

        def send_message(self, app_name, chat_object, message):
            return True, f"send:{self.device_id}:{app_name}:{chat_object}:{message}"

    fake_phone_agent_module.PhoneAgent = _FakePhoneAgent
    original = sys.modules.get("yuntai.agents.phone_agent")
    sys.modules["yuntai.agents.phone_agent"] = fake_phone_agent_module

    try:
        spec = importlib.util.spec_from_file_location(module_name, PHONE_TOOLS_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if original is None:
            sys.modules.pop("yuntai.agents.phone_agent", None)
        else:
            sys.modules["yuntai.agents.phone_agent"] = original


def test_open_app_tool_calls_agent():
    module = _load_phone_tools_module("test_phone_tools_open")
    ok, msg = module.open_app_tool("device-1", "微信")
    assert ok is True
    assert msg == "open:device-1:微信"


def test_execute_phone_operation_calls_agent():
    module = _load_phone_tools_module("test_phone_tools_operation")
    ok, msg = module.execute_phone_operation("device-2", "打开QQ")
    assert ok is True
    assert msg == "operate:device-2:打开QQ"


def test_extract_chat_records_ignores_extra_prompt_argument():
    module = _load_phone_tools_module("test_phone_tools_extract")
    ok, msg = module.extract_chat_records_tool("device-3", "QQ", "张三", extra_prompt="ignored")
    assert ok is True
    assert msg == "extract:device-3:QQ:张三"


def test_send_message_tool_calls_agent_with_long_message():
    module = _load_phone_tools_module("test_phone_tools_send")
    message = "x" * 200
    ok, msg = module.send_message_tool("device-4", "微信", "李四", message)
    assert ok is True
    assert msg == f"send:device-4:微信:李四:{message}"

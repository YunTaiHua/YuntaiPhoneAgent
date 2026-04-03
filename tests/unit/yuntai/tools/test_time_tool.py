import datetime
import importlib.util
from pathlib import Path


TIME_TOOL_PATH = Path(__file__).resolve().parents[4] / "yuntai" / "tools" / "time_tool.py"


def _load_time_tool_module(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, TIME_TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeDatetime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 1, 31, 14, 30, 45)


def test_get_current_timestamp_formats(monkeypatch):
    module = _load_time_tool_module("test_time_tool_formats")
    monkeypatch.setattr(module.datetime, "datetime", _FakeDatetime)
    time_tool = module.TimeTool

    assert time_tool.get_current_timestamp("datetime") == "2026-01-31 14:30:45"
    assert time_tool.get_current_timestamp("filename") == "20260131_143045"


def test_get_current_timestamp_short_format(monkeypatch):
    module = _load_time_tool_module("test_time_tool_short")
    monkeypatch.setattr(module.time, "strftime", lambda *args: "[14:30:45]")
    time_tool = module.TimeTool

    assert time_tool.get_current_timestamp("short") == "[14:30:45]"


def test_get_current_timestamp_unknown_format_falls_back(monkeypatch):
    module = _load_time_tool_module("test_time_tool_unknown")
    monkeypatch.setattr(module.datetime, "datetime", _FakeDatetime)
    assert module.TimeTool.get_current_timestamp("unknown") == "2026-01-31 14:30:45"


def test_date_time_weekday_and_info(monkeypatch):
    module = _load_time_tool_module("test_time_tool_info")
    monkeypatch.setattr(module.datetime, "datetime", _FakeDatetime)
    time_tool = module.TimeTool

    assert time_tool.get_date_only() == "2026-01-31"
    assert time_tool.get_time_only() == "14:30:45"
    assert time_tool.get_weekday() == "周六"

    info = time_tool.get_time_info()
    assert "完整时间：2026-01-31 14:30:45" in info
    assert "日期：2026-01-31" in info
    assert "时间：14:30:45" in info
    assert "星期：周六" in info

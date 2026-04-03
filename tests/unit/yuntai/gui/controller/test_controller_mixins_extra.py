import threading
from types import SimpleNamespace

from yuntai.gui.controller.command import CommandMixin
from yuntai.gui.controller.core import ControllerCore, _format_action_lines
from yuntai.gui.controller.device import DeviceMixin
from yuntai.gui.controller.file_ops import FileOpsMixin
from yuntai.gui.controller.tts_integration import TTSIntegrationMixin
from yuntai.gui.controller.ui_state import UIStateMixin


class _Signal:
    def __init__(self):
        self.calls = []

    def emit(self, *args):
        self.calls.append(args)


class _Btn:
    def __init__(self):
        self.enabled = True

    def setEnabled(self, value):
        self.enabled = value


class _Text:
    def __init__(self, value=""):
        self.value = value
        self.readonly = True
        self.height = None

    def toPlainText(self):
        return self.value

    def clear(self):
        self.value = ""

    def setText(self, value):
        self.value = value

    def setStyleSheet(self, _style):
        return None

    def setFixedHeight(self, h):
        self.height = h

    def setReadOnly(self, value):
        self.readonly = value

    def insertPlainText(self, value):
        self.value += value

    def ensureCursorVisible(self):
        return None


class _View:
    def __init__(self, comps=None):
        self.comps = comps or {}
        self.current_page_index = 0
        self.is_dark_theme = False
        self.toast_widget = SimpleNamespace(show_toast=lambda *args, **kwargs: None)

    def get_component(self, name):
        return self.comps.get(name)

    def show_attached_files(self, *_args, **_kwargs):
        return None

    def show_file_upload_dialog(self):
        return []

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme


def test_format_action_lines_accepts_dict_and_non_dict():
    assert _format_action_lines({"a": 1, "b": 2}) in ("a: 1\nb: 2", "b: 2\na: 1")
    assert _format_action_lines("x") == "x"


def test_controller_core_event_text_branches():
    core = ControllerCore.__new__(ControllerCore)
    assert core._format_agent_event_text({"type": "run_started", "payload": {}}) == ""
    assert "任务类型" in core._format_agent_event_text({"type": "task_type", "payload": {"task_type": "task"}})
    assert "free_chat" in core._format_agent_event_text({"type": "task_type", "payload": {"task_type": "free_chat"}})
    assert core._format_agent_event_text({"type": "thinking_chunk", "payload": {"text": "abc"}}) == "abc"
    assert "动作" in core._format_agent_event_text({"type": "action_decoded", "payload": {"action": {"k": "v"}}})
    assert "性能指标" in core._format_agent_event_text({"type": "performance_metric", "payload": {"name": "label"}})
    assert "结果" in core._format_agent_event_text({"type": "result", "payload": {"message": "ok"}})
    assert "错误" in core._format_agent_event_text({"type": "error", "payload": {"message": "bad"}})
    assert "hello" in core._format_agent_event_text({"type": "status", "payload": {"message": "hello"}})


def test_ui_state_buttons_and_indicator_styles():
    comps = {"execute_button": _Btn(), "terminate_button": _Btn(), "tts_indicator": _Text()}
    obj = object.__new__(UIStateMixin)
    obj.view = _View(comps)
    obj._disable_execute_button_signal = _Signal()
    obj._show_enter_button_signal = _Signal()
    obj._enable_execute_button_signal = _Signal()
    obj._hide_enter_button_signal = _Signal()
    obj._disable_terminate_button_signal = _Signal()
    obj._enable_terminate_button_signal = _Signal()
    obj.is_executing = True

    obj._disable_execute_button()
    obj._enable_execute_button()
    obj._disable_terminate_button()
    obj._enable_terminate_button()

    obj._do_disable_execute_button()
    assert comps["execute_button"].enabled is False
    obj._do_enable_execute_button()
    assert comps["execute_button"].enabled is True

    obj._do_disable_terminate_button()
    assert comps["terminate_button"].enabled is False
    obj._do_enable_terminate_button()
    assert comps["terminate_button"].enabled is True

    obj.update_tts_indicator(True)
    assert "TTS: 开" in comps["tts_indicator"].value
    obj.update_tts_indicator(False)
    assert "TTS: 关" in comps["tts_indicator"].value


def test_device_mixin_paths():
    calls = []
    cmd_input = SimpleNamespace(clear=lambda: calls.append("clear"), setPlainText=lambda t: calls.append(t))
    view = _View({"command_input": cmd_input})
    obj = object.__new__(DeviceMixin)
    obj.view = view
    obj.show_toast = lambda m, t: calls.append((m, t))
    obj.execute_command = lambda: calls.append("exec")

    obj._on_device_type_changed("HarmonyOS (HDC)")
    assert obj.device_type == "harmonyos"
    obj._on_device_type_changed("Android")
    assert obj.device_type == "android"

    obj.execute_shortcut("unknown")
    obj.execute_shortcut("w")
    assert "exec" in calls


def test_file_ops_support_and_history_paths(tmp_path):
    existing = tmp_path / "a.txt"
    existing.write_text("x", encoding="utf-8")
    missing = tmp_path / "missing.txt"

    class _MM:
        def is_file_supported(self, _):
            return True

        def check_file_size(self, _):
            return True, "ok"

    calls = []
    file_manager = SimpleNamespace(
        safe_read_json_file=lambda *_: {
            "free_chats": [{"user_input": "u", "assistant_reply": "a"}, {"user_input": "", "assistant_reply": "r"}]
        },
        save_conversation_history=lambda data: calls.append(data),
    )
    obj = object.__new__(FileOpsMixin)
    obj.view = _View()
    obj.is_executing = False
    obj.attached_files = []
    obj.multimodal_processor = _MM()
    obj.task_manager = SimpleNamespace(file_manager=file_manager)
    obj.show_toast = lambda *_args, **_kwargs: None

    assert obj._check_file_supported(str(existing)) == (True, "")
    ok, msg = obj._check_file_supported(str(missing))
    assert ok is False and "不存在" in msg

    obj.attached_files = ["a", "b"]
    obj.clear_attached_files()
    assert obj.attached_files == []

    obj.attached_files = ["a", "b"]
    obj.remove_attached_file("a")
    assert obj.attached_files == ["b"]

    history = obj._get_chat_history_for_multimodal()
    assert history and history[0]["role"] == "user"
    obj._save_multimodal_chat_history("hello", [str(existing)], "reply")
    assert calls and calls[0]["type"] == "free_chat"


def test_tts_integration_synthesize_and_wait(monkeypatch):
    hide = _Signal()
    show = _Signal()
    update = _Signal()

    tts_manager = SimpleNamespace(
        tts_files_database={"gpt": {"g": 1}, "sovits": {"s": 1}, "audio": {"/tmp/a.wav": 1}, "text": {"a.txt": 1}},
        get_current_model=lambda kind: None if kind != "audio" else "/tmp/a.wav",
        set_current_model=lambda *_args, **_kwargs: True,
        speak_text_intelligently=lambda *_args, **_kwargs: True,
        is_playing_audio=False,
    )
    obj = object.__new__(TTSIntegrationMixin)
    obj.task_manager = SimpleNamespace(preload_tts_modules=lambda: True, tts_manager=tts_manager)
    obj._hide_tts_loading_signal = hide
    obj._show_tts_loading_signal = show
    obj._update_tts_indicator_signal = update

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            self._target()

    monkeypatch.setattr(threading, "Thread", _ImmediateThread)
    obj.preload_tts_modules()
    assert update.calls and update.calls[0] == (True,)

    obj._wait_audio_then_hide()
    assert hide.calls


def test_command_clear_output_and_simulate_enter(monkeypatch):
    output = _Text("abc")
    calls = []
    obj = object.__new__(CommandMixin)
    obj.view = _View({"output_text": output})
    obj.show_toast = lambda *args: calls.append(args)
    obj._append_output = lambda text: calls.append(text)
    obj.simulate_enter()
    assert any("用户已确认" in str(x) for x in calls)

    obj.clear_output()
    assert output.value == ""

    monkeypatch.setattr("yuntai.core.agent_executor.AgentExecutor.user_confirm", lambda: (_ for _ in ()).throw(RuntimeError("no")))
    obj.simulate_enter()
    assert any("发送确认信号失败" in str(x) for x in calls)


def test_command_multimodal_chat_paths(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("x", encoding="utf-8")
    logs = []
    tts = SimpleNamespace(tts_enabled=False)
    obj = object.__new__(CommandMixin)
    obj.multimodal_processor = None
    obj._append_output = lambda text: logs.append(text)
    obj._get_chat_history_for_multimodal = lambda: []
    obj._save_multimodal_chat_history = lambda *args: logs.append("saved")
    obj.task_manager = SimpleNamespace(tts_manager=tts)

    assert obj._handle_multimodal_chat("hi", []) == "没有可处理的文件"
    assert obj._handle_multimodal_chat("hi", [str(tmp_path / "missing")]) == "没有有效的文件"

    class _MM:
        def process_with_files(self, **_kwargs):
            return True, "response", {}

    obj.multimodal_processor = _MM()
    assert obj._handle_multimodal_chat("hi", [str(f)]) == "response"
    assert "saved" in logs

import queue
from types import SimpleNamespace

from yuntai.gui.controller.command import CommandMixin
from yuntai.gui.controller.core import ControllerCore
from yuntai.gui.controller.file_ops import FileOpsMixin


class _Signal:
    def __init__(self):
        self.connected = []

    def disconnect(self):
        raise TypeError()

    def connect(self, fn):
        self.connected.append(fn)


class _Button:
    def __init__(self):
        self.clicked = _Signal()


class _Text:
    def __init__(self, value=""):
        self.value = value
        self.height = None

    def toPlainText(self):
        return self.value

    def clear(self):
        self.value = ""

    def setFixedHeight(self, height):
        self.height = height


def test_controller_core_process_messages_and_event_emission():
    calls = []
    emitted = []

    core = ControllerCore.__new__(ControllerCore)
    core.message_queue = queue.Queue()
    core.message_queue.put(("info", "ok"))
    core.message_queue.put(("error", "bad"))
    core.show_toast = lambda msg, level: calls.append((msg, level))
    core._output_signal = SimpleNamespace(emit=lambda text: emitted.append(text))

    core.process_messages()
    assert calls == [("ok", "info"), ("bad", "error")]

    core._handle_agent_event({"type": "status", "payload": {"message": "hello"}})
    assert emitted and "hello" in emitted[-1]


def test_controller_core_rebind_dispatch():
    calls = []
    core = ControllerCore.__new__(ControllerCore)
    core._bind_dashboard_events = lambda: calls.append("dashboard")
    core.connection_handler = SimpleNamespace(_bind_events=lambda: calls.append("conn"))
    core.tts_handler = SimpleNamespace(_bind_events=lambda: calls.append("tts"))
    core.system_handler = SimpleNamespace(
        _bind_history_events=lambda: calls.append("history"),
        _bind_settings_events=lambda: calls.append("settings"),
    )
    core.dynamic_handler = SimpleNamespace(_bind_events=lambda: calls.append("dynamic"))

    for idx in range(6):
        core._rebind_current_page_events(idx)

    assert calls == ["dashboard", "conn", "tts", "history", "dynamic", "settings"]


def test_controller_core_bind_dashboard_events_connects_all(monkeypatch):
    import yuntai.gui.controller.core as core_mod

    monkeypatch.setattr(core_mod, "SHORTCUTS", {"w": "微信"})

    comps = {
        "execute_button": _Button(),
        "terminate_button": _Button(),
        "tts_button": _Button(),
        "clear_output_btn": _Button(),
        "scrcpy_button": _Button(),
        "enter_button": _Button(),
        "theme_toggle_button": _Button(),
        "file_upload_button": _Button(),
        "shortcut_btn_w": _Button(),
    }
    core = ControllerCore.__new__(ControllerCore)
    core.view = SimpleNamespace(get_component=lambda name: comps.get(name))
    core.execute_command = lambda: None
    core.terminate_operation = lambda: None
    core.tts_handler = SimpleNamespace(show_tts_settings_popup=lambda: None)
    core.clear_output = lambda: None
    core.connection_handler = SimpleNamespace(show_scrcpy_popup=lambda: None)
    core.simulate_enter = lambda: None
    core.toggle_theme = lambda: None
    core.show_file_upload = lambda: None
    core.execute_shortcut = lambda _k: None

    core._bind_dashboard_events()

    assert len(comps["execute_button"].clicked.connected) == 1
    assert len(comps["shortcut_btn_w"].clicked.connected) == 1


def test_file_ops_show_upload_and_support_branches(tmp_path):
    class _View:
        def __init__(self, selected):
            self._selected = selected
            self.shown = None

        def show_file_upload_dialog(self):
            return self._selected

        def show_attached_files(self, files, _controller):
            self.shown = list(files)

    obj = FileOpsMixin.__new__(FileOpsMixin)
    toasts = []
    obj.show_toast = lambda msg, level: toasts.append((msg, level))
    obj.attached_files = []
    obj.is_executing = True
    obj.view = _View([])
    obj.show_file_upload()
    assert toasts and toasts[-1][1] == "warning"

    obj.is_executing = False
    f1 = tmp_path / "ok.txt"
    f2 = tmp_path / "bad.bin"
    f1.write_text("x", encoding="utf-8")
    f2.write_text("x", encoding="utf-8")
    obj.view = _View([str(f1), str(f2)])
    obj._check_file_supported = lambda p: (True, "") if p.endswith("ok.txt") else (False, "bad")

    obj.show_file_upload()
    assert obj.attached_files == [str(f1)]
    assert obj.view.shown == [str(f1)]


def test_command_mixin_execute_and_terminate_guards():
    obj = CommandMixin.__new__(CommandMixin)
    toasts = []
    obj.show_toast = lambda msg, level: toasts.append((msg, level))
    obj.is_executing = True
    obj.view = SimpleNamespace(get_component=lambda _name: _Text(""))
    obj.attached_files = []
    obj.execute_command()
    assert toasts[-1][1] == "warning"

    obj.is_executing = False
    obj.view = SimpleNamespace(get_component=lambda _name: _Text(""))
    obj.execute_command()
    assert toasts[-1][1] == "warning"

    obj.is_executing = False
    obj.terminate_operation()
    assert toasts[-1][1] == "warning"


def test_command_sync_device_to_task_chain_sets_fields_when_connected():
    obj = CommandMixin.__new__(CommandMixin)
    obj.task_manager = SimpleNamespace(is_connected=True, device_id="dev1", task_args={"k": "v"})
    obj.task_chain = SimpleNamespace(device_id="", task_args={})

    obj._sync_device_to_task_chain()
    assert obj.task_chain.device_id == "dev1"
    assert obj.task_chain.task_args == {"k": "v"}


def test_core_bind_ui_events_nav_and_message_exception_branch():
    nav_buttons = [_Button() for _ in range(6)]
    core = ControllerCore.__new__(ControllerCore)
    calls = []
    core.view = SimpleNamespace(get_component=lambda name: nav_buttons if name == "nav_buttons" else None)
    core.show_dashboard = lambda: calls.append("dashboard")
    core.connection_handler = SimpleNamespace(show_panel=lambda: calls.append("conn"))
    core.tts_handler = SimpleNamespace(show_panel=lambda: calls.append("tts"))
    core.system_handler = SimpleNamespace(show_history_panel=lambda: calls.append("history"), show_settings_panel=lambda: calls.append("settings"))
    core.dynamic_handler = SimpleNamespace(show_panel=lambda: calls.append("dynamic"))
    core._bind_dashboard_events = lambda: calls.append("bind_dashboard")
    core._bind_ui_events()
    assert calls and calls[-1] == "bind_dashboard"
    for i, btn in enumerate(nav_buttons):
        assert btn.clicked.connected, f"nav button {i} not connected"

    # process_messages exception swallowed branch
    core2 = ControllerCore.__new__(ControllerCore)

    class _QBad:
        def empty(self):
            return False

        def get_nowait(self):
            raise RuntimeError("boom")

    core2.message_queue = _QBad()
    core2.show_toast = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("must not be called"))
    core2.process_messages()

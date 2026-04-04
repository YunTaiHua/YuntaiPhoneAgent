from pathlib import Path
from types import SimpleNamespace

import pytest

import yuntai.handlers.system_handler as mod
from yuntai.handlers.system_handler import SystemHandler


class _Clicked:
    def __init__(self):
        self.connected = None

    def disconnect(self):
        raise TypeError()

    def connect(self, fn):
        self.connected = fn


class _Btn:
    def __init__(self):
        self.clicked = _Clicked()


class _HistoryText:
    def __init__(self):
        self.value = ""

    def setText(self, v):
        self.value = v


class _Signal:
    def __init__(self):
        self.connected = []

    def connect(self, fn):
        self.connected.append(fn)

    def emit(self, *args):
        for fn in self.connected:
            fn(*args)


class _StatusLabel:
    def __init__(self):
        self.text = ""
        self.style = ""

    def setText(self, v):
        self.text = v

    def setStyleSheet(self, s):
        self.style = s


class _ResultText:
    def __init__(self):
        self.lines = []

    def append(self, text):
        self.lines.append(text)

    def textCursor(self):
        return SimpleNamespace(movePosition=lambda *_a, **_k: None, MoveOperation=SimpleNamespace(End=1))

    def setTextCursor(self, _cursor):
        return None


def _make_handler(components=None):
    h = SystemHandler.__new__(SystemHandler)
    components = components or {}
    h.view = SimpleNamespace(get_component=lambda name: components.get(name), colors=SimpleNamespace())
    h.controller = SimpleNamespace(
        show_toast=lambda *args, **kwargs: None,
        connection_handler=SimpleNamespace(show_panel=lambda: None),
        tts_handler=SimpleNamespace(show_panel=lambda: None),
    )
    h.task_manager = SimpleNamespace(file_manager=SimpleNamespace(), utils=SimpleNamespace(), tts_manager=SimpleNamespace())
    return h


def test_bind_history_events_connects_buttons():
    refresh = _Btn()
    clear = _Btn()
    h = _make_handler({"refresh_history_btn": refresh, "clear_history_btn": clear})

    h._bind_history_events()
    assert refresh.clicked.connected == h.load_history_data
    assert clear.clicked.connected == h.clear_history_data


def test_load_history_data_formats_text():
    history_text = _HistoryText()
    h = _make_handler({"history_text": history_text})
    h.task_manager.file_manager.safe_read_json_file = lambda *_: {
        "sessions": [{"timestamp": "t", "target_app": "wx", "target_object": "a", "reply_generated": "ok"}],
        "free_chats": [{"timestamp": "t2", "user_input": "u", "assistant_reply": "r"}],
    }

    h.load_history_data()
    assert "聊天会话" in history_text.value
    assert "自由聊天" in history_text.value


def test_clear_history_data_confirm_cancel_and_success(monkeypatch):
    h = _make_handler()
    calls = []
    h.load_history_data = lambda: calls.append("load")
    h.task_manager.file_manager.safe_write_json_file = lambda *args, **kwargs: calls.append("write")
    h.controller = SimpleNamespace(show_toast=lambda msg, level: calls.append((msg, level)))

    monkeypatch.setattr("yuntai.handlers.system_handler.show_confirm_dialog", lambda *args, **kwargs: False)
    h.clear_history_data()
    assert calls == []

    monkeypatch.setattr("yuntai.handlers.system_handler.show_confirm_dialog", lambda *args, **kwargs: True)
    h.clear_history_data()
    assert "write" in calls
    assert "load" in calls


def test_show_file_management_handles_exception(monkeypatch):
    h = _make_handler()
    captured = []
    h.controller = SimpleNamespace(show_toast=lambda msg, level: captured.append((msg, level)))
    h.task_manager.tts_manager.default_tts_config = {
        "gpt_model_dir": "g",
        "sovits_model_dir": "s",
        "ref_audio_root": "a",
        "output_path": "o",
    }

    monkeypatch.setattr("yuntai.handlers.system_handler.QDialog", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    h.show_file_management()
    assert captured and captured[0][1] == "error"


def test_show_panels_and_bind_settings_events():
    calls = []
    settings_btns = [_Btn(), _Btn(), _Btn(), _Btn()]
    components = {f"settings_btn_{i}": settings_btns[i] for i in range(4)}
    h = _make_handler(components)
    h.view.create_history_page = lambda: calls.append("history_page")
    h.view.create_settings_page = lambda: calls.append("settings_page")
    h._bind_history_events = lambda: calls.append("bind_history")
    h.load_history_data = lambda: calls.append("load_history")
    h.controller.connection_handler = SimpleNamespace(show_panel=lambda: calls.append("conn"))
    h.controller.tts_handler = SimpleNamespace(show_panel=lambda: calls.append("tts"))
    h.check_system_gui = lambda: calls.append("check")
    h.show_file_management = lambda: calls.append("files")

    h.show_history_panel()
    h.show_settings_panel()

    assert calls[:4] == ["history_page", "bind_history", "load_history", "settings_page"]
    settings_btns[0].clicked.connected()
    settings_btns[1].clicked.connected()
    settings_btns[2].clicked.connected()
    settings_btns[3].clicked.connected()
    assert calls[-4:] == ["conn", "check", "tts", "files"]


def test_load_history_data_and_clear_history_error_paths(monkeypatch):
    h = _make_handler({"history_text": _HistoryText()})
    h.task_manager.file_manager.safe_read_json_file = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("bad"))
    h.load_history_data()

    errors = []
    h.controller = SimpleNamespace(show_toast=lambda msg, level: errors.append((msg, level)))
    h.task_manager.file_manager.safe_write_json_file = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("write-fail"))
    monkeypatch.setattr("yuntai.handlers.system_handler.show_confirm_dialog", lambda *a, **k: True)
    h.clear_history_data()
    assert errors and errors[0][1] == "error"


def test_check_system_gui_and_start_thread(monkeypatch):
    import yuntai.handlers.system_handler as mod

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    class _FakeDialog:
        instances = []

        def __init__(self, _parent, _is_harmony, _task_manager):
            self.tool_result = False
            self.api_result = False
            self.messages = []
            self.statuses = []
            self.colors = []
            self.__class__.instances.append(self)

        def append_text(self, text):
            self.messages.append(text)

        def set_status(self, text):
            self.statuses.append(text)

        def set_status_color(self, color):
            self.colors.append(color)

        def exec(self):
            return None

    monkeypatch.setattr(mod, "SystemCheckDialog", _FakeDialog)
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

    device_menu = SimpleNamespace(currentText=lambda: "Android")
    view = SimpleNamespace(get_component=lambda name: device_menu if name == "device_type_menu" else None)
    tts_mgr = SimpleNamespace(
        tts_available=False,
        tts_files_database={"gpt": [], "sovits": [], "audio": [], "text": []},
    )
    task_manager = SimpleNamespace(
        utils=SimpleNamespace(
            check_hdc=lambda: True,
            check_system_requirements=lambda: False,
            check_model_api=lambda *_a, **_k: False,
        ),
        tts_manager=tts_mgr,
        is_connected=False,
        device_id="",
        config={},
    )
    controller = SimpleNamespace(view=view, task_manager=task_manager)
    h = SystemHandler(controller)

    h.check_system_gui()
    d = _FakeDialog.instances[-1]
    assert any("ADB" in msg for msg in d.messages)
    assert any("模型API检查失败" in msg for msg in d.messages)
    assert d.statuses and "检查完成" in d.statuses[-1]
    assert d.colors

    h._current_check_thread = None
    h._on_start_check_thread()


def test_check_system_gui_harmony_success_and_file_management_success(monkeypatch):
    import yuntai.handlers.system_handler as mod

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    class _FakeDialog:
        instances = []

        def __init__(self, _parent, _is_harmony, _task_manager):
            self.tool_result = False
            self.api_result = False
            self.messages = []
            self.statuses = []
            self.colors = []
            self.__class__.instances.append(self)

        def append_text(self, text):
            self.messages.append(text)

        def set_status(self, text):
            self.statuses.append(text)

        def set_status_color(self, color):
            self.colors.append(color)

        def exec(self):
            return None

    monkeypatch.setattr(mod, "SystemCheckDialog", _FakeDialog)
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

    view = SimpleNamespace(
        get_component=lambda name: SimpleNamespace(currentText=lambda: "HarmonyOS (HDC)") if name == "device_type_menu" else None,
        colors=SimpleNamespace(),
    )
    tts_mgr = SimpleNamespace(
        tts_available=True,
        tts_files_database={"gpt": [1], "sovits": [1], "audio": [1], "text": [1]},
        default_tts_config={"gpt_model_dir": "g", "sovits_model_dir": "s", "ref_audio_root": "a", "output_path": "o"},
    )
    task_manager = SimpleNamespace(
        utils=SimpleNamespace(
            check_hdc=lambda: True,
            check_system_requirements=lambda: True,
            check_model_api=lambda *_a, **_k: True,
        ),
        tts_manager=tts_mgr,
        is_connected=True,
        device_id="dev",
        config={"connection_type": "usb"},
    )
    controller = SimpleNamespace(
        view=view,
        task_manager=task_manager,
        show_toast=lambda *_a, **_k: None,
        connection_handler=SimpleNamespace(show_panel=lambda: None),
        tts_handler=SimpleNamespace(show_panel=lambda: None),
    )
    h = SystemHandler(controller)

    h.check_system_gui()
    d = _FakeDialog.instances[-1]
    assert any("HDC" in msg for msg in d.messages)
    assert any("系统检查通过" in msg for msg in d.messages)

    class _Dlg:
        def __init__(self, *_a, **_k):
            pass

        def setWindowTitle(self, *_a, **_k):
            return None

        def setFixedSize(self, *_a, **_k):
            return None

        def setModal(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def accept(self):
            return None

        def exec(self):
            return None

    monkeypatch.setattr(mod, "QDialog", _Dlg)
    h.show_file_management()


def test_on_start_check_thread_starts_when_present(monkeypatch):
    import yuntai.handlers.system_handler as mod

    called = []

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    h = _make_handler()
    h._current_check_thread = lambda: called.append("ran")
    h._on_start_check_thread()
    assert called == ["ran"]


def test_system_check_dialog_signal_methods_forward_to_slots():
    d = mod.SystemCheckDialog.__new__(mod.SystemCheckDialog)
    d.append_text_signal = _Signal()
    d.set_status_signal = _Signal()
    d.set_status_color_signal = _Signal()
    d.result_text = _ResultText()
    d.status_label = _StatusLabel()

    d._connect_signals()
    d.append_text("line")
    d.set_status("ok")
    d.set_status_color("green")

    assert "line" in d.result_text.lines
    assert d.status_label.text == "ok"
    assert "green" in d.status_label.style


def test_show_file_management_info_building_and_close_bind(monkeypatch, tmp_path):
    import yuntai.handlers.system_handler as mod

    monkeypatch.setattr(mod, "CONVERSATION_HISTORY_FILE", str(tmp_path / "history.json"))
    monkeypatch.setattr(mod, "RECORD_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setattr(mod, "FOREVER_MEMORY_FILE", str(tmp_path / "mem.txt"))
    monkeypatch.setattr(mod, "CONNECTION_CONFIG_FILE", str(tmp_path / "conn.json"))

    class _Dialog:
        accepted = 0

        def __init__(self, *_a, **_k):
            pass

        def setWindowTitle(self, *_a, **_k):
            return None

        def setFixedSize(self, *_a, **_k):
            return None

        def setModal(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def accept(self):
            _Dialog.accepted += 1

        def exec(self):
            return None

    class _TextEdit:
        text_value = ""
        instances = []

        def __init__(self, *_a, **_k):
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setReadOnly(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def setText(self, text):
            _TextEdit.text_value = text

    class _Btn2:
        last_clicked = None

        def __init__(self, *_a, **_k):
            self.clicked = _Signal()
            self.clicked.connect(lambda: None)
            _Btn2.last_clicked = self.clicked

        def setFont(self, *_a, **_k):
            return None

        def setFixedHeight(self, *_a, **_k):
            return None

        def setFixedWidth(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

    class _Frame2:
        def setStyleSheet(self, *_a, **_k):
            return None

    class _Layout2:
        def __init__(self, *_a, **_k):
            return None

        def setContentsMargins(self, *_a, **_k):
            return None

        def setSpacing(self, *_a, **_k):
            return None

        def addWidget(self, *_a, **_k):
            return None

    class _Label2:
        def __init__(self, *_a, **_k):
            return None

        def setFont(self, *_a, **_k):
            return None

        def setAlignment(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

    monkeypatch.setattr(mod, "QDialog", _Dialog)
    monkeypatch.setattr(mod, "QTextEdit", _TextEdit)
    monkeypatch.setattr(mod, "QPushButton", _Btn2)
    monkeypatch.setattr(mod, "QFrame", _Frame2)
    monkeypatch.setattr(mod, "QVBoxLayout", _Layout2)
    monkeypatch.setattr(mod, "QLabel", _Label2)

    toasts = []
    h = _make_handler()
    h.view = SimpleNamespace(colors=mod.ThemeColors, get_component=lambda _name: None)
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.task_manager.tts_manager.default_tts_config = {
        "gpt_model_dir": "g",
        "sovits_model_dir": "s",
        "ref_audio_root": "a",
        "output_path": "o",
    }
    h.show_file_management()
    assert not toasts


def test_system_check_dialog_slots_and_format_action_lines():
    dlg = mod.SystemCheckDialog.__new__(mod.SystemCheckDialog)

    class _Cursor:
        MoveOperation = SimpleNamespace(End=1)

        def __init__(self):
            self.moves = 0

        def movePosition(self, _op):
            self.moves += 1

    class _Text:
        def __init__(self):
            self.lines = []
            self.cursor = _Cursor()

        def append(self, text):
            self.lines.append(text)

        def textCursor(self):
            return self.cursor

        def setTextCursor(self, _cursor):
            return None

    dlg.result_text = _Text()
    dlg.status_label = SimpleNamespace(text="", style="", setText=lambda v: setattr(dlg.status_label, "text", v), setStyleSheet=lambda v: setattr(dlg.status_label, "style", v))
    dlg._on_append_text("ok")
    dlg._on_set_status("s")
    dlg._on_set_status_color("red")
    dlg.scroll_to_bottom()
    assert dlg.result_text.lines == ["ok"]
    assert dlg.status_label.text == "s"
    assert "red" in dlg.status_label.style
    assert dlg.result_text.cursor.moves == 2

    dlg.append_text_signal = SimpleNamespace(emit=lambda v: setattr(dlg, "_emit1", v))
    dlg.set_status_signal = SimpleNamespace(emit=lambda v: setattr(dlg, "_emit2", v))
    dlg.set_status_color_signal = SimpleNamespace(emit=lambda v: setattr(dlg, "_emit3", v))
    dlg.append_text("a")
    dlg.set_status("b")
    dlg.set_status_color("c")
    assert dlg._emit1 == "a" and dlg._emit2 == "b" and dlg._emit3 == "c"

    from yuntai.gui.controller import core as controller_core_mod
    assert controller_core_mod._format_action_lines("x") == "x"
    assert controller_core_mod._format_action_lines({"a": 1, "b": 2}) == "a: 1\nb: 2"




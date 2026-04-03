from types import SimpleNamespace

import yuntai.handlers.connection_handler as mod
from yuntai.handlers.connection_handler import ConnectionHandler


class _LineEdit:
    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text


class _Check:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _Label:
    def __init__(self):
        self.text = ""
        self.style = ""

    def setText(self, v):
        self.text = v

    def setStyleSheet(self, v):
        self.style = v


class _Frame:
    def __init__(self):
        self.hidden = False
        self.shown = False

    def hide(self):
        self.hidden = True

    def show(self):
        self.shown = True


class _Signal:
    def __init__(self):
        self.connected = []

    def disconnect(self):
        raise TypeError()

    def connect(self, fn):
        self.connected.append(fn)


class _Btn:
    def __init__(self):
        self.clicked = _Signal()


class _StubLabel:
    def __init__(self, *_a, **_k):
        self.text_value = ""

    def setFont(self, *_a, **_k):
        return None

    def setAlignment(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setText(self, value):
        self.text_value = value


class _StubTextEdit:
    def __init__(self, *_a, **_k):
        self.text_value = ""

    def setFont(self, *_a, **_k):
        return None

    def setReadOnly(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setText(self, value):
        self.text_value = value


class _StubButton:
    def __init__(self, *_a, **_k):
        self.clicked = _Signal()

    def setFont(self, *_a, **_k):
        return None

    def setFixedHeight(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None


class _StubFrame:
    def setStyleSheet(self, *_a, **_k):
        return None


class _StubLayout:
    def __init__(self, *_a, **_k):
        self.items = []

    def setContentsMargins(self, *_a, **_k):
        return None

    def setSpacing(self, *_a, **_k):
        return None

    def addWidget(self, *_a, **_k):
        return None

    def addLayout(self, *_a, **_k):
        return None

    def addStretch(self, *_a, **_k):
        return None

    def count(self):
        return 0

    def takeAt(self, *_a, **_k):
        return SimpleNamespace(widget=lambda: None)


class _DialogStub:
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
        self.__class__.accepted += 1

    def exec(self):
        return None


def _make_handler(components):
    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(get_component=lambda name: components.get(name))
    h.controller = SimpleNamespace(show_toast=lambda *args, **kwargs: None)
    h.task_manager = SimpleNamespace()
    return h


def test_get_device_type_and_connection_type():
    components = {
        "device_type_menu": SimpleNamespace(currentText=lambda: "HarmonyOS (HDC)"),
        "usb_option": _Check(True),
    }
    h = _make_handler(components)

    assert h._get_device_type() == "harmony"
    assert h._get_connection_type() == "usb"


def test_get_device_type_display_and_defaults():
    h = _make_handler({})
    assert h._get_device_type() == "android"
    assert h._get_device_type_display() == "Android (ADB)"

    h2 = _make_handler({"device_type_menu": SimpleNamespace(currentText=lambda: "HarmonyOS (HDC)")})
    assert h2._get_device_type_display() == "HarmonyOS (HDC)"


def test_get_connection_config_from_ui_usb_missing_id_shows_warning():
    calls = []
    components = {
        "usb_option": _Check(True),
        "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
        "usb_entry": _LineEdit(""),
    }
    h = _make_handler(components)
    h.controller = SimpleNamespace(show_toast=lambda msg, level: calls.append((msg, level)))

    assert h._get_connection_config_from_ui() is None
    assert calls and calls[0][1] == "warning"


def test_get_connection_config_from_ui_wireless_defaults_port():
    components = {
        "usb_option": _Check(False),
        "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
        "ip_entry": _LineEdit("192.168.1.20"),
        "port_entry": _LineEdit(""),
    }
    h = _make_handler(components)

    config = h._get_connection_config_from_ui()
    assert config["connection_type"] == "wireless"
    assert config["wireless_port"] == "5555"
    assert config["wireless_ip"] == "192.168.1.20"


def test_get_connection_config_from_ui_usb_and_wireless_ip_missing_warning():
    calls = []
    usb_components = {
        "usb_option": _Check(True),
        "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
        "usb_entry": _LineEdit(" dev-1 "),
    }
    h = _make_handler(usb_components)
    cfg = h._get_connection_config_from_ui()
    assert cfg["usb_device_id"] == "dev-1"

    h2 = _make_handler(
        {
            "usb_option": _Check(False),
            "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
            "ip_entry": _LineEdit(""),
            "port_entry": _LineEdit("6666"),
        }
    )
    h2.controller = SimpleNamespace(show_toast=lambda msg, level: calls.append((msg, level)))
    assert h2._get_connection_config_from_ui() is None
    assert calls and calls[0][1] == "warning"


def test_do_update_connection_status_updates_labels():
    indicator = _Label()
    status = _Label()
    info = _Label()
    components = {
        "connection_indicator": indicator,
        "connection_status_label": status,
        "connection_info_label": info,
    }
    h = _make_handler(components)

    h._do_update_connection_status(True)
    assert "已连接" in indicator.text
    assert "已连接" in status.text

    h._do_update_connection_status(False)
    assert "未连接" in indicator.text
    assert "未连接" in status.text
    assert info.text == ""


def test_on_connection_type_changed_toggles_frames():
    usb_frame = _Frame()
    wireless_frame = _Frame()
    h = _make_handler({"usb_frame": usb_frame, "wireless_frame": wireless_frame})

    h._on_connection_type_changed(SimpleNamespace(text=lambda: "USB连接"))
    assert wireless_frame.hidden is True and usb_frame.shown is True

    usb_frame2 = _Frame()
    wireless_frame2 = _Frame()
    h2 = _make_handler({"usb_frame": usb_frame2, "wireless_frame": wireless_frame2})
    h2._on_connection_type_changed(SimpleNamespace(text=lambda: "无线连接"))
    assert usb_frame2.hidden is True and wireless_frame2.shown is True


def test_connect_detect_disconnect_gui_paths(monkeypatch):
    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    queue_calls = []
    toast_calls = []
    sync_calls = []
    status_calls = []
    components = {
        "usb_option": _Check(True),
        "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
        "usb_entry": _LineEdit("dev-id"),
    }
    h = _make_handler(components)
    h.controller = SimpleNamespace(
        message_queue=SimpleNamespace(put=lambda item: queue_calls.append(item)),
        show_toast=lambda msg, level: toast_calls.append((msg, level)),
        _sync_device_to_task_chain=lambda: sync_calls.append("sync"),
    )
    h.task_manager = SimpleNamespace(
        connect_device=lambda _cfg: (True, "dev-id", "ok"),
        detect_devices=lambda _dt: ["a", "b"],
        disconnect_device=lambda: status_calls.append("disconnect"),
    )
    h._update_connection_status_gui = lambda connected: status_calls.append(connected)

    h.connect_device_gui()
    assert ("success", "✅ ok") in queue_calls
    assert True in status_calls
    assert "sync" in sync_calls

    h.task_manager.connect_device = lambda _cfg: (False, None, "bad")
    h.connect_device_gui()
    assert ("error", "❌ 连接失败: bad") in queue_calls

    class _Dialog:
        shown = []

        def __init__(self, _view, _tm, _ctrl):
            pass

        def show_result(self, devices, _dtype, _display):
            self.__class__.shown.append(devices)

        def exec(self):
            return None

    monkeypatch.setattr(mod, "DeviceDetectDialog", _Dialog)
    h.detect_devices_gui()
    assert _Dialog.shown[-1] == ["a", "b"]

    h.task_manager.detect_devices = lambda _dt: (_ for _ in ()).throw(RuntimeError("x"))
    h.detect_devices_gui()
    assert _Dialog.shown[-1] == []
    assert toast_calls and toast_calls[-1][1] == "error"

    h.disconnect_device()
    assert "disconnect" in status_calls
    assert False in status_calls


def test_bind_events_and_show_panel_paths():
    detect = _Btn()
    connect = _Btn()
    disconnect = _Btn()
    group = SimpleNamespace(buttonClicked=_Signal())
    comps = {
        "detect_devices_btn": detect,
        "connect_device_btn": connect,
        "disconnect_device_btn": disconnect,
        "conn_button_group": group,
    }

    handler = ConnectionHandler.__new__(ConnectionHandler)
    handler.view = SimpleNamespace(
        get_component=lambda name: comps.get(name),
        create_connection_page=lambda: None,
    )
    handler.task_manager = SimpleNamespace(is_connected=True)
    handler.detect_devices_gui = lambda: None
    handler.connect_device_gui = lambda: None
    handler.disconnect_device = lambda: None
    handler._on_connection_type_changed = lambda *_a, **_k: None
    calls = []
    handler._update_connection_status_gui = lambda connected: calls.append(connected)

    handler._bind_events()
    assert len(detect.clicked.connected) == 1
    assert len(group.buttonClicked.connected) == 1

    handler.show_panel()
    assert calls and calls[-1] is True


def test_get_connection_config_wireless_custom_port_and_no_widgets():
    # wireless with custom port
    h = _make_handler(
        {
            "usb_option": _Check(False),
            "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
            "ip_entry": _LineEdit("10.0.0.2"),
            "port_entry": _LineEdit("6666"),
        }
    )
    cfg = h._get_connection_config_from_ui()
    assert cfg["wireless_ip"] == "10.0.0.2"
    assert cfg["wireless_port"] == "6666"

    # no ip/port widgets: returns base config (branch coverage)
    h2 = _make_handler(
        {
            "usb_option": _Check(False),
            "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
        }
    )
    cfg2 = h2._get_connection_config_from_ui()
    assert cfg2["connection_type"] == "wireless"


def test_connect_device_gui_without_config_short_circuit(monkeypatch):
    h = _make_handler({})
    h._get_connection_config_from_ui = lambda: None
    called = []

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            called.append("constructed")
            self._target = target

        def start(self):
            called.append("started")

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    h.connect_device_gui()
    assert called == []


def test_detect_devices_gui_dialog_exception_path(monkeypatch):
    h = _make_handler({"device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)")})
    h.controller = SimpleNamespace(show_toast=lambda *_a, **_k: None)
    h.task_manager = SimpleNamespace(detect_devices=lambda *_a, **_k: ["x"])

    monkeypatch.setattr(mod, "DeviceDetectDialog", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("dialog boom")))
    import pytest

    with pytest.raises(RuntimeError):
        h.detect_devices_gui()


def test_connection_type_changed_and_update_status_missing_components():
    h = _make_handler({})
    # no frames -> branch noop
    h._on_connection_type_changed(SimpleNamespace(text=lambda: "USB连接"))
    h._do_update_connection_status(True)
    h._do_update_connection_status(False)


def test_update_connection_status_signal_emit_path():
    emitted = []
    h = _make_handler({})
    h.update_status_signal = SimpleNamespace(emit=lambda connected: emitted.append(connected))
    h._update_connection_status_gui(True)
    h._update_connection_status_gui(False)
    assert emitted == [True, False]


def test_connection_handler_init_and_show_connection_form_noop():
    updates = []

    class _FakeSignal:
        def connect(self, fn):
            updates.append(fn)

    h = ConnectionHandler.__new__(ConnectionHandler)
    h.update_status_signal = _FakeSignal()

    controller = SimpleNamespace(
        view=SimpleNamespace(),
        task_manager=SimpleNamespace(),
    )

    ConnectionHandler.__init__(h, controller)
    assert h.controller is controller
    assert h.view is controller.view
    assert h.task_manager is controller.task_manager
    assert updates and updates[0] == h._do_update_connection_status

    # Compatibility no-op branch
    assert h._show_connection_form() is None


def test_device_detect_dialog_internal_renderers(monkeypatch):
    # Build dialog object without Qt init and execute renderer branches directly.
    copied = []
    monkeypatch.setattr(mod.pyperclip, "copy", lambda text: copied.append(text))

    class _BtnSig:
        def __init__(self):
            self.connected = []

        def connect(self, fn):
            self.connected.append(fn)

    class _BtnW:
        instances = []

        def __init__(self, *_a, **_k):
            self.clicked = _BtnSig()
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setFixedHeight(self, *_a, **_k):
            return None

        def setFixedWidth(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

    class _TextW:
        instances = []

        def __init__(self, *_a, **_k):
            self.text = ""
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setReadOnly(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def setText(self, text):
            self.text = text

    class _LblW:
        def __init__(self, *_a, **_k):
            self.text = ""

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def setAlignment(self, *_a, **_k):
            return None

        def setText(self, text):
            self.text = text

    class _LayoutW:
        def addWidget(self, *_a, **_k):
            return None

        def addLayout(self, *_a, **_k):
            return None

        def addStretch(self, *_a, **_k):
            return None

    monkeypatch.setattr(mod, "QPushButton", _BtnW)
    monkeypatch.setattr(mod, "QTextEdit", _TextW)
    monkeypatch.setattr(mod, "QLabel", _LblW)
    monkeypatch.setattr(mod, "QHBoxLayout", lambda *_a, **_k: _LayoutW())

    toasts = []
    d = mod.DeviceDetectDialog.__new__(mod.DeviceDetectDialog)
    d.devices = ["id1", "id2"]
    d.device_type = "android"
    d.device_type_display = "Android (ADB)"
    d.colors = mod.ThemeColors
    d.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    d.status_label = _LblW()
    d.content_layout = _LayoutW()

    d._show_devices_found()
    assert toasts and toasts[-1][1] == "success"

    # trigger copy callback
    copy_btn = _BtnW.instances[-1]
    copy_btn.clicked.connected[0]()
    assert copied

    toasts.clear()
    d.device_type = mod.DEVICE_TYPE_HARMONY
    d._show_no_devices()
    assert toasts and toasts[-1][1] == "warning"
    copy_btn2 = _BtnW.instances[-1]
    copy_btn2.clicked.connected[0]()
    assert len(copied) >= 2


def test_device_detect_dialog_show_result_paths(monkeypatch):
    toasts = []
    dialog = mod.DeviceDetectDialog.__new__(mod.DeviceDetectDialog)
    dialog.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    dialog.type_label = _StubLabel()
    dialog.status_label = _StubLabel()
    dialog.content_layout = _StubLayout()
    dialog._show_devices_found = lambda: toasts.append(("found", "success"))
    dialog._show_no_devices = lambda: toasts.append(("none", "warning"))

    dialog._on_show_result(["dev1", "dev2"], "android", "Android (ADB)")
    assert dialog.devices == ["dev1", "dev2"]

    dialog._on_show_result([], "harmony", "HarmonyOS (HDC)")
    assert dialog.device_type == "harmony"
    assert any(level in {"success", "warning"} for _, level in toasts)


def test_show_scrcpy_popup_start_path_with_selected_device(monkeypatch):
    # Reuse lightweight stubs from popup tests to avoid Qt dependencies.
    class _Signal2:
        def __init__(self):
            self.connected = []

        def connect(self, fn):
            self.connected.append(fn)

    class _Button2:
        instances = []

        def __init__(self, text="", *_a, **_k):
            self.text = text
            self.clicked = _Signal2()
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setFixedHeight(self, *_a, **_k):
            return None

        def setFixedWidth(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

    class _Dialog2:
        last = None

        def __init__(self, *_a, **_k):
            self.accepted = False
            self.__class__.last = self

        def setWindowTitle(self, *_a, **_k):
            return None

        def setFixedSize(self, *_a, **_k):
            return None

        def setModal(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def accept(self):
            self.accepted = True

        def exec(self):
            return 0

    class _Layout2:
        def __init__(self, *_a, **_k):
            return None

        def setContentsMargins(self, *_a, **_k):
            return None

        def setSpacing(self, *_a, **_k):
            return None

        def addWidget(self, *_a, **_k):
            return None

        def addLayout(self, *_a, **_k):
            return None

    class _Combo2:
        instances = []

        def __init__(self):
            self.items = []
            self.current = ""
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def addItems(self, items):
            self.items.extend(items)
            if items:
                self.current = items[0]
            if items:
                self.current = items[0]
            if items:
                self.current = items[0]
            if items:
                self.current = items[0]

        def currentText(self):
            return self.current

    class _Check2:
        def __init__(self, *_a, **_k):
            self._checked = True

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def isChecked(self):
            return self._checked

    class _Label2:
        def __init__(self, *_a, **_k):
            return None

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def setAlignment(self, *_a, **_k):
            return None

    class _Frame2:
        def setStyleSheet(self, *_a, **_k):
            return None

    monkeypatch.setattr(mod, "QDialog", _Dialog2)
    monkeypatch.setattr(mod, "QVBoxLayout", _Layout2)
    monkeypatch.setattr(mod, "QHBoxLayout", _Layout2)
    monkeypatch.setattr(mod, "QLabel", _Label2)
    monkeypatch.setattr(mod, "QPushButton", _Button2)
    monkeypatch.setattr(mod, "QFrame", _Frame2)
    monkeypatch.setattr(mod, "QComboBox", _Combo2)
    monkeypatch.setattr(mod, "QCheckBox", _Check2)
    monkeypatch.setattr(mod, "sanitize_device_id", lambda v: v)

    process_list = []
    toasts = []

    class _FakeProcess:
        def wait(self):
            return 0

    monkeypatch.setattr(
        mod.subprocess,
        "Popen",
        lambda *args, **kwargs: process_list.append((args, kwargs)) or _FakeProcess(),
    )

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(colors=mod.ThemeColors)
    h.task_manager = SimpleNamespace(detect_devices=lambda: ["dev-1"])
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        scrcpy_path="scrcpy",
        active_subprocesses=[],
    )

    h.show_scrcpy_popup()

    start_btn = next(b for b in _Button2.instances if b.text == "启动投屏")
    start_btn.clicked.connected[0]()

    assert process_list
    cmd = process_list[0][0][0]
    assert "scrcpy" in cmd[0]
    assert "-s" in cmd and "dev-1" in cmd
    assert "--always-on-top" in cmd
    assert any(level == "success" for _, level in toasts)
    assert _Dialog2.last.accepted is True


def test_show_scrcpy_popup_validation_and_error_branches(monkeypatch):
    class _Signal2:
        def __init__(self):
            self.connected = []

        def connect(self, fn):
            self.connected.append(fn)

    class _Button2:
        instances = []

        def __init__(self, text="", *_a, **_k):
            self.text = text
            self.clicked = _Signal2()
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setFixedHeight(self, *_a, **_k):
            return None

        def setFixedWidth(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

    class _Dialog2:
        def __init__(self, *_a, **_k):
            self.accepted = False

        def setWindowTitle(self, *_a, **_k):
            return None

        def setFixedSize(self, *_a, **_k):
            return None

        def setModal(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def accept(self):
            self.accepted = True

        def exec(self):
            return 0

    class _Layout2:
        def __init__(self, *_a, **_k):
            return None

        def setContentsMargins(self, *_a, **_k):
            return None

        def setSpacing(self, *_a, **_k):
            return None

        def addWidget(self, *_a, **_k):
            return None

        def addLayout(self, *_a, **_k):
            return None

    class _Combo2:
        instances = []

        def __init__(self):
            self.items = []
            self.current = ""
            self.__class__.instances.append(self)

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def addItems(self, items):
            self.items.extend(items)
            if items:
                self.current = items[0]

        def currentText(self):
            return self.current

    class _Check2:
        def __init__(self, *_a, **_k):
            self._checked = False

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def isChecked(self):
            return self._checked

    class _Label2:
        def __init__(self, *_a, **_k):
            return None

        def setFont(self, *_a, **_k):
            return None

        def setStyleSheet(self, *_a, **_k):
            return None

        def setAlignment(self, *_a, **_k):
            return None

    class _Frame2:
        def setStyleSheet(self, *_a, **_k):
            return None

    monkeypatch.setattr(mod, "QDialog", _Dialog2)
    monkeypatch.setattr(mod, "QVBoxLayout", _Layout2)
    monkeypatch.setattr(mod, "QHBoxLayout", _Layout2)
    monkeypatch.setattr(mod, "QLabel", _Label2)
    monkeypatch.setattr(mod, "QPushButton", _Button2)
    monkeypatch.setattr(mod, "QFrame", _Frame2)
    monkeypatch.setattr(mod, "QComboBox", _Combo2)
    monkeypatch.setattr(mod, "QCheckBox", _Check2)

    toasts = []
    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(colors=mod.ThemeColors)
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        scrcpy_path="scrcpy",
        active_subprocesses=[],
    )

    # 1) no devices -> warning
    h.task_manager = SimpleNamespace(detect_devices=lambda: [])
    _Button2.instances.clear()
    h.show_scrcpy_popup()
    start_btn = next(b for b in _Button2.instances if b.text == "启动投屏")
    start_btn.clicked.connected[0]()
    assert any(level == "warning" for _, level in toasts)

    # 2) sanitize failure -> error
    toasts.clear()
    h.task_manager = SimpleNamespace(detect_devices=lambda: ["bad-device"])
    monkeypatch.setattr(mod, "sanitize_device_id", lambda _v: (_ for _ in ()).throw(ValueError("bad")))
    _Button2.instances.clear()
    _Combo2.instances.clear()
    h.show_scrcpy_popup()
    if _Combo2.instances:
        _Combo2.instances[-1].current = "bad-device"
    start_btn = next(b for b in _Button2.instances if b.text == "启动投屏")
    start_btn.clicked.connected[0]()
    assert any(level == "error" for _, level in toasts)

    # 2.1) empty selected device -> warning
    toasts.clear()
    monkeypatch.setattr(mod, "sanitize_device_id", lambda v: v)
    _Button2.instances.clear()
    _Combo2.instances.clear()
    h.show_scrcpy_popup()
    if _Combo2.instances:
        _Combo2.instances[-1].current = ""
    start_btn = next(b for b in _Button2.instances if b.text == "启动投屏")
    start_btn.clicked.connected[0]()
    assert any(level == "warning" for _, level in toasts)

    # 3) subprocess exception in worker -> error
    toasts.clear()
    monkeypatch.setattr(mod, "sanitize_device_id", lambda v: v)
    monkeypatch.setattr(
        mod.subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    _Button2.instances.clear()
    _Combo2.instances.clear()
    h.show_scrcpy_popup()
    if _Combo2.instances:
        _Combo2.instances[-1].current = "bad-device"
    start_btn = next(b for b in _Button2.instances if b.text == "启动投屏")
    start_btn.clicked.connected[0]()
    assert any(level == "error" for _, level in toasts)

    # 4) thread start wrapper exception -> outer error path
    toasts.clear()
    monkeypatch.setattr(mod, "sanitize_device_id", lambda v: v)

    class _ImmediateProcess:
        def wait(self):
            return 0

    monkeypatch.setattr(mod.subprocess, "Popen", lambda *args, **kwargs: _ImmediateProcess())
    monkeypatch.setattr(
        mod.threading,
        "Thread",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("thread-fail")),
    )

    _Button2.instances.clear()
    _Combo2.instances.clear()
    h.show_scrcpy_popup()
    if _Combo2.instances:
        _Combo2.instances[-1].current = "dev-1"
    start_btn = next(b for b in _Button2.instances if b.text == "启动投屏")
    start_btn.clicked.connected[0]()
    assert any(level == "error" for _, level in toasts)

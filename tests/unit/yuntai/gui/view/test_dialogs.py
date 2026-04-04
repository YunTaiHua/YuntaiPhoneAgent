from pathlib import Path
from types import SimpleNamespace

from yuntai.gui.view import dialogs as mod


def test_dialogs_show_file_upload_dialog(monkeypatch):
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg.colors = SimpleNamespace()
    monkeypatch.setattr(mod.QFileDialog, "getOpenFileNames", lambda *a, **k: (["/path/to/file.txt"], ""))
    result = dlg.show_file_upload_dialog()
    assert result == ["/path/to/file.txt"]


def test_dialogs_get_component():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg.components = {"test_widget": "widget_value"}
    assert dlg.get_component("test_widget") == "widget_value"
    assert dlg.get_component("missing") is None


def test_dialogs_update_component():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)

    class _FakeWidget:
        def __init__(self):
            self.text = None
            self.style = None

        def setText(self, value):
            self.text = value

        def setStyleSheet(self, value):
            self.style = value

    widget = _FakeWidget()
    dlg.components = {"test_widget": widget}
    dlg.update_component("test_widget", text="new text", style="new style")
    assert widget.text == "new text"
    assert widget.style == "new style"


def test_dialogs_show_enter_button():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)

    class _FakeButton:
        def __init__(self):
            self.visible = False

        def show(self):
            self.visible = True

        def hide(self):
            self.visible = False

    btn = _FakeButton()
    dlg.components = {"enter_button": btn}
    dlg.show_enter_button()
    assert btn.visible is True


def test_dialogs_hide_enter_button():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)

    class _FakeButton:
        def __init__(self):
            self.visible = True

        def show(self):
            self.visible = True

        def hide(self):
            self.visible = False

    btn = _FakeButton()
    dlg.components = {"enter_button": btn}
    dlg.hide_enter_button()
    assert btn.visible is False


def test_dialogs_show_attached_files_empty(monkeypatch):
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg.colors = SimpleNamespace(BG_HOVER="#eee", TEXT_PRIMARY="#333", DANGER="#f00", DANGER_HOVER="#d00", WARNING="#fa0", WARNING_HOVER="#d80", TEXT_LIGHT="#fff")

    class _FakeLayout:
        def __init__(self):
            self.items = []

        def count(self):
            return 0

        def takeAt(self, idx):
            return None

        def addWidget(self, widget, *args):
            self.items.append(widget)

        def addStretch(self, n):
            pass

    class _FakeScrollFrame:
        def __init__(self):
            self._layout = _FakeLayout()

        def layout(self):
            return self._layout

    dlg.components = {"files_list_scroll_frame": _FakeScrollFrame()}
    dlg.show_attached_files([])
    assert len(dlg.components["files_list_scroll_frame"]._layout.items) == 0


def test_dialogs_show_attached_files_no_scroll_frame(monkeypatch):
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg.colors = SimpleNamespace()
    dlg.components = {}
    result = dlg.show_attached_files(["/path/to/file.txt"])
    assert result is None


def test_dialogs_show_attached_files_with_files(monkeypatch):
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg.colors = SimpleNamespace(BG_HOVER="#eee", TEXT_PRIMARY="#333", DANGER="#f00", DANGER_HOVER="#d00", WARNING="#fa0", WARNING_HOVER="#d80", TEXT_LIGHT="#fff")

    class _FakeLayout:
        def __init__(self):
            self.items = []
            self.count_val = 0

        def count(self):
            return self.count_val

        def takeAt(self, idx):
            return SimpleNamespace(widget=lambda: None)

        def addWidget(self, widget, *args, **kwargs):
            self.items.append(widget)

        def addStretch(self, n):
            pass

    class _FakeScrollFrame:
        def __init__(self):
            self._layout = _FakeLayout()

        def layout(self):
            return self._layout

    dlg.components = {"files_list_scroll_frame": _FakeScrollFrame()}

    class _FakeController:
        removed = []

        def remove_attached_file(self, f):
            self.removed.append(f)

        def clear_attached_files(self):
            pass

    controller = _FakeController()
    dlg.show_attached_files(["/path/to/image.jpg", "/path/to/video.mp4", "/path/to/audio.mp3"], controller)
    assert len(dlg.components["files_list_scroll_frame"]._layout.items) > 0


def test_dialogs_on_device_type_change():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    calls = []
    dlg._device_type_callback = lambda dt: calls.append(dt)
    dlg._on_device_type_change("harmony")
    assert calls == ["harmony"]


def test_dialogs_on_device_type_change_no_callback():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg._on_device_type_change("android")


def test_dialogs_update_component_missing_widget():
    dlg = mod.DialogsMixin.__new__(mod.DialogsMixin)
    dlg.components = {}
    dlg.update_component("missing_widget", text="new text")

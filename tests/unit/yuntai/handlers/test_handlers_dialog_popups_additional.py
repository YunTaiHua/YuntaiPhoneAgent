from types import SimpleNamespace

import yuntai.handlers.connection_handler as conn_mod
import yuntai.handlers.tts_handler as tts_mod


class _Signal:
    def __init__(self):
        self._cb = None

    def connect(self, cb):
        self._cb = cb

    def emit(self, *args, **kwargs):
        if self._cb:
            self._cb(*args, **kwargs)


class _Button:
    def __init__(self, *args, **kwargs):
        self.clicked = _Signal()

    def setFont(self, *_a, **_k):
        return None

    def setFixedHeight(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None


class _CheckBox:
    def __init__(self, checked=False):
        self._checked = checked

    def setFont(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setChecked(self, v):
        self._checked = bool(v)

    def isChecked(self):
        return self._checked


class _Combo:
    def __init__(self):
        self._items = []
        self._current = ""

    def setFont(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None

    def addItems(self, items):
        self._items.extend(list(items))
        if not self._current and self._items:
            self._current = self._items[0]

    def setCurrentText(self, text):
        self._current = text

    def currentText(self):
        return self._current


class _Label:
    def __init__(self, text=""):
        self._text = text

    def setFont(self, *_a, **_k):
        return None

    def setAlignment(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None

    def setText(self, text):
        self._text = text


class _Frame:
    def setStyleSheet(self, *_a, **_k):
        return None


class _Layout:
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

    def addStretch(self, *_a, **_k):
        return None


class _Dialog:
    last_instance = None

    def __init__(self, *_a, **_k):
        self.accepted = False
        self.rejected = False
        _Dialog.last_instance = self

    def setWindowTitle(self, *_a, **_k):
        return None

    def setFixedSize(self, *_a, **_k):
        return None

    def setModal(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def exec(self):
        return 0

    def accept(self):
        self.accepted = True

    def reject(self):
        self.rejected = True


class _TreeItem:
    def __init__(self, texts):
        self._t = texts[0]

    def text(self, _col):
        return self._t


class _Tree:
    def __init__(self):
        self._items = []
        self._selected = []

    def setHeaderHidden(self, *_a, **_k):
        return None

    def setFont(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def addTopLevelItem(self, item):
        self._items.append(item)
        if not self._selected:
            self._selected = [item]

    def selectedItems(self):
        return self._selected


def _patch_common_dialog_widgets(monkeypatch, module):
    monkeypatch.setattr(module, "QDialog", _Dialog)
    monkeypatch.setattr(module, "QVBoxLayout", _Layout)
    monkeypatch.setattr(module, "QHBoxLayout", _Layout)
    monkeypatch.setattr(module, "QLabel", _Label)
    monkeypatch.setattr(module, "QPushButton", _Button)
    monkeypatch.setattr(module, "QFrame", _Frame)
    monkeypatch.setattr(module, "QComboBox", _Combo)
    monkeypatch.setattr(module, "QCheckBox", _CheckBox)
    if hasattr(module, "QTreeWidget"):
        monkeypatch.setattr(module, "QTreeWidget", _Tree)
    if hasattr(module, "QTreeWidgetItem"):
        monkeypatch.setattr(module, "QTreeWidgetItem", _TreeItem)


def test_connection_handler_show_scrcpy_popup_no_devices(monkeypatch):
    _patch_common_dialog_widgets(monkeypatch, conn_mod)

    toasts = []
    handler = conn_mod.ConnectionHandler.__new__(conn_mod.ConnectionHandler)
    handler.view = SimpleNamespace(colors=conn_mod.ThemeColors)
    handler.task_manager = SimpleNamespace(detect_devices=lambda: [])
    handler.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        scrcpy_path="scrcpy",
        active_subprocesses=[],
    )

    started = []

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            started.append(True)
            if self._target:
                self._target()

    monkeypatch.setattr(conn_mod.threading, "Thread", _ImmediateThread)

    handler.show_scrcpy_popup()

    btn = _Dialog.last_instance
    assert btn is not None
    assert started == []


def test_tts_create_file_selection_popup_smoke(monkeypatch):
    _patch_common_dialog_widgets(monkeypatch, tts_mod)
    monkeypatch.setattr(tts_mod, "show_warning_dialog", lambda *_a, **_k: None)

    handler = tts_mod.TTSHandler.__new__(tts_mod.TTSHandler)
    handler.view = SimpleNamespace(colors=tts_mod.ThemeColors)

    monkeypatch.setattr(tts_mod, "QPushButton", _Button)

    def _dialog_exec(self):
        return 0

    monkeypatch.setattr(_Dialog, "exec", _dialog_exec, raising=False)

    handler._create_file_selection_popup(
        "选择",
        {"a.txt": "x", "b.txt": "y"},
        lambda _filename: None,
    )
    assert _Dialog.last_instance is not None

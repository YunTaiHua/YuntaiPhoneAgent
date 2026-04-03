from pathlib import Path
from types import SimpleNamespace

from yuntai.handlers.connection_handler import ConnectionHandler
from yuntai.handlers.dynamic_handler import DynamicHandler
from yuntai.handlers.system_handler import SystemHandler
from yuntai.handlers.tts_handler import TTSHandler


class _Label:
    def __init__(self, text=""):
        self._text = text
        self.style = ""

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text

    def setStyleSheet(self, style):
        self.style = style


class _ListBox:
    def __init__(self, selected=None):
        self._selected = selected or []
        self.items = []

    def clear(self):
        self.items.clear()

    def addItem(self, item):
        self.items.append(item)

    def selectedItems(self):
        return self._selected

    def row(self, item):
        return item


class _Lock:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_connection_handler_connection_type_toggle():
    calls = []
    usb = SimpleNamespace(show=lambda: calls.append("usb_show"), hide=lambda: calls.append("usb_hide"))
    wireless = SimpleNamespace(show=lambda: calls.append("wireless_show"), hide=lambda: calls.append("wireless_hide"))
    comps = {"usb_frame": usb, "wireless_frame": wireless}

    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(get_component=lambda name: comps.get(name))

    h._on_connection_type_changed(SimpleNamespace(text=lambda: "USB调试连接"))
    h._on_connection_type_changed(SimpleNamespace(text=lambda: "无线调试连接"))

    assert "wireless_hide" in calls
    assert "usb_hide" in calls


def test_tts_handler_update_audio_list_and_try_bind_paths():
    db = SimpleNamespace(tts_synthesized_files=[], tts_synthesized_files_lock=_Lock())
    box = _ListBox()
    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(components={"tts_audio_listbox": box}, get_component=lambda name: {"tts_audio_listbox": box}.get(name))
    h.task_manager = SimpleNamespace(tts_manager=db)
    h._events_bound = False
    h._events_bound_success = False
    h._bind_events = lambda: setattr(h, "_events_bound_success", True)

    files = [("/a.wav", "a.wav"), ("/b.wav", "b.wav")]
    h._on_update_audio_list(files)
    assert len(box.items) == 2
    assert db.tts_synthesized_files == files

    h._try_bind_events(0)
    assert h._events_bound is True


def test_tts_handler_select_ref_audio_auto_matches_text():
    text_label = _Label("未选择")
    audio_label = _Label("未选择")
    selected = []

    tts_manager = SimpleNamespace(
        tts_files_database={"audio": {"voice.wav": "x"}, "text": {"voice.txt": "y"}},
        set_current_model=lambda kind, name: selected.append((kind, name)) or True,
    )

    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(
        get_component=lambda name: {"tts_audio_label": audio_label, "tts_text_label": text_label}.get(name)
    )
    h.task_manager = SimpleNamespace(tts_manager=tts_manager)
    h.tts_add_log = lambda *_: None
    h._create_file_selection_popup = lambda _t, d, cb: cb(next(iter(d.keys())))

    h.tts_select_ref_audio()

    assert ("audio", "voice.wav") in selected
    assert ("text", "voice.txt") in selected
    assert text_label.text() == "voice.txt"


def test_dynamic_handler_video_error_and_preview_no_file(monkeypatch):
    logs = []
    toasts = []
    h = DynamicHandler.__new__(DynamicHandler)
    h.video_log_signal = SimpleNamespace(emit=lambda msg: logs.append(msg))
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))

    h._on_video_error("boom")
    assert logs and "boom" in logs[0]
    assert toasts and toasts[0][1] == "error"

    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.preview_latest_video()
    assert toasts[-1][1] == "warning"


def test_system_handler_start_check_thread_signal_slot(monkeypatch):
    called = []

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr("threading.Thread", _ImmediateThread)

    h = SystemHandler.__new__(SystemHandler)
    h._current_check_thread = lambda: called.append(True)
    h._on_start_check_thread()
    assert called == [True]

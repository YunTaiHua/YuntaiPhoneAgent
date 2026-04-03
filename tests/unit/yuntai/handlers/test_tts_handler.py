from pathlib import Path
from types import SimpleNamespace

import yuntai.handlers.tts_handler as tts_mod
from yuntai.handlers.tts_handler import TTSHandler


class _ListBox:
    def __init__(self, selected=None):
        self._selected = selected or []

    def selectedItems(self):
        return self._selected

    def row(self, item):
        return item


class _TextInput:
    def __init__(self, text):
        self._text = text

    def toPlainText(self):
        return self._text


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


class _Label:
    def __init__(self):
        self.value = ""

    def setText(self, value):
        self.value = value


class _Lock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self._target = target

    def start(self):
        if self._target:
            self._target()


class _Dialog:
    instances = []

    def __init__(self, *_a, **_k):
        self.accepted = 0
        self.rejected = 0
        self.__class__.instances.append(self)

    def setWindowTitle(self, *_a, **_k):
        return None

    def setFixedSize(self, *_a, **_k):
        return None

    def setModal(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def accept(self):
        self.accepted += 1

    def reject(self):
        self.rejected += 1

    def exec(self):
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


class _Frame:
    def setStyleSheet(self, *_a, **_k):
        return None


class _CheckBox:
    def __init__(self, *_a, **_k):
        self._checked = False

    def setFont(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setChecked(self, v):
        self._checked = bool(v)

    def isChecked(self):
        return self._checked


class _Combo:
    instances = []

    def __init__(self, *_a, **_k):
        self.items = []
        self.current = "未选择"
        self.__class__.instances.append(self)

    def setFont(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None

    def addItems(self, items):
        self.items.extend(list(items))
        if self.items:
            self.current = self.items[0]

    def setCurrentText(self, text):
        self.current = text

    def currentText(self):
        return self.current


class _Label2:
    def __init__(self, *_a, **_k):
        return None

    def setFont(self, *_a, **_k):
        return None

    def setAlignment(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None


class _Button2:
    instances = []

    def __init__(self, text="", *_a, **_k):
        self.text = text
        self.clicked = _Signal()
        self.__class__.instances.append(self)

    def setFont(self, *_a, **_k):
        return None

    def setFixedHeight(self, *_a, **_k):
        return None

    def setFixedWidth(self, *_a, **_k):
        return None

    def setStyleSheet(self, *_a, **_k):
        return None


def _make_handler(components=None, tts_manager=None):
    h = TTSHandler.__new__(TTSHandler)
    components = components or {}
    tts_manager = tts_manager or SimpleNamespace(
        is_playing_audio=False,
        is_tts_synthesizing=False,
        tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}},
        load_synthesized_files=lambda: [],
        get_current_model=lambda _: None,
    )
    h.view = SimpleNamespace(get_component=lambda name: components.get(name), components=components)
    h.task_manager = SimpleNamespace(
        tts_manager=tts_manager,
        tts_synthesize_text=lambda *args, **kwargs: (True, "ok.wav"),
        stop_audio_playback=lambda: True,
    )
    h._events_bound = False
    h._events_bound_success = False
    logs = []
    h.tts_add_log = lambda msg: logs.append(msg)
    h._logs = logs
    return h


def test_tts_play_selected_audio_no_selection_and_invalid_index():
    play_calls = []
    h = _make_handler({"tts_audio_listbox": _ListBox([])})
    h.task_manager.tts_manager.play_audio_file = lambda path: play_calls.append(path)
    h.tts_play_selected_audio()
    assert play_calls == []
    assert h._logs

    h = _make_handler(
        {"tts_audio_listbox": _ListBox([5])},
        SimpleNamespace(
            is_playing_audio=False,
            load_synthesized_files=lambda: [("a.wav", "a.wav")],
            play_audio_file=lambda p: None,
        ),
    )
    h.task_manager.tts_manager.play_audio_file = lambda path: play_calls.append(path)
    h.tts_play_selected_audio()
    assert play_calls == []
    assert h._logs


def test_tts_on_audio_double_click_missing_file(tmp_path):
    missing = tmp_path / "missing.wav"
    h = _make_handler(
        {"tts_audio_listbox": _ListBox()},
        SimpleNamespace(
            is_playing_audio=False,
            load_synthesized_files=lambda: [(str(missing), missing.name)],
            play_audio_file=lambda p: None,
        ),
    )

    h.tts_on_audio_double_click(0)
    assert any("不存在" in x for x in h._logs)


def test_tts_stop_audio_playback_logs_status():
    h = _make_handler()
    h.task_manager.stop_audio_playback = lambda: True
    h.tts_stop_audio_playback()
    assert any("已停止" in x for x in h._logs)

    h = _make_handler()
    h.task_manager.stop_audio_playback = lambda: False
    h.tts_stop_audio_playback()
    assert any("没有正在播放" in x for x in h._logs)


def test_tts_start_synthesis_validation_paths():
    synth_calls = []
    h = _make_handler({"tts_text_input": _TextInput("")})
    h.task_manager.tts_synthesize_text = lambda *args, **kwargs: synth_calls.append((args, kwargs)) or (True, "ok.wav")
    h.tts_start_synthesis()
    assert synth_calls == []
    assert h._logs


def test_tts_update_list_select_load_delete_and_synthesize(monkeypatch, tmp_path):
    monkeypatch.setattr(tts_mod.threading, "Thread", _ImmediateThread)

    out_dir = tmp_path / "audio_out"
    out_dir.mkdir()
    wav = out_dir / "b.wav"
    wav.write_bytes(b"x")

    listbox = _ListBox(["first"])
    listbox.row = lambda _item: 0
    logs = []
    labels = {
        "tts_gpt_label": _Label(),
        "tts_sovits_label": _Label(),
        "tts_audio_label": _Label(),
        "tts_text_label": _Label(),
    }

    tts_manager = SimpleNamespace(
        default_tts_config={"output_path": str(out_dir)},
        tts_synthesized_files_lock=_Lock(),
        tts_synthesized_files=[],
        is_playing_audio=False,
        tts_files_database={
            "gpt": {"g.pt": "g"},
            "sovits": {"s.pt": "s"},
            "audio": {"a.wav": "a"},
            "text": {"a.txt": "t"},
        },
        set_current_model=lambda kind, name: logs.append((kind, name)) or True,
        get_current_model=lambda kind: {
            "gpt": "g.pt",
            "sovits": "s.pt",
            "audio": "a.wav",
            "text": "a.txt",
        }.get(kind),
        tts_modules_loaded=True,
        tts_modules={
            "change_gpt_weights": lambda *_a: logs.append("gpt_loaded"),
            "change_sovits_weights": lambda *_a: logs.append("sovits_loaded"),
        },
        is_tts_synthesizing=False,
        load_synthesized_files=lambda: [(str(wav), wav.name)],
        play_audio_file=lambda _path: logs.append("played"),
    )

    components = {"tts_audio_listbox": listbox}
    components.update(labels)

    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(get_component=lambda name: components.get(name), components=components)
    h.task_manager = SimpleNamespace(
        tts_manager=tts_manager,
        tts_synthesize_text=lambda *_a, **_k: (True, "ok"),
    )
    h.tts_add_log = lambda msg: logs.append(msg)
    h.update_audio_list_signal = SimpleNamespace(emit=lambda files: h._on_update_audio_list(files))
    h._create_file_selection_popup = lambda _title, file_dict, cb: cb(sorted(file_dict.keys())[0])
    h.tts_update_synthesized_list = lambda: logs.append("refresh")

    h.tts_play_selected_audio()
    assert "played" in logs

    h.tts_select_gpt_model()
    h.tts_select_sovits_model()
    h.tts_select_ref_audio()
    h.tts_select_ref_text()
    assert labels["tts_gpt_label"].value == "g.pt"

    h.tts_load_selected_models()
    assert "gpt_loaded" in logs and "sovits_loaded" in logs

    h.view = SimpleNamespace(get_component=lambda name: _TextInput("hello") if name == "tts_text_input" else None, components={})
    h.tts_start_synthesis()
    assert "refresh" in logs


def test_tts_delete_audio_files_cancel_and_success(monkeypatch, tmp_path):
    monkeypatch.setattr(tts_mod.threading, "Thread", _ImmediateThread)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "a.wav").write_bytes(b"1")
    logs = []
    handler = TTSHandler.__new__(TTSHandler)
    handler.task_manager = SimpleNamespace(tts_manager=SimpleNamespace(default_tts_config={"output_path": str(out_dir)}))
    handler.tts_add_log = lambda msg: logs.append(msg)
    handler.tts_update_synthesized_list = lambda: logs.append("updated")
    handler.view = SimpleNamespace()

    monkeypatch.setattr(tts_mod, "show_confirm_dialog", lambda *_a, **_k: False)
    handler.tts_delete_audio_files()
    assert any("已取消" in x for x in logs)

    logs.clear()
    monkeypatch.setattr(tts_mod, "show_confirm_dialog", lambda *_a, **_k: True)
    handler.tts_delete_audio_files()
    assert any("已删除" in x for x in logs)
    assert "updated" in logs


def test_show_tts_settings_popup_apply_and_cancel(monkeypatch):
    monkeypatch.setattr(tts_mod, "QDialog", _Dialog)
    monkeypatch.setattr(tts_mod, "QVBoxLayout", _Layout)
    monkeypatch.setattr(tts_mod, "QHBoxLayout", _Layout)
    monkeypatch.setattr(tts_mod, "QLabel", _Label2)
    monkeypatch.setattr(tts_mod, "QCheckBox", _CheckBox)
    monkeypatch.setattr(tts_mod, "QComboBox", _Combo)
    monkeypatch.setattr(tts_mod, "QFrame", _Frame)
    monkeypatch.setattr(tts_mod, "QPushButton", _Button2)

    toasts = []
    updates = []
    set_calls = []

    tts_manager = SimpleNamespace(
        tts_enabled=True,
        tts_files_database={
            "gpt": {"g.pt": "g"},
            "sovits": {"s.pt": "s"},
            "audio": {"a.wav": "a"},
            "text": {"a.txt": "t"},
        },
        get_current_model=lambda k: {"gpt": "g.pt", "sovits": "s.pt", "audio": "a.wav"}.get(k),
        set_current_model=lambda kind, name: set_calls.append((kind, name)) or True,
    )

    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(colors=tts_mod.ThemeColors)
    h.task_manager = SimpleNamespace(tts_manager=tts_manager)
    h.controller = SimpleNamespace(
        update_tts_indicator=lambda enabled: updates.append(enabled),
        show_toast=lambda msg, level: toasts.append((msg, level)),
    )

    h.show_tts_settings_popup()

    save_btn = next(b for b in _Button2.instances if b.text == "保存设置")
    cancel_btn = next(b for b in _Button2.instances if b.text == "取消")
    save_btn.clicked.connected[0]()
    cancel_btn.clicked.connected[0]()

    assert updates
    assert set_calls
    assert any(level == "success" for _, level in toasts)

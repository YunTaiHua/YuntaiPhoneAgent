from pathlib import Path
from types import SimpleNamespace

import pytest

from yuntai.handlers.connection_handler import ConnectionHandler
from yuntai.handlers.tts_handler import TTSHandler


class _Signal:
    def __init__(self):
        self.connected = []

    def connect(self, fn):
        self.connected.append(fn)

    def disconnect(self):
        raise TypeError("no previous")

    def emit(self, *args, **kwargs):
        for fn in self.connected:
            fn(*args, **kwargs)


class _Button:
    def __init__(self):
        self.clicked = _Signal()


class _ButtonGroup:
    def __init__(self):
        self.buttonClicked = _Signal()


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self.target = target

    def start(self):
        if self.target:
            self.target()


def test_connection_bind_and_disconnect_and_detect_exception(monkeypatch):
    import yuntai.handlers.connection_handler as mod

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    components = {
        "detect_devices_btn": _Button(),
        "connect_device_btn": _Button(),
        "disconnect_device_btn": _Button(),
        "conn_button_group": _ButtonGroup(),
        "device_type_menu": None,
    }
    toasts = []
    status = []
    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(get_component=lambda name: components.get(name))
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.task_manager = SimpleNamespace(disconnect_device=lambda: status.append("disconnected"), detect_devices=lambda _t: (_ for _ in ()).throw(RuntimeError("boom")))
    h._update_connection_status_gui = lambda connected: status.append(connected)

    h._bind_events()
    assert components["detect_devices_btn"].clicked.connected
    assert components["connect_device_btn"].clicked.connected
    assert components["disconnect_device_btn"].clicked.connected
    assert components["conn_button_group"].buttonClicked.connected

    h.disconnect_device()
    assert status[:2] == ["disconnected", False]
    assert toasts[-1][1] == "info"

    calls = []

    class _Dialog:
        def __init__(self, *_args, **_kwargs):
            return None

        def show_result(self, devices, device_type, display):
            calls.append((devices, device_type, display))

        def exec(self):
            calls.append(("exec",))

    monkeypatch.setattr(mod, "DeviceDetectDialog", _Dialog)
    h._get_device_type = lambda: "android"
    h._get_device_type_display = lambda: "Android"
    h.detect_devices_gui()
    assert ([], "android", "Android") in calls
    assert any("检测设备出错" in m for m, _ in toasts)


def test_connection_connect_none_config_returns_early():
    h = ConnectionHandler.__new__(ConnectionHandler)
    h._get_connection_config_from_ui = lambda: None
    h.task_manager = SimpleNamespace(connect_device=lambda _cfg: pytest.fail("must not connect"))
    h.connect_device_gui()


def test_tts_bind_events_and_play_paths(monkeypatch, tmp_path):
    import yuntai.handlers.tts_handler as mod
    from PyQt6.QtWidgets import QWidget

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    class _ListBox:
        def __init__(self):
            self.itemDoubleClicked = _Signal()

        def selectedItems(self):
            return [0]

        def row(self, item):
            return item

    components = {
        "tts_select_gpt_btn": _Button(),
        "tts_select_sovits_btn": _Button(),
        "tts_select_audio_btn": _Button(),
        "tts_select_text_btn": _Button(),
        "tts_synth_btn": _Button(),
        "tts_load_btn": _Button(),
        "tts_stop_btn": _Button(),
        "tts_text_input": QWidget(),
        "tts_audio_listbox": _ListBox(),
        "tts_play_btn": _Button(),
        "tts_refresh_btn": _Button(),
        "tts_delete_btn": _Button(),
    }

    audio_path = tmp_path / "ok.wav"
    audio_path.write_bytes(b"ok")
    played = []
    tts_manager = SimpleNamespace(
        is_playing_audio=False,
        load_synthesized_files=lambda: [(str(audio_path), audio_path.name)],
        play_audio_file=lambda p: played.append(p),
        tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}},
    )

    logs = []
    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(get_component=lambda name: components.get(name), components=components)
    h.task_manager = SimpleNamespace(tts_manager=tts_manager)
    h.tts_add_log = lambda msg: logs.append(msg)

    h._bind_events()
    assert h._events_bound_success is True
    assert components["tts_synth_btn"].clicked.connected
    assert components["tts_audio_listbox"].itemDoubleClicked.connected

    h.tts_play_selected_audio()
    assert played == [str(audio_path)]

    logs.clear()
    h.task_manager.tts_manager.is_playing_audio = True
    h.tts_play_selected_audio()
    assert any("已有音频正在播放" in m for m in logs)


def test_tts_misc_guard_paths():
    logs = []
    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(components={}, get_component=lambda _name: None)
    h.task_manager = SimpleNamespace(
        tts_manager=SimpleNamespace(
            tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}},
            is_tts_synthesizing=True,
            get_current_model=lambda _k: None,
        )
    )
    h.tts_add_log = lambda msg: logs.append(msg)

    h._events_bound_success = True
    h._events_bound = False
    h._try_bind_events(10)
    assert h._events_bound is False

    h._events_bound_success = False
    h._bind_events()
    assert h._events_bound_success is False

    h.tts_select_gpt_model()
    h.tts_select_sovits_model()
    h.tts_select_ref_audio()
    h.tts_select_ref_text()
    h.tts_start_synthesis()

    assert any("未找到任何GPT模型" in m for m in logs)
    assert any("未找到任何SoVITS模型" in m for m in logs)
    assert any("未找到任何参考音频" in m for m in logs)
    assert any("未找到任何参考文本" in m for m in logs)
    assert any("正在合成中" in m for m in logs)

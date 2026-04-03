from types import SimpleNamespace

from yuntai.handlers.connection_handler import ConnectionHandler
from yuntai.handlers.dynamic_handler import DynamicHandler
from yuntai.handlers.system_handler import SystemHandler
from yuntai.handlers.tts_handler import TTSHandler


def test_connection_handler_simple_paths():
    components = {
        "device_type_menu": SimpleNamespace(currentText=lambda: "Android (ADB)"),
        "usb_option": SimpleNamespace(isChecked=lambda: False),
        "ip_entry": SimpleNamespace(text=lambda: "1.2.3.4"),
        "port_entry": SimpleNamespace(text=lambda: "5555"),
    }
    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(get_component=lambda name: components.get(name))
    h.controller = SimpleNamespace(show_toast=lambda *_args, **_kwargs: None)
    h.task_manager = SimpleNamespace(
        connect_device=lambda _cfg: (False, None, "bad"),
        detect_devices=lambda _t="android": ["d1"],
        disconnect_device=lambda: None,
        is_connected=False,
    )
    h.update_status_signal = SimpleNamespace(emit=lambda *_args, **_kwargs: None)

    cfg = h._get_connection_config_from_ui()
    assert cfg["connection_type"] == "wireless"
    h.disconnect_device()


def test_dynamic_handler_generate_video_missing_components_and_preview(monkeypatch):
    h = DynamicHandler.__new__(DynamicHandler)
    h.view = SimpleNamespace(get_component=lambda _name: None)
    calls = []
    h.controller = SimpleNamespace(show_toast=lambda msg, level: calls.append((msg, level)))
    h.generate_video()
    assert calls and calls[0][1] == "warning"

    h.controller = SimpleNamespace(show_toast=lambda msg, level: calls.append((msg, level)), latest_video_path="x.mp4")
    monkeypatch.setattr("webbrowser.open", lambda _u: True)
    h.preview_latest_video()


def test_system_handler_show_panels_and_bind_settings():
    comps = {f"settings_btn_{i}": SimpleNamespace(clicked=SimpleNamespace(disconnect=lambda: (_ for _ in ()).throw(TypeError()), connect=lambda _fn: None)) for i in range(4)}
    h = SystemHandler.__new__(SystemHandler)
    h.view = SimpleNamespace(
        get_component=lambda name: comps.get(name),
        create_history_page=lambda: None,
        create_settings_page=lambda: None,
        colors=SimpleNamespace(),
    )
    h.controller = SimpleNamespace(
        connection_handler=SimpleNamespace(show_panel=lambda: None),
        tts_handler=SimpleNamespace(show_panel=lambda: None),
        show_toast=lambda *_args, **_kwargs: None,
    )
    h.task_manager = SimpleNamespace(file_manager=SimpleNamespace(safe_read_json_file=lambda *_: {"sessions": [], "free_chats": []}), utils=SimpleNamespace(), tts_manager=SimpleNamespace(default_tts_config={"gpt_model_dir": "g", "sovits_model_dir": "s", "ref_audio_root": "a", "output_path": "o"}, tts_available=False, tts_files_database={"g": {}, "sovits": {}, "audio": {}, "text": {}}), is_connected=False, device_id=None, config={})
    h._bind_history_events = lambda: None
    h.load_history_data = lambda: None
    h.show_history_panel()
    h.show_settings_panel()


def test_tts_handler_selection_and_popup_paths(monkeypatch):
    tts_manager = SimpleNamespace(
        tts_files_database={"gpt": {"a": "a"}, "sovits": {"b": "b"}, "audio": {"c.wav": "c"}, "text": {"c.txt": "t"}},
        set_current_model=lambda *_args, **_kwargs: True,
        get_current_model=lambda _k: None,
        tts_modules_loaded=True,
        tts_modules={},
        is_tts_synthesizing=False,
    )
    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(get_component=lambda _name: None, components={}, colors=SimpleNamespace())
    h.task_manager = SimpleNamespace(tts_manager=tts_manager, tts_synthesize_text=lambda *_args, **_kwargs: (True, "ok"), stop_audio_playback=lambda: True)
    h.tts_add_log = lambda *_args, **_kwargs: None
    h._create_file_selection_popup = lambda _title, file_dict, cb: cb(next(iter(file_dict.keys())))

    h.tts_select_gpt_model()
    h.tts_select_sovits_model()
    h.tts_select_ref_audio()
    h.tts_select_ref_text()

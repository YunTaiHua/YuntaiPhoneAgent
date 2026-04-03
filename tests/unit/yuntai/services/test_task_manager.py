from types import SimpleNamespace

import yuntai.services.task_manager as mod
from yuntai.services.task_manager import TaskManager


def make_task_manager_stub():
    tm = object.__new__(TaskManager)
    tm.config = {}
    tm.is_connected = False
    tm.device_id = None
    tm.task_args = SimpleNamespace(device_id=None)
    tm.connection_manager = SimpleNamespace(
        save_connection_config=lambda config: None,
        connect_to_device=lambda config: (True, "dev1", "ok"),
        set_device_type=lambda dt: None,
        get_available_devices=lambda: ["d1"],
    )
    tm.tts_manager = SimpleNamespace(
        tts_enabled=False,
        load_tts_modules=lambda: (True, "ok"),
        synthesize_text=lambda text, ra, rt, auto_play=True: (True, "audio.wav"),
        play_audio_file=lambda path: None,
        stop_current_audio_playback=lambda: True,
        cleanup=lambda: None,
    )
    return tm


def test_connect_device_success_updates_state():
    tm = make_task_manager_stub()

    ok, device, msg = tm.connect_device({"connection_type": "usb", "usb_device_id": "dev1"})

    assert ok is True
    assert device == "dev1"
    assert tm.is_connected is True
    assert tm.task_args.device_id == "dev1"
    assert msg == "ok"


def test_connect_device_failure_keeps_disconnected_state():
    tm = make_task_manager_stub()
    tm.connection_manager.connect_to_device = lambda config: (False, None, "failed")

    ok, device, msg = tm.connect_device({"connection_type": "wireless"})

    assert ok is False
    assert device is None
    assert tm.is_connected is False
    assert msg == "failed"


def test_detect_disconnect_and_tts_paths():
    tm = make_task_manager_stub()

    assert tm.detect_devices("harmony") == ["d1"]

    tm.is_connected = True
    tm.device_id = "dev"
    tm.task_args.device_id = "dev"
    tm.disconnect_device()
    assert tm.is_connected is False
    assert tm.device_id is None
    assert tm.task_args.device_id is None

    assert tm.preload_tts_modules() is True
    assert tm.tts_manager.tts_enabled is True

    tm.tts_manager.load_tts_modules = lambda: (False, "no")
    assert tm.preload_tts_modules() is False
    assert tm.tts_manager.tts_enabled is False


def test_tts_wrapper_methods_and_cleanup_calls_stop(monkeypatch):
    tm = make_task_manager_stub()
    called = {"stop": 0, "cleanup": 0}

    def stop():
        called["stop"] += 1
        return True

    def cleanup():
        called["cleanup"] += 1

    tm.tts_manager.stop_current_audio_playback = stop
    tm.tts_manager.cleanup = cleanup

    ok, out = tm.tts_synthesize_text("hello", "a.wav", "a.txt", auto_play=False)
    assert (ok, out) == (True, "audio.wav")

    assert tm.stop_audio_playback() is True
    tm.cleanup()
    assert called["stop"] == 2
    assert called["cleanup"] == 1


def test_task_manager_init_and_connection_paths(monkeypatch):
    monkeypatch.setattr(mod, "Utils", lambda: SimpleNamespace(enable_windows_color=lambda: None))
    monkeypatch.setattr(
        mod,
        "ConnectionManager",
        lambda: SimpleNamespace(
            load_connection_config=lambda: {"connection_type": "usb", "usb_device_id": "u1"},
            connect_to_device=lambda _cfg: (True, "u1", "ok"),
            save_connection_config=lambda _cfg: None,
            set_device_type=lambda _dt: None,
            get_available_devices=lambda: ["u1"],
        ),
    )
    monkeypatch.setattr(mod, "FileManager", lambda: SimpleNamespace(init_file_system=lambda: None))
    monkeypatch.setattr(mod, "ZhipuAI", lambda api_key=None: object())
    monkeypatch.setattr(mod, "AgentExecutor", lambda: object())
    monkeypatch.setattr(
        mod,
        "TTSManager",
        lambda _root: SimpleNamespace(
            init_tts_files_database=lambda: True,
            tts_enabled=False,
            load_tts_modules=lambda: (True, "ok"),
            synthesize_text=lambda *_a, **_k: (True, "x.wav"),
            play_audio_file=lambda _p: None,
            stop_current_audio_playback=lambda: True,
            cleanup=lambda: None,
        ),
    )

    tm = TaskManager("/p", "/s")
    assert tm.task_args.port == "5555"
    assert tm.task_args.base_url

    tm.check_initial_connection()
    assert tm.is_connected is True
    assert tm.device_id == "u1"


def test_task_manager_try_connect_fail_and_preload_exception(monkeypatch):
    tm = make_task_manager_stub()
    tm.connection_manager.load_connection_config = lambda: {"connection_type": "wireless", "wireless_ip": "1.2.3.4"}
    tm.connection_manager.connect_to_device = lambda _cfg: (False, None, "bad")

    tm.check_initial_connection()
    assert tm.is_connected is False

    tm.tts_manager.load_tts_modules = lambda: (_ for _ in ()).throw(RuntimeError("tts"))
    assert tm.preload_tts_modules() is False


def test_task_manager_setup_and_play_wrapper():
    tm = make_task_manager_stub()
    called = []
    tm.tts_manager.play_audio_file = lambda path: called.append(path)

    tm.setup_connection()
    tm.play_audio_file("z.wav")
    assert called == ["z.wav"]


def test_tts_manager_property_bridge_fields(tmp_path):
    from yuntai.services.task_manager import TTSManager

    mgr = object.__new__(TTSManager)
    db = SimpleNamespace(
        tts_files_database={"gpt": {"a": "b"}},
        tts_synthesized_files=[("x.wav", "x")],
        tts_synthesized_files_lock=object(),
        current_gpt_model="g",
        current_sovits_model="s",
        current_ref_audio="a.wav",
        current_ref_text="a.txt",
    )
    audio_player = SimpleNamespace(is_playing_audio=True)
    engine = SimpleNamespace(tts_modules={"k": 1}, is_tts_synthesizing=True)

    mgr.database_manager = db
    mgr.audio_player = audio_player
    mgr.engine = engine

    assert mgr.tts_files_database["gpt"]["a"] == "b"
    assert mgr.tts_synthesized_files == [("x.wav", "x")]
    mgr.tts_synthesized_files = [("y.wav", "y")]
    assert db.tts_synthesized_files == [("y.wav", "y")]
    assert mgr.current_gpt_model == "g"
    assert mgr.current_sovits_model == "s"
    assert mgr.current_ref_audio == "a.wav"
    assert mgr.current_ref_text == "a.txt"
    assert mgr.tts_synthesized_files_lock is db.tts_synthesized_files_lock
    assert mgr.is_playing_audio is True
    assert mgr.tts_modules == {"k": 1}
    mgr.tts_modules = {"z": 2}
    assert engine.tts_modules == {"z": 2}
    assert mgr.is_tts_synthesizing is True
    mgr.is_tts_synthesizing = False
    assert engine.is_tts_synthesizing is False

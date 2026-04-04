import threading
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import yuntai.services.task_manager as mod
from yuntai.services.task_manager import TaskManager, TTSManager


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
        init_tts_files_database=lambda: True,
        speak_text_intelligently=lambda text: True,
        should_use_segmented_synthesis=lambda text: False,
        synthesize_long_text_serial=lambda text, ra, rt: (True, "audio.wav"),
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


class TestTTSManagerDeepBranches:
    def test_init_tts_files_database_failure(self, monkeypatch, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.config = {"gpt_model_dir": str(tmp_path)}
        mgr.database_manager = SimpleNamespace(init_tts_files_database=lambda: False)
        result = mgr.init_tts_files_database()
        assert result is False

    def test_load_tts_modules_engine_failure(self, monkeypatch, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.engine = SimpleNamespace(
            load_tts_modules=lambda: (False, "加载失败"),
            tts_modules_loaded=True,
            tts_available=True,
        )
        ok, msg = mgr.load_tts_modules()
        assert ok is False
        assert "加载失败" in msg

    def test_synthesize_text_not_connected(self, monkeypatch, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.engine = SimpleNamespace(
            is_tts_synthesizing=False,
            tts_available=False,
            tts_modules_loaded=True,
            synthesize_text=lambda *a, **k: (False, "不可用"),
        )
        ok, msg = mgr.synthesize_text("test", "a.wav", "a.txt")
        assert ok is False

    def test_synthesize_text_engine_busy(self, monkeypatch, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.engine = SimpleNamespace(
            is_tts_synthesizing=True,
            tts_available=True,
            tts_modules_loaded=True,
            synthesize_text=lambda *a, **k: (False, "TTS正忙"),
        )
        ok, msg = mgr.synthesize_text("test", "a.wav", "a.txt")
        assert ok is False

    def test_synthesize_text_success_no_auto_play(self, monkeypatch, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.engine = SimpleNamespace(
            is_tts_synthesizing=False,
            tts_available=True,
            tts_modules_loaded=True,
            synthesize_text=lambda *a, **k: (True, "out.wav"),
        )
        mgr.audio_player = SimpleNamespace(play_audio_file=lambda p: None)
        mgr.executor = SimpleNamespace(submit=lambda fn: fn())
        ok, msg = mgr.synthesize_text("test", "a.wav", "a.txt", auto_play=False)
        assert ok is True
        assert msg == "out.wav"

    def test_clean_text_for_tts(self, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.text_processor = SimpleNamespace(clean_text_for_tts=lambda t: f"cleaned_{t}")
        result = mgr._clean_text_for_tts("hello")
        assert result == "cleaned_hello"

    def test_should_use_segmented_synthesis(self, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.text_processor = SimpleNamespace(should_use_segmented_synthesis=lambda t: True)
        result = mgr.should_use_segmented_synthesis("long text")
        assert result is True

    def test_speak_text_intelligently_no_ref_audio(self, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: None if t == "audio" else "text"
        mgr.tts_enabled = True
        result = mgr.speak_text_intelligently("hello")
        assert result is False

    def test_speak_text_intelligently_no_ref_text(self, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: "audio" if t == "audio" else None
        mgr.tts_enabled = True
        result = mgr.speak_text_intelligently("hello")
        assert result is False

    def test_speak_text_intelligently_tts_disabled(self, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: "audio" if t == "audio" else "text"
        mgr.tts_enabled = False
        result = mgr.speak_text_intelligently("hello")
        assert result is False

    def test_speak_text_intelligently_with_segmented(self, tmp_path, monkeypatch):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: "audio" if t == "audio" else "text"
        mgr.tts_enabled = True
        mgr.tts_available = True
        mgr.text_processor = SimpleNamespace(
            clean_text_for_tts=lambda t: t,
            should_use_segmented_synthesis=lambda t: True,
        )
        mgr.synthesize_long_text_serial = lambda *a: (True, "audio.wav")
        mgr.audio_player = SimpleNamespace(play_audio_file=lambda p: None)
        mgr.executor = ThreadPoolExecutor(max_workers=1)
        result = mgr.speak_text_intelligently("long text")
        assert result is True

    def test_speak_text_intelligently_without_segmented(self, tmp_path, monkeypatch):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: "audio" if t == "audio" else "text"
        mgr.tts_enabled = True
        mgr.tts_available = True
        mgr.text_processor = SimpleNamespace(
            clean_text_for_tts=lambda t: t,
            should_use_segmented_synthesis=lambda t: False,
        )
        mgr.synthesize_text = lambda *a, **k: (True, "audio.wav")
        result = mgr.speak_text_intelligently("short text")
        assert result is True

    def test_speak_text_intelligently_exception(self, tmp_path):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: (_ for _ in ()).throw(RuntimeError("get model boom"))
        result = mgr.speak_text_intelligently("hello")
        assert result is False

    def test_synthesize_long_text_serial_delete_segment_exception(self, tmp_path, monkeypatch):
        mgr = object.__new__(TTSManager)
        mgr.text_processor = SimpleNamespace(
            clean_text_for_tts=lambda t: t,
            split_text_by_numbered_sections=lambda t: ["seg1", "seg2"],
        )
        mgr.engine = SimpleNamespace(
            synthesize_text_with_retry=lambda seg, ra, rt, max_retries: (True, str(tmp_path / f"{seg}.wav"))
        )
        mgr.default_tts_config = {"output_path": str(tmp_path)}
        (tmp_path / "seg1.wav").write_bytes(b"x")
        (tmp_path / "seg2.wav").write_bytes(b"x")
        mgr.audio_player = SimpleNamespace(merge_audio_segments=lambda files: str(tmp_path / "merged.wav"))

        real_unlink = Path.unlink

        def failing_unlink(self, *args, **kwargs):
            if "seg2" in str(self):
                raise OSError("delete failed")
            return real_unlink(self, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", failing_unlink)
        monkeypatch.setattr("time.sleep", lambda x: None)
        ok, result = mgr.synthesize_long_text_serial("test text", str(tmp_path / "ref.wav"), str(tmp_path / "ref.txt"))
        assert ok is True

    def test_synthesize_long_text_serial_no_merge(self, tmp_path, monkeypatch):
        mgr = object.__new__(TTSManager)
        mgr.text_processor = SimpleNamespace(
            clean_text_for_tts=lambda t: t,
            split_text_by_numbered_sections=lambda t: ["seg1", "seg2"],
        )
        mgr.engine = SimpleNamespace(
            synthesize_text_with_retry=lambda seg, ra, rt, max_retries: (True, str(tmp_path / f"{seg}.wav"))
        )
        mgr.default_tts_config = {"output_path": str(tmp_path)}
        (tmp_path / "seg1.wav").write_bytes(b"x")
        (tmp_path / "seg2.wav").write_bytes(b"x")
        mgr.audio_player = SimpleNamespace(merge_audio_segments=lambda files: None)
        monkeypatch.setattr("time.sleep", lambda x: None)
        ok, result = mgr.synthesize_long_text_serial("test text", str(tmp_path / "ref.wav"), str(tmp_path / "ref.txt"))
        assert ok is True
        # 当 merge_audio_segments 返回 None 时，会创建一个 merged 文件
        assert "merged" in str(result) or "seg1.wav" in str(result)

    def test_speak_text_intelligently_segmented_fallback(self, tmp_path, monkeypatch):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: "audio" if t == "audio" else "text"
        mgr.tts_enabled = True
        mgr.tts_available = True
        mgr.text_processor = SimpleNamespace(
            clean_text_for_tts=lambda t: t if len(t) > 5 else "",
            should_use_segmented_synthesis=lambda t: True,
        )

        def fake_synthesize(text, ra, rt, auto_play=False):
            if len(text) < 5:
                return (False, "text too short")
            return (True, "audio.wav")

        mgr.synthesize_text = fake_synthesize
        mgr.synthesize_long_text_serial = lambda *a: (_ for _ in ()).throw(RuntimeError("segmented boom"))
        mgr.audio_player = SimpleNamespace(play_audio_file=lambda p: None)
        mgr.executor = ThreadPoolExecutor(max_workers=1)
        result = mgr.speak_text_intelligently("short")
        assert result is True

    def test_speak_text_intelligently_non_segmented_exception(self, tmp_path, monkeypatch):
        mgr = object.__new__(TTSManager)
        mgr.get_current_model = lambda t: "audio" if t == "audio" else "text"
        mgr.tts_enabled = True
        mgr.tts_available = True
        mgr.text_processor = SimpleNamespace(
            clean_text_for_tts=lambda t: t,
            should_use_segmented_synthesis=lambda t: False,
        )
        mgr.synthesize_text = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("synthesize boom"))
        mgr.executor = ThreadPoolExecutor(max_workers=1)
        result = mgr.speak_text_intelligently("test text")
        assert result is True


class TestTaskManagerInitExceptions:
    def test_check_initial_connection_no_config(self, monkeypatch):
        tm = make_task_manager_stub()
        tm.connection_manager.load_connection_config = lambda: {}
        tm.check_initial_connection()
        assert tm.is_connected is False

    def test_preload_tts_modules_already_enabled(self, monkeypatch):
        tm = make_task_manager_stub()
        tm.tts_manager.tts_enabled = True
        result = tm.preload_tts_modules()
        assert result is True

    def test_set_device_type(self, monkeypatch):
        tm = make_task_manager_stub()
        calls = []
        tm.connection_manager.set_device_type = lambda dt: calls.append(dt)
        tm.set_device_type("harmony")
        assert calls == ["harmony"]


class TestTTSManagerInit:
    def test_tts_manager_init(self, monkeypatch, tmp_path):
        monkeypatch.setattr(mod, "GPT_MODEL_DIR", str(tmp_path / "gpt"))
        monkeypatch.setattr(mod, "SOVITS_MODEL_DIR", str(tmp_path / "sovits"))
        monkeypatch.setattr(mod, "REF_AUDIO_ROOT", str(tmp_path / "audio"))
        monkeypatch.setattr(mod, "REF_TEXT_ROOT", str(tmp_path / "text"))
        monkeypatch.setattr(mod, "TTS_REF_LANGUAGE", "zh")
        monkeypatch.setattr(mod, "TTS_TARGET_LANGUAGE", "zh")
        monkeypatch.setattr(mod, "TTS_OUTPUT_DIR", str(tmp_path / "output"))
        monkeypatch.setattr(mod, "BERT_MODEL_PATH", str(tmp_path / "bert"))
        monkeypatch.setattr(mod, "HUBERT_MODEL_PATH", str(tmp_path / "hubert"))
        monkeypatch.setattr(mod, "TTS_MAX_SEGMENT_LENGTH", 500)
        monkeypatch.setattr(mod, "TTSDatabaseManager", lambda cfg: SimpleNamespace())
        monkeypatch.setattr(mod, "TTSTextProcessor", lambda max_text_length: SimpleNamespace())
        monkeypatch.setattr(mod, "TTSAudioPlayer", lambda cfg: SimpleNamespace())
        monkeypatch.setattr(mod, "TTSEngine", lambda cfg, db, tp: SimpleNamespace())

        mgr = TTSManager(str(tmp_path))
        assert mgr.project_root == str(tmp_path)
        assert mgr.tts_enabled is False
        assert mgr.tts_available is False
        assert mgr.tts_modules_loaded is False


class TestTaskManagerFullInit:
    def test_task_manager_init_zhipu_exception(self, monkeypatch, tmp_path):
        monkeypatch.setattr(mod, "Utils", lambda: SimpleNamespace(enable_windows_color=lambda: None))
        monkeypatch.setattr(mod, "ConnectionManager", lambda: SimpleNamespace())
        monkeypatch.setattr(mod, "FileManager", lambda: SimpleNamespace(init_file_system=lambda: None))
        monkeypatch.setattr(mod, "ZhipuAI", lambda api_key=None: (_ for _ in ()).throw(RuntimeError("zhipu boom")))
        monkeypatch.setattr(mod, "AgentExecutor", lambda: object())
        monkeypatch.setattr(mod, "TTSManager", lambda _root: SimpleNamespace(
            init_tts_files_database=lambda: True,
            tts_enabled=False,
        ))

        try:
            TaskManager(str(tmp_path), "/scrcpy")
        except RuntimeError as e:
            assert "zhipu boom" in str(e)

    def test_task_manager_init_tts_db_exception(self, monkeypatch, tmp_path):
        monkeypatch.setattr(mod, "Utils", lambda: SimpleNamespace(enable_windows_color=lambda: None))
        monkeypatch.setattr(mod, "ConnectionManager", lambda: SimpleNamespace())
        monkeypatch.setattr(mod, "FileManager", lambda: SimpleNamespace(init_file_system=lambda: None))
        monkeypatch.setattr(mod, "ZhipuAI", lambda api_key=None: object())
        monkeypatch.setattr(mod, "AgentExecutor", lambda: object())
        monkeypatch.setattr(mod, "TTSManager", lambda _root: SimpleNamespace(
            init_tts_files_database=lambda: (_ for _ in ()).throw(RuntimeError("tts db boom")),
            tts_enabled=False,
        ))

        tm = TaskManager(str(tmp_path), "/scrcpy")
        assert tm is not None

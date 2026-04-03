from pathlib import Path
from types import SimpleNamespace

import yuntai.services.task_manager as mod
from yuntai.services.task_manager import TTSManager


def _make_tts_manager_stub(tmp_path):
    mgr = object.__new__(TTSManager)
    mgr.default_tts_config = {"output_path": str(tmp_path)}
    mgr.tts_enabled = True
    mgr.tts_available = True
    mgr.tts_modules_loaded = False
    mgr.database_manager = SimpleNamespace(
        tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}},
        tts_synthesized_files=[],
        tts_synthesized_files_lock=SimpleNamespace(),
        current_gpt_model=None,
        current_sovits_model=None,
        current_ref_audio=None,
        current_ref_text=None,
        init_tts_files_database=lambda: True,
        load_synthesized_files=lambda: [],
        set_current_model=lambda *_args, **_kwargs: True,
        get_current_model=lambda _k: None,
        get_model_filename=lambda _k: "",
    )
    mgr.audio_player = SimpleNamespace(
        is_playing_audio=False,
        play_audio_file=lambda *_args, **_kwargs: None,
        stop_current_audio_playback=lambda: True,
        cleanup=lambda: None,
        merge_audio_segments=lambda files: files[0] if files else None,
    )
    mgr.text_processor = SimpleNamespace(
        clean_text_for_tts=lambda text: text,
        should_use_segmented_synthesis=lambda text: len(text) > 20,
        split_text_by_numbered_sections=lambda text: [text[:5], text[5:10], text[10:]],
    )
    mgr.engine = SimpleNamespace(
        tts_modules=None,
        is_tts_synthesizing=False,
        tts_modules_loaded=False,
        tts_available=True,
        load_tts_modules=lambda: (True, "ok"),
        synthesize_text=lambda text, *_args, **_kwargs: (True, str(Path(tmp_path) / f"{text[:3]}.wav")),
        synthesize_text_with_retry=lambda text, *_args, **_kwargs: (True, str(Path(tmp_path) / f"{text[:3]}-r.wav")),
    )
    mgr.executor = SimpleNamespace(submit=lambda fn: fn(), shutdown=lambda wait=False: None)
    return mgr


def test_tts_manager_load_and_synthesize_paths(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)
    ok, msg = mgr.load_tts_modules()
    assert ok is True
    assert msg == "ok"

    ok2, out = mgr.synthesize_text("hello", "a.wav", "a.txt", auto_play=True)
    assert ok2 is True
    assert out.endswith("hel.wav")


def test_tts_manager_long_text_and_speak_paths(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)
    mgr.database_manager.get_current_model = lambda kind: {"audio": "a.wav", "text": "a.txt"}.get(kind)

    ok, out = mgr.synthesize_long_text_serial("012345678901234567890", "a.wav", "a.txt")
    assert ok is True
    assert out

    assert mgr.speak_text_intelligently("012345678901234567890") is True
    mgr.text_processor.should_use_segmented_synthesis = lambda _text: False
    assert mgr.speak_text_intelligently("short") is True


def test_tts_manager_cleanup_and_wrappers(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)
    assert mgr.stop_current_audio_playback() is True
    mgr.play_audio_file("x.wav")
    assert mgr.init_tts_files_database() is True
    assert mgr.load_synthesized_files() == []
    assert mgr.set_current_model("gpt", "m") is True
    assert mgr.get_current_model("gpt") is None
    assert mgr.get_model_filename("gpt") == ""
    mgr.cleanup()


def test_tts_manager_long_text_failure_and_fallback_copy(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)

    # all segments fail
    mgr.text_processor.split_text_by_numbered_sections = lambda _text: ["a", "b"]
    mgr.engine.synthesize_text_with_retry = lambda *_a, **_k: (False, "bad")
    ok, msg = mgr.synthesize_long_text_serial("abcdef", "a.wav", "a.txt")
    assert ok is False
    assert "所有分段合成失败" in msg

    # merge fails, fallback copies first segment
    seg = tmp_path / "seg.wav"
    seg.write_text("x", encoding="utf-8")
    mgr.engine.synthesize_text_with_retry = lambda *_a, **_k: (True, str(seg))
    mgr.audio_player.merge_audio_segments = lambda _files: None
    ok2, out2 = mgr.synthesize_long_text_serial("abcdef", "a.wav", "a.txt")
    assert ok2 is True
    assert str(out2).endswith(".wav")


def test_tts_manager_long_text_exception_and_single_segment_path(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)
    mgr.text_processor.clean_text_for_tts = lambda _text: (_ for _ in ()).throw(RuntimeError("boom"))
    ok, msg = mgr.synthesize_long_text_serial("abc", "a.wav", "a.txt")
    assert ok is False
    assert "分段合成失败" in msg

    mgr2 = _make_tts_manager_stub(tmp_path)
    mgr2.text_processor.split_text_by_numbered_sections = lambda _text: ["single"]
    ok2, out2 = mgr2.synthesize_long_text_serial("single", "a.wav", "a.txt")
    assert ok2 is True
    assert out2.endswith("sin.wav")


def test_tts_manager_speak_text_guard_paths(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)
    mgr.database_manager.get_current_model = lambda _kind: None
    assert mgr.speak_text_intelligently("hello") is False

    mgr.database_manager.get_current_model = lambda kind: {"audio": "a.wav", "text": "a.txt"}.get(kind)
    mgr.tts_enabled = False
    assert mgr.speak_text_intelligently("hello") is False


def test_tts_manager_speak_text_segmented_fallback_and_exception(tmp_path):
    mgr = _make_tts_manager_stub(tmp_path)
    mgr.database_manager.get_current_model = lambda kind: {"audio": "a.wav", "text": "a.txt"}.get(kind)
    mgr.tts_enabled = True
    mgr.text_processor.should_use_segmented_synthesis = lambda _text: True
    mgr.synthesize_long_text_serial = lambda *_a, **_k: (False, "bad")
    fallback_calls = []
    mgr.synthesize_text = lambda text, *_a, **_k: (fallback_calls.append(text) or True, "f.wav")
    assert mgr.speak_text_intelligently("1234567890") is True
    assert fallback_calls

    mgr2 = _make_tts_manager_stub(tmp_path)
    mgr2.database_manager.get_current_model = lambda kind: {"audio": "a.wav", "text": "a.txt"}.get(kind)
    mgr2.tts_enabled = True
    mgr2.text_processor.should_use_segmented_synthesis = lambda _text: False

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            self._target()

    orig_thread = mod.threading.Thread
    mod.threading.Thread = _ImmediateThread
    try:
        mgr2.synthesize_text = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("x"))
        assert mgr2.speak_text_intelligently("short") is True
    finally:
        mod.threading.Thread = orig_thread

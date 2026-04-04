import asyncio
import builtins
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from yuntai.processors import audio_processor as module


def test_check_ffmpeg_success_failure_missing_path_and_exception(monkeypatch, tmp_path):
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.write_text("x", encoding="utf-8")
    ap = module.AudioProcessor(ffmpeg_path=str(ffmpeg))

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=""))
    assert ap.check_ffmpeg() == (True, "")

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="bad"))
    ok, msg = ap.check_ffmpeg()
    assert ok is False and "FFmpeg 执行失败" in msg

    ap.ffmpeg_path = None
    ok2, msg2 = ap.check_ffmpeg()
    assert ok2 is False and "路径不存在" in msg2

    ap.ffmpeg_path = ffmpeg
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    ok3, msg3 = ap.check_ffmpeg()
    assert ok3 is False and "FFmpeg 检查失败" in msg3


def test_extract_audio_from_video_branches(monkeypatch, tmp_path):
    ffmpeg = tmp_path / "ffmpeg.exe"
    ffmpeg.write_text("x", encoding="utf-8")
    ap = module.AudioProcessor(ffmpeg_path=str(ffmpeg))

    monkeypatch.setattr(ap, "check_ffmpeg", lambda: (False, "no ffmpeg"))
    assert ap.extract_audio_from_video(str(tmp_path / "a.mp4")) == (False, "no ffmpeg")

    monkeypatch.setattr(ap, "check_ffmpeg", lambda: (True, ""))
    assert "视频文件不存在" in ap.extract_audio_from_video(str(tmp_path / "missing.mp4"))[1]

    video = tmp_path / "v.mp4"
    video.write_bytes(b"x")
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=b""))
    ok, out = ap.extract_audio_from_video(str(video))
    assert ok is True
    assert out.endswith("_audio.wav")

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="err".encode("utf-8")))
    ok2, msg = ap.extract_audio_from_video(str(video))
    assert ok2 is False and "音频提取失败" in msg


def test_load_whisper_model_success_import_error_and_exception(monkeypatch):
    ap = module.AudioProcessor(ffmpeg_path=None)

    class _Whisper:
        @staticmethod
        def load_model(model_size, device):
            return {"model": model_size, "device": device}

    monkeypatch.setitem(sys.modules, "whisper", _Whisper)
    assert ap.load_whisper_model("small", "cpu") == (True, "")
    assert ap.model_loaded is True
    assert ap.load_whisper_model("small", "cpu") == (True, "")

    ap2 = module.AudioProcessor(ffmpeg_path=None)
    real_import = builtins.__import__

    def _import_block_whisper(name, *args, **kwargs):
        if name == "whisper":
            raise ImportError("no whisper")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import_block_whisper)
    ok, msg = ap2.load_whisper_model()
    assert ok is False and "Whisper 库未安装" in msg

    monkeypatch.setattr(builtins, "__import__", real_import)

    ap3 = module.AudioProcessor(ffmpeg_path=None)
    class _BadWhisper:
        @staticmethod
        def load_model(*_args, **_kwargs):
            raise RuntimeError("boom")
    monkeypatch.setitem(sys.modules, "whisper", _BadWhisper)
    ok2, msg2 = ap3.load_whisper_model()
    assert ok2 is False and "加载失败" in msg2


def test_transcribe_audio_and_process_flows(monkeypatch, tmp_path):
    ap = module.AudioProcessor(ffmpeg_path=None)

    missing = ap.transcribe_audio(str(tmp_path / "missing.wav"))
    assert missing[0] is False and "不存在" in missing[1]

    audio = tmp_path / "a.wav"
    audio.write_bytes(b"x")

    monkeypatch.setattr(ap, "load_whisper_model", lambda *args, **kwargs: (True, ""))
    ap.model_loaded = True
    ap.whisper_model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: {"text": "  转录文本  "})
    monkeypatch.setattr(ap, "_convert_to_simplified_chinese", lambda t: t)
    assert ap.transcribe_audio(str(audio), "zh") == (True, "转录文本")

    ap.whisper_model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: {"text": "   "})
    ok, msg = ap.transcribe_audio(str(audio), "zh")
    assert ok is False and "结果为空" in msg

    monkeypatch.setattr(ap, "extract_audio_from_video", lambda *_args, **_kwargs: (True, str(audio)))
    monkeypatch.setattr(ap, "transcribe_audio", lambda *_args, **_kwargs: (True, "hello"))
    video = tmp_path / "v.mp4"
    video.write_bytes(b"x")
    ok2, result = ap.process_video_with_audio(str(video), prompt="p", language="zh")
    assert ok2 is True
    assert result["audio_transcription"] == "hello"

    ok3, result3 = ap.process_audio_only(str(audio), prompt="p", language="zh")
    assert ok3 is True
    assert result3["audio_language"] == "zh"


def test_convert_to_simplified_and_cleanup_temp_files(monkeypatch, tmp_path):
    ap = module.AudioProcessor(ffmpeg_path=None)

    monkeypatch.setattr(module, "WHISPER_CONVERT_TO_SIMPLIFIED", False)
    assert ap._convert_to_simplified_chinese("繁體") == "繁體"

    monkeypatch.setattr(module, "WHISPER_CONVERT_TO_SIMPLIFIED", True)

    class _OpenCCModule:
        class OpenCC:
            def __init__(self, *_args):
                pass

            def convert(self, text):
                return "简体"

    monkeypatch.setitem(sys.modules, "opencc", _OpenCCModule)
    ap.text_converter = None
    assert ap._convert_to_simplified_chinese("繁體") == "简体"

    monkeypatch.delitem(sys.modules, "opencc", raising=False)
    monkeypatch.setitem(sys.modules, "zhconv", SimpleNamespace(convert=lambda text, *_args: f"{text}-zh"))
    real_import = builtins.__import__

    def _import_no_opencc(name, *args, **kwargs):
        if name == "opencc":
            raise ImportError("no opencc")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import_no_opencc)
    ap.text_converter = None
    assert ap._convert_to_simplified_chinese("sample") == "sample-zh"

    monkeypatch.delitem(sys.modules, "zhconv", raising=False)
    def _import_no_opencc_zhconv(name, *args, **kwargs):
        if name in ("opencc", "zhconv"):
            raise ImportError("blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _import_no_opencc_zhconv)
    ap.text_converter = None
    assert ap._convert_to_simplified_chinese("sample") == "sample"

    old_file = tmp_path / "a_audio.wav"
    new_file = tmp_path / "b_extracted.wav"
    keep_file = tmp_path / "c.txt"
    old_file.write_bytes(b"x")
    new_file.write_bytes(b"x")
    keep_file.write_text("x", encoding="utf-8")
    ap.temp_dir = tmp_path

    import os
    import time as _time

    now = _time.time()
    os.utime(old_file, (now - 50 * 3600, now - 50 * 3600))
    os.utime(new_file, (now - 0.1 * 3600, now - 0.1 * 3600))

    ap.cleanup_temp_files(older_than_hours=24)
    assert old_file.exists() is False
    assert new_file.exists() is True


class TestAudioProcessorExecutorAndAsync:
    def test_get_executor_creates_thread_pool(self, monkeypatch):
        monkeypatch.setattr(module, "_executor", None)
        executor = module._get_executor()
        assert executor is not None
        assert executor._max_workers == 4

    def test_check_ffmpeg_async(self, monkeypatch, tmp_path):
        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_text("x", encoding="utf-8")
        ap = module.AudioProcessor(ffmpeg_path=str(ffmpeg))
        monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=""))
        loop = asyncio.new_event_loop()
        try:
            ok, msg = loop.run_until_complete(ap.check_ffmpeg_async())
            assert ok is True
        finally:
            loop.close()

    def test_process_video_with_audio_async(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        monkeypatch.setattr(ap, "process_video_with_audio", lambda *a, **k: (True, {"audio_path": "test"}))
        loop = asyncio.new_event_loop()
        try:
            ok, result = loop.run_until_complete(ap.process_video_with_audio_async(str(video)))
            assert ok is True
        finally:
            loop.close()

    def test_process_audio_only_async(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")
        monkeypatch.setattr(ap, "process_audio_only", lambda *a, **k: (True, {"audio_path": "test"}))
        loop = asyncio.new_event_loop()
        try:
            ok, result = loop.run_until_complete(ap.process_audio_only_async(str(audio)))
            assert ok is True
        finally:
            loop.close()


class TestAudioProcessorDeepBranches:
    def test_convert_to_simplified_chinese_has_convert_attr(self, monkeypatch):
        ap = module.AudioProcessor(ffmpeg_path=None)
        monkeypatch.setattr(module, "WHISPER_CONVERT_TO_SIMPLIFIED", True)

        class _FakeConverter:
            def convert(self, text):
                return f"converted_{text}"

        ap.text_converter = _FakeConverter()
        result = ap._convert_to_simplified_chinese("测试")
        assert result == "converted_测试"

    def test_extract_audio_with_custom_output_path(self, monkeypatch, tmp_path):
        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_text("x", encoding="utf-8")
        ap = module.AudioProcessor(ffmpeg_path=str(ffmpeg))
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        output = tmp_path / "custom_output.wav"
        monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=b""))
        ok, out = ap.extract_audio_from_video(str(video), str(output))
        assert ok is True

    def test_extract_audio_timeout(self, monkeypatch, tmp_path):
        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_text("x", encoding="utf-8")
        ap = module.AudioProcessor(ffmpeg_path=str(ffmpeg))
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        call_count = {"n": 0}

        def conditional_timeout(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return SimpleNamespace(returncode=0, stderr="")
            raise subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=1)

        monkeypatch.setattr(module.subprocess, "run", conditional_timeout)
        ok, msg = ap.extract_audio_from_video(str(video))
        assert ok is False
        assert "超时" in msg

    def test_transcribe_audio_loads_model_if_needed(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")
        ap.model_loaded = False
        monkeypatch.setattr(ap, "load_whisper_model", lambda *a, **k: (True, ""))
        ap.whisper_model = SimpleNamespace(transcribe=lambda *a, **k: {"text": "转录结果"})
        monkeypatch.setattr(ap, "_convert_to_simplified_chinese", lambda t: t)
        ok, text = ap.transcribe_audio(str(audio), "zh")
        assert ok is True

    def test_transcribe_audio_exception(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")
        ap.model_loaded = True
        ap.whisper_model = SimpleNamespace(transcribe=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("transcribe boom")))
        ok, msg = ap.transcribe_audio(str(audio), "zh")
        assert ok is False
        assert "转录失败" in msg

    def test_process_video_file_not_found(self, monkeypatch):
        ap = module.AudioProcessor(ffmpeg_path=None)
        ok, result = ap.process_video_with_audio("/nonexistent/video.mp4")
        assert ok is False
        assert "不存在" in result["error"]

    def test_process_video_audio_extract_fail(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        monkeypatch.setattr(ap, "extract_audio_from_video", lambda *a: (False, "提取失败"))
        ok, result = ap.process_video_with_audio(str(video))
        assert ok is False
        assert "音频提取失败" in result["error"]

    def test_process_video_transcribe_fail(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        monkeypatch.setattr(ap, "extract_audio_from_video", lambda *a: (True, str(tmp_path / "audio.wav")))
        monkeypatch.setattr(ap, "transcribe_audio", lambda *a, **k: (False, "转录失败"))
        ok, result = ap.process_video_with_audio(str(video))
        assert ok is False
        assert "音频转录失败" in result["error"]

    def test_process_video_exception(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        monkeypatch.setattr(ap, "extract_audio_from_video", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
        ok, result = ap.process_video_with_audio(str(video))
        assert ok is False
        assert "失败" in result["error"]

    def test_process_audio_only_file_not_found(self, monkeypatch):
        ap = module.AudioProcessor(ffmpeg_path=None)
        ok, result = ap.process_audio_only("/nonexistent/audio.wav")
        assert ok is False
        assert "不存在" in result["error"]

    def test_process_audio_only_transcribe_fail(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")
        monkeypatch.setattr(ap, "transcribe_audio", lambda *a, **k: (False, "转录失败"))
        ok, result = ap.process_audio_only(str(audio))
        assert ok is False
        assert "音频转录失败" in result["error"]

    def test_process_audio_only_exception(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")
        monkeypatch.setattr(ap, "transcribe_audio", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        ok, result = ap.process_audio_only(str(audio))
        assert ok is False
        assert "失败" in result["error"]

    def test_cleanup_temp_files_unlink_failure(self, monkeypatch, tmp_path):
        import time as _time
        ap = module.AudioProcessor(ffmpeg_path=None)
        old_file = tmp_path / "old_audio.wav"
        old_file.write_bytes(b"x")
        now = _time.time()
        os.utime(old_file, (now - 50 * 3600, now - 50 * 3600))
        ap.temp_dir = tmp_path
        real_unlink = Path.unlink

        def failing_unlink(self_path, *args, **kwargs):
            if "old_audio.wav" in str(self_path):
                raise OSError("permission denied")
            return real_unlink(self_path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", failing_unlink)
        ap.cleanup_temp_files(older_than_hours=24)
        assert old_file.exists() is True

    def test_cleanup_temp_files_outer_exception(self, monkeypatch, tmp_path):
        ap = module.AudioProcessor(ffmpeg_path=None)
        ap.temp_dir = tmp_path
        monkeypatch.setattr(tmp_path.__class__, "iterdir", lambda self: (_ for _ in ()).throw(RuntimeError("iterdir boom")))
        ap.cleanup_temp_files(older_than_hours=24)

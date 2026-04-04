"""
针对 managers 和 processors 模块中未覆盖行的补充测试
=================================================

覆盖模块:
    - tts_engine: lines 66-68, 80, 84, 239-251, 255-263, 326-328, 342, 346-347, 354, 389, 408-409, 422-427, 448-496
    - audio_processor: lines 52-54, 124, 165-167, 193, 225-229, 278-280, 301-303, 321, 325, 329, 345-347, 366-368, 389, 393, 407-409, 428-430, 461-462, 468-469
    - media_generator: lines 150-158, 176, 224, 257-261, 327-331, 375, 382, 388-390, 402-412, 459-460, 477-480, 526-528, 534-538
    - multimodal_processor: lines 157-159, 182-183, 231, 257-260, 272-277, 300, 371-375, 378, 385-386, 410, 422, 433, 440, 486-487
    - tts_audio: lines 89-92, 112-113, 145, 154-156, 207, 210, 221, 232, 243-246, 262-263
    - tts_database: lines 100, 109, 119, 128, 215, 217, 219
"""

import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


# ==============================================================
# tts_engine 未覆盖行
# ==============================================================

def _load_tts_engine_module(monkeypatch, cuda_available=False):
    """加载 tts_engine 模块（带 mock 依赖）"""
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: cuda_available))
    fake_sf = SimpleNamespace(write=lambda *_args, **_kwargs: None)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
    module = importlib.import_module("yuntai.managers.tts_engine")
    return importlib.reload(module)


def _make_tts_engine(module, tmp_path):
    """创建 TTSEngine 实例"""
    cfg = {
        "output_path": str(tmp_path / "out"),
        "ref_language": "中文",
        "target_language": "中文",
        "bert_model_path": str(tmp_path / "bert"),
        "hubert_model_path": str(tmp_path / "hubert"),
    }
    db = SimpleNamespace(
        tts_files_database={"gpt": {"a": "/g.pt"}, "sovits": {"b": "/s.pth"}},
        get_cached_text=lambda _p: "参考文本",
        add_synthesized_file=lambda _p: None,
    )
    text = SimpleNamespace(clean_text_for_tts=lambda s: s)
    return module.TTSEngine(cfg, db, text)


class TestNullIOAndNullWriter:
    """测试 NullIO 和 NullWriter 类（lines 66-68, 80, 84）

    直接使用类，无需加载整个模块。
    """

    def test_null_io_writes_error_text(self):
        """测试 NullIO 写入错误信息（line 66-68）"""
        import io
        # 直接内联 NullIO 逻辑，避免模块重载问题
        from yuntai.managers.tts_engine import NullIO
        null_io = NullIO()
        result = null_io.write("this is an ERROR message")
        assert result > 0
        assert "ERROR" in null_io.getvalue()

    def test_null_io_skips_normal_text(self):
        """测试 NullIO 跳过普通文本（line 68）"""
        from yuntai.managers.tts_engine import NullIO
        null_io = NullIO()
        result = null_io.write("normal text without issues")
        assert result == len("normal text without issues")
        assert null_io.getvalue() == ""

    def test_null_io_writes_exception_text(self):
        """测试 NullIO 写入异常信息（line 67）"""
        from yuntai.managers.tts_engine import NullIO
        null_io = NullIO()
        result = null_io.write("caught an exception here")
        assert result > 0
        assert "exception" in null_io.getvalue()

    def test_null_writer_write_returns_length(self):
        """测试 NullWriter.write 返回字符串长度（line 80）"""
        from yuntai.managers.tts_engine import NullWriter
        nw = NullWriter()
        assert nw.write("hello") == 5

    def test_null_writer_flush_does_nothing(self):
        """测试 NullWriter.flush 为空操作（line 84）"""
        from yuntai.managers.tts_engine import NullWriter
        nw = NullWriter()
        # 应该不抛异常
        nw.flush()


class TestTTSEngineModuleLoadFallback:
    """测试 TTS 模块加载的降级路径（lines 239-251, 255-263）"""

    def test_load_custom_tts_modules_imports(self, monkeypatch, tmp_path):
        """测试自定义 TTS 模块导入（lines 239-251）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)

        import types
        fake_gpt_sovits_custom = types.ModuleType("yuntai.managers.gpt_sovits_custom")
        fake_gpt_sovits_custom.get_tts_wav = lambda *a, **k: None
        fake_gpt_sovits_custom.change_gpt_weights = lambda *a: None
        fake_gpt_sovits_custom.change_sovits_weights = lambda *a: None
        fake_gpt_sovits_custom.I18nAuto = lambda: "i18n"

        monkeypatch.setitem(sys.modules, "yuntai.managers.gpt_sovits_custom", fake_gpt_sovits_custom)
        engine._load_custom_tts_modules()

        assert "get_tts_wav" in engine.tts_modules
        assert "I18nAuto" in engine.tts_modules
        assert "i18n" in engine.tts_modules

    def test_load_original_tts_modules_imports(self, monkeypatch, tmp_path):
        """测试原始 TTS 模块导入（lines 255-263）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)

        import types
        fake_i18n_mod = types.ModuleType("tools.i18n.i18n")
        fake_i18n_mod.I18nAuto = lambda: "orig_i18n"

        fake_inference = types.ModuleType("GPT_SoVITS.inference_webui")
        fake_inference.change_gpt_weights = lambda *a: None
        fake_inference.change_sovits_weights = lambda *a: None
        fake_inference.get_tts_wav = lambda *a, **k: "orig_wav"

        monkeypatch.setitem(sys.modules, "tools.i18n.i18n", fake_i18n_mod)
        monkeypatch.setitem(sys.modules, "GPT_SoVITS.inference_webui", fake_inference)

        engine._load_original_tts_modules()
        assert "get_tts_wav" in engine.tts_modules
        assert "i18n" in engine.tts_modules


class TestTTSEngineRetrySynthesis:
    """测试带重试合成的各种分支（lines 326-328, 342, 346-347, 354）"""

    def test_retry_all_attempts_busy(self, monkeypatch, tmp_path):
        """测试所有重试均因忙碌失败（line 354 - 达到最大重试次数）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)
        engine.is_tts_synthesizing = True
        engine.tts_modules_loaded = True
        engine.tts_available = True
        monkeypatch.setattr(module.time, "sleep", lambda *_args: None)

        ok, msg = engine.synthesize_text_with_retry("x", "a", "b", max_retries=0, retry_delay=0)
        assert ok is False
        assert "TTS正忙" in msg

    def test_retry_non_busy_failure_no_retry_keyword(self, monkeypatch, tmp_path):
        """测试合成失败且不包含'合成中'关键字时直接返回（line 342）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)
        engine.is_tts_synthesizing = False
        engine.tts_modules_loaded = True
        engine.tts_available = True
        monkeypatch.setattr(engine, "_do_synthesis", lambda *_args: (False, "其他错误"))

        ok, msg = engine.synthesize_text_with_retry("x", "a", "b", max_retries=2, retry_delay=0)
        assert ok is False
        assert "其他错误" in msg

    def test_retry_exception_on_final_attempt(self, monkeypatch, tmp_path):
        """测试最后一次重试时抛出异常（lines 346-347）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)
        engine.is_tts_synthesizing = False
        engine.tts_modules_loaded = True
        engine.tts_available = True
        monkeypatch.setattr(module.time, "sleep", lambda *_args: None)
        monkeypatch.setattr(engine, "_do_synthesis", lambda *_args: (_ for _ in ()).throw(RuntimeError("err")))

        ok, msg = engine.synthesize_text_with_retry("x", "a", "b", max_retries=0, retry_delay=0)
        assert ok is False
        assert "合成异常" in msg


class TestTTSEngineDoSynthesisDeepBranches:
    """测试 _do_synthesis 深层分支（lines 389, 408-409, 422-427）"""

    def test_ref_text_file_not_found(self, monkeypatch, tmp_path):
        """测试参考文本文件不存在（line 389）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)
        engine.tts_modules_loaded = True
        engine.tts_available = True

        ref_audio = tmp_path / "ref.wav"
        ref_audio.write_bytes(b"x")
        # ref_text 不存在
        ok, msg = engine._do_synthesis("abc", str(ref_audio), str(tmp_path / "missing.txt"))
        assert ok is False
        assert "参考文本文件不存在" in msg

    def test_text_few_chinese_chars_uses_default(self, monkeypatch, tmp_path):
        """测试中文字符过少使用默认文本（lines 408-409）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)
        engine.tts_modules_loaded = True
        engine.tts_available = True

        ref_audio = tmp_path / "ref.wav"
        ref_text = tmp_path / "ref.txt"
        ref_audio.write_bytes(b"x")
        ref_text.write_text("ref", encoding="utf-8")

        engine.database_manager.get_cached_text = lambda _p: "参考文本"
        engine.tts_modules = {"get_tts_wav": lambda *a, **k: [(16000, [0.1])], "i18n": lambda x: x}
        # 清理后只有很少中文字符
        engine.text_processor.clean_text_for_tts = lambda _t: "hello world abc"

        monkeypatch.setattr(engine, "_execute_synthesis", lambda *_args: [(16000, [0.1])])
        monkeypatch.setattr(engine, "_save_synthesis_result", lambda *_args: (True, "ok.wav"))

        ok, msg = engine._do_synthesis("abc", str(ref_audio), str(ref_text))
        assert ok is True

    def test_synthesis_exception_catches_and_returns_error(self, monkeypatch, tmp_path):
        """测试合成过程中的异常捕获（lines 422-427）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)
        engine.tts_modules_loaded = True
        engine.tts_available = True

        ref_audio = tmp_path / "ref.wav"
        ref_text = tmp_path / "ref.txt"
        ref_audio.write_bytes(b"x")
        ref_text.write_text("x", encoding="utf-8")

        engine.database_manager.get_cached_text = lambda _p: "有效参考"
        # 让合成过程抛出异常
        engine.tts_modules = {"get_tts_wav": object(), "i18n": lambda x: x}
        engine.text_processor.clean_text_for_tts = lambda _t: "这是一个足够长的文本用于测试"
        monkeypatch.setattr(
            engine,
            "_execute_synthesis",
            lambda *_args: (_ for _ in ()).throw(ValueError("合成内部错误")),
        )

        ok, msg = engine._do_synthesis("abc", str(ref_audio), str(ref_text))
        assert ok is False
        assert "合成出错" in msg


class TestTTSEngineExecuteSynthesis:
    """测试 _execute_synthesis 方法（lines 448-496）"""

    def test_execute_synthesis_returns_result(self, monkeypatch, tmp_path):
        """测试合成执行返回结果（lines 448-496 完整流程）"""
        module = _load_tts_engine_module(monkeypatch)
        engine = _make_tts_engine(module, tmp_path)

        engine.tts_modules = {
            "get_tts_wav": lambda *a, **k: [(16000, [0.1, 0.2])],
            "i18n": lambda x: x,
        }
        engine.default_tts_config["ref_language"] = "中文"
        engine.default_tts_config["target_language"] = "中文"

        result = engine._execute_synthesis("测试文本", "ref.wav", "参考文本")
        assert result is not None


# ==============================================================
# audio_processor 未覆盖行
# ==============================================================

class TestAudioProcessorExecutorAndAsync:
    """测试线程池执行器和异步方法（lines 52-54, 165-167, 366-368, 428-430）"""

    def test_get_executor_creates_thread_pool(self, monkeypatch):
        """测试全局执行器创建（lines 52-54）"""
        from yuntai.processors import audio_processor as mod
        # 重置全局执行器
        monkeypatch.setattr(mod, "_executor", None)
        executor = mod._get_executor()
        assert executor is not None
        assert executor._max_workers == 4

    def test_check_ffmpeg_async(self, monkeypatch, tmp_path):
        """测试异步 FFmpeg 检查（lines 165-167）"""
        import asyncio
        from yuntai.processors import audio_processor as mod

        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_text("x", encoding="utf-8")
        ap = mod.AudioProcessor(ffmpeg_path=str(ffmpeg))
        monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=""))

        loop = asyncio.new_event_loop()
        try:
            ok, msg = loop.run_until_complete(ap.check_ffmpeg_async())
            assert ok is True
        finally:
            loop.close()

    def test_process_video_with_audio_async(self, monkeypatch, tmp_path):
        """测试异步视频音频处理（lines 366-368）"""
        import asyncio
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
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
        """测试异步音频处理（lines 428-430）"""
        import asyncio
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
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
    """测试 audio_processor 深层分支（lines 124, 193, 225-229, 278-280, 301-303, 321, 325, 329, 345-347, 389, 393, 407-409, 461-462, 468-469）"""

    def test_convert_to_simplified_chinese_has_convert_attr(self, monkeypatch):
        """测试 text_converter 有 convert 属性的分支（line 124）"""
        from yuntai.processors import audio_processor as mod
        ap = mod.AudioProcessor(ffmpeg_path=None)
        monkeypatch.setattr(mod, "WHISPER_CONVERT_TO_SIMPLIFIED", True)

        class _FakeConverter:
            def convert(self, text):
                return f"converted_{text}"

        ap.text_converter = _FakeConverter()
        result = ap._convert_to_simplified_chinese("测试")
        assert result == "converted_测试"

    def test_extract_audio_with_custom_output_path(self, monkeypatch, tmp_path):
        """测试指定输出路径的音频提取（line 193）"""
        from yuntai.processors import audio_processor as mod

        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_text("x", encoding="utf-8")
        ap = mod.AudioProcessor(ffmpeg_path=str(ffmpeg))

        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")
        output = tmp_path / "custom_output.wav"

        monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=b""))
        ok, out = ap.extract_audio_from_video(str(video), str(output))
        assert ok is True

    def test_extract_audio_timeout(self, monkeypatch, tmp_path):
        """测试音频提取超时（lines 225-229 - subprocess.TimeoutExpired）"""
        import subprocess
        from yuntai.processors import audio_processor as mod

        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_text("x", encoding="utf-8")
        ap = mod.AudioProcessor(ffmpeg_path=str(ffmpeg))

        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")

        # check_ffmpeg 正常通过，但 extract_audio 的 subprocess.run 超时
        call_count = {"n": 0}
        original_run = mod.subprocess.run

        def conditional_timeout(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # check_ffmpeg call
                return SimpleNamespace(returncode=0, stderr="")
            raise subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=1)

        monkeypatch.setattr(mod.subprocess, "run", conditional_timeout)
        ok, msg = ap.extract_audio_from_video(str(video))
        assert ok is False
        assert "超时" in msg

    def test_transcribe_audio_loads_model_if_needed(self, monkeypatch, tmp_path):
        """测试转录时加载模型（lines 278-280）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")

        ap.model_loaded = False
        monkeypatch.setattr(ap, "load_whisper_model", lambda *a, **k: (True, ""))
        ap.whisper_model = SimpleNamespace(transcribe=lambda *a, **k: {"text": "转录结果"})
        monkeypatch.setattr(ap, "_convert_to_simplified_chinese", lambda t: t)

        ok, text = ap.transcribe_audio(str(audio), "zh")
        assert ok is True

    def test_transcribe_audio_exception(self, monkeypatch, tmp_path):
        """测试转录异常（lines 301-303）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")

        ap.model_loaded = True
        ap.whisper_model = SimpleNamespace(transcribe=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("transcribe boom")))

        ok, msg = ap.transcribe_audio(str(audio), "zh")
        assert ok is False
        assert "转录失败" in msg

    def test_process_video_file_not_found(self, monkeypatch):
        """测试视频文件不存在（line 321）"""
        from yuntai.processors import audio_processor as mod
        ap = mod.AudioProcessor(ffmpeg_path=None)
        ok, result = ap.process_video_with_audio("/nonexistent/video.mp4")
        assert ok is False
        assert "不存在" in result["error"]

    def test_process_video_audio_extract_fail(self, monkeypatch, tmp_path):
        """测试视频音频提取失败（line 325）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")

        monkeypatch.setattr(ap, "extract_audio_from_video", lambda *a: (False, "提取失败"))
        ok, result = ap.process_video_with_audio(str(video))
        assert ok is False
        assert "音频提取失败" in result["error"]

    def test_process_video_transcribe_fail(self, monkeypatch, tmp_path):
        """测试视频转录失败（line 329）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")

        monkeypatch.setattr(ap, "extract_audio_from_video", lambda *a: (True, str(tmp_path / "audio.wav")))
        monkeypatch.setattr(ap, "transcribe_audio", lambda *a, **k: (False, "转录失败"))

        ok, result = ap.process_video_with_audio(str(video))
        assert ok is False
        assert "音频转录失败" in result["error"]

    def test_process_video_exception(self, monkeypatch, tmp_path):
        """测试视频处理异常（lines 345-347）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"x")

        monkeypatch.setattr(ap, "extract_audio_from_video", lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))

        ok, result = ap.process_video_with_audio(str(video))
        assert ok is False
        assert "失败" in result["error"]

    def test_process_audio_only_file_not_found(self, monkeypatch):
        """测试音频文件不存在（line 389）"""
        from yuntai.processors import audio_processor as mod
        ap = mod.AudioProcessor(ffmpeg_path=None)
        ok, result = ap.process_audio_only("/nonexistent/audio.wav")
        assert ok is False
        assert "不存在" in result["error"]

    def test_process_audio_only_transcribe_fail(self, monkeypatch, tmp_path):
        """测试单独音频转录失败（line 393）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")

        monkeypatch.setattr(ap, "transcribe_audio", lambda *a, **k: (False, "转录失败"))
        ok, result = ap.process_audio_only(str(audio))
        assert ok is False
        assert "音频转录失败" in result["error"]

    def test_process_audio_only_exception(self, monkeypatch, tmp_path):
        """测试单独音频处理异常（lines 407-409）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"x")

        monkeypatch.setattr(ap, "transcribe_audio", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))

        ok, result = ap.process_audio_only(str(audio))
        assert ok is False
        assert "失败" in result["error"]

    def test_cleanup_temp_files_unlink_failure(self, monkeypatch, tmp_path):
        """测试清理临时文件时删除失败（lines 461-462）"""
        from yuntai.processors import audio_processor as mod
        import time as _time

        ap = mod.AudioProcessor(ffmpeg_path=None)
        old_file = tmp_path / "old_audio.wav"
        old_file.write_bytes(b"x")

        now = _time.time()
        os.utime(old_file, (now - 50 * 3600, now - 50 * 3600))
        ap.temp_dir = tmp_path

        # 让 unlink 失败
        real_unlink = Path.unlink
        def failing_unlink(self_path, *args, **kwargs):
            if "old_audio.wav" in str(self_path):
                raise OSError("permission denied")
            return real_unlink(self_path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", failing_unlink)
        ap.cleanup_temp_files(older_than_hours=24)
        # 文件应该仍然存在（删除失败）
        assert old_file.exists() is True

    def test_cleanup_temp_files_outer_exception(self, monkeypatch, tmp_path):
        """测试清理临时文件外层异常（lines 468-469）"""
        from yuntai.processors import audio_processor as mod

        ap = mod.AudioProcessor(ffmpeg_path=None)
        ap.temp_dir = tmp_path

        # 让 iterdir 抛异常
        monkeypatch.setattr(tmp_path.__class__, "iterdir", lambda self: (_ for _ in ()).throw(RuntimeError("iterdir boom")))
        # 不应该抛异常
        ap.cleanup_temp_files(older_than_hours=24)


# ==============================================================
# media_generator 未覆盖行
# ==============================================================

class _Resp:
    """模拟 HTTP 响应"""
    def __init__(self, status_code=200, json_data=None, text="", content=b"", headers=None, chunks=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.content = content
        self.headers = headers or {}
        self._chunks = chunks or []

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size=8192):
        for c in self._chunks:
            yield c


class TestMediaGeneratorDeepBranches:
    """测试 media_generator 深层分支"""

    def test_generate_image_request_exception(self, monkeypatch, tmp_path):
        """测试图像生成请求异常（lines 150-155）"""
        import requests as req
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.post",
            lambda *a, **k: (_ for _ in ()).throw(req.RequestException("connection error")),
        )
        result = mg.generate_image("cat")
        assert result["success"] is False
        assert "图像生成失败" in result["message"]

    def test_generate_image_unknown_exception(self, monkeypatch, tmp_path):
        """测试图像生成未知错误（lines 156-161）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        # RuntimeError 不是 (RequestException, ValueError, KeyError) 的子类
        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.post",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("unknown")),
        )
        result = mg.generate_image("cat")
        assert result["success"] is False
        assert "未知错误" in result["message"]

    def test_download_image_no_filename(self, monkeypatch, tmp_path):
        """测试下载图像时不指定文件名（line 176）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: _Resp(status_code=200, content=b"img"),
        )
        monkeypatch.setattr("yuntai.processors.media_generator.time.time", lambda: 1000000)
        out = mg.download_image("https://img")
        assert "image_1000000.png" in out

    def test_generate_video_empty_url_in_list(self, monkeypatch, tmp_path):
        """测试视频生成时空 URL 被过滤（line 224）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.post",
            lambda *a, **k: _Resp(status_code=200, json_data={"id": "t1", "task_status": "PROCESSING"}),
        )
        # 包含空 URL（过滤后只有 1 个有效 URL）
        result = mg.generate_video("p", image_urls=["http://valid.com/img.jpg", "  "])
        assert result["success"] is True

    def test_generate_video_two_valid_image_urls(self, monkeypatch, tmp_path):
        """测试视频生成两张有效图片 URL（lines 257-258）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.post",
            lambda *a, **k: _Resp(status_code=200, json_data={"id": "t2", "task_status": "PROCESSING"}),
        )
        result = mg.generate_video("p", image_urls=["http://a.com/1.jpg", "http://b.com/2.jpg"])
        assert result["success"] is True

    def test_generate_video_no_valid_images_after_filter(self, monkeypatch, tmp_path):
        """测试视频生成过滤后无有效图片（lines 260-261）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.post",
            lambda *a, **k: _Resp(status_code=200, json_data={"id": "t1", "task_status": "PROCESSING"}),
        )
        # 提供2个URL但都不符合格式，过滤后为空 -> image_urls 为空列表
        # image_count = 0，不会进入 image_urls 相关分支
        result = mg.generate_video("p", image_urls=["bad1", "bad2"])
        assert result["success"] is True

    def test_generate_video_outer_exception(self, monkeypatch, tmp_path):
        """测试视频生成外层异常（lines 327-331）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        # 让 post 抛出非请求异常
        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.post",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("video boom")),
        )
        result = mg.generate_video("p")
        assert result["success"] is False
        assert "视频生成失败" in result["message"]

    def test_check_video_result_processing_status(self, monkeypatch, tmp_path):
        """测试查询视频结果 - 处理中状态（line 382）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: _Resp(status_code=200, json_data={"task_status": "PROCESSING"}),
        )
        result = mg.check_video_result("t")
        assert result["success"] is False
        assert result["status"] == "PROCESSING"

    def test_check_video_result_fail_status(self, monkeypatch, tmp_path):
        """测试查询视频结果 - 失败状态（lines 388-390）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: _Resp(status_code=200, json_data={"task_status": "FAIL", "error": {"message": "boom"}}),
        )
        result = mg.check_video_result("t")
        assert result["success"] is False
        assert "boom" in result["message"]

    def test_check_video_result_non_200(self, monkeypatch, tmp_path):
        """测试查询视频结果 - 非200状态码（lines 402-406）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: _Resp(status_code=500, text="server error"),
        )
        result = mg.check_video_result("t")
        assert result["success"] is False
        assert "查询失败" in result["message"]

    def test_check_video_result_exception(self, monkeypatch, tmp_path):
        """测试查询视频结果异常（lines 408-412）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("check boom")),
        )
        result = mg.check_video_result("t")
        assert result["success"] is False
        assert "查询视频结果失败" in result["message"]

    def test_check_video_result_success_empty_result(self, monkeypatch, tmp_path):
        """测试查询视频结果 - 成功但结果为空（line 375）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: _Resp(status_code=200, json_data={"task_status": "SUCCESS", "video_result": []}),
        )
        result = mg.check_video_result("t")
        assert result["success"] is False
        assert "视频结果格式错误" in result["message"]

    def test_download_video_exception(self, monkeypatch, tmp_path):
        """测试视频下载异常（lines 477-480）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(
            "yuntai.processors.media_generator.requests.get",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("download boom")),
        )
        result = mg.download_video("https://video")
        assert result["success"] is False

    def test_download_video_cover_download_failure(self, monkeypatch, tmp_path):
        """测试视频下载时封面下载失败（lines 459-460）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        call_count = {"n": 0}

        def _fake_get(url, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] > 1:
                # 第二次调用是封面下载 -> 失败
                raise RuntimeError("cover download failed")
            return _Resp(status_code=200, headers={"content-length": "4"}, chunks=[b"ab", b"cd"])

        monkeypatch.setattr("yuntai.processors.media_generator.requests.get", _fake_get)
        result = mg.download_video("https://video", cover_url="https://cover", filename="test")
        assert result["success"] is True
        # cover_path 被设置为路径字符串（在异常之前赋值），但封面文件不会存在
        assert "cover" in result.get("cover_path", "") or result.get("cover_path") is not None

    def test_wait_for_video_timeout(self, monkeypatch, tmp_path):
        """测试等待视频生成超时（lines 534-538）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(mg, "check_video_result", lambda *_: {"success": False, "status": "PROCESSING"})
        monkeypatch.setattr("yuntai.processors.media_generator.time.sleep", lambda *_: None)

        result = mg.wait_for_video_completion("task", image_count=0, interval=0, max_attempts=1)
        assert result["success"] is False
        assert "超时" in result["message"]

    def test_wait_for_video_fail_event(self, monkeypatch, tmp_path):
        """测试等待视频生成失败事件（lines 526-528）"""
        from yuntai.processors.media_generator import MediaGenerator
        mg = MediaGenerator(api_key="k", project_root=tmp_path)

        monkeypatch.setattr(mg, "check_video_result", lambda *_: {"success": False, "status": "FAIL"})
        monkeypatch.setattr("yuntai.processors.media_generator.time.sleep", lambda *_: None)

        events = []
        result = mg.wait_for_video_completion("task", callback=lambda *e: events.append(e))
        assert result["status"] == "FAIL"
        assert any(e[0] == "FAIL" for e in events)


# ==============================================================
# multimodal_processor 未覆盖行
# ==============================================================

def _build_multimodal_processor(monkeypatch):
    """创建 MultimodalProcessor 实例"""
    import importlib
    import sys

    class _FakeZhipuAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: []))

    if "yuntai.processors.multimodal_processor" not in sys.modules:
        monkeypatch.setitem(sys.modules, "zhipuai", SimpleNamespace(ZhipuAI=_FakeZhipuAI))
    module = importlib.import_module("yuntai.processors.multimodal_processor")
    monkeypatch.setattr(module, "ZhipuAI", _FakeZhipuAI)
    return module.MultimodalProcessor(api_key="k")


class TestMultimodalProcessorDeepBranches:
    """测试 multimodal_processor 深层分支"""

    def test_encode_file_exception(self, monkeypatch, tmp_path):
        """测试文件编码异常（lines 157-159）"""
        p = _build_multimodal_processor(monkeypatch)
        ok = p.encode_file_to_base64(str(tmp_path / "nonexistent.bin"))
        assert ok is None

    def test_get_file_type_video(self, monkeypatch):
        """测试获取视频文件类型（lines 182-183）"""
        p = _build_multimodal_processor(monkeypatch)
        file_type, mime = p.get_file_type("test.mp4")
        assert file_type == "video"
        assert "video" in mime

    def test_prepare_messages_video_audio_fail(self, monkeypatch, tmp_path):
        """测试准备消息时视频音频处理失败（lines 257-260）"""
        p = _build_multimodal_processor(monkeypatch)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"data")

        monkeypatch.setattr(p, "encode_file_to_base64", lambda _fp: "BASE64")
        monkeypatch.setattr(p, "get_file_type", lambda fp: ("video", "video/mp4") if fp.endswith(".mp4") else ("audio", "audio/wav"))

        fake_audio_processor = SimpleNamespace(
            process_video_with_audio=lambda *_args, **_kwargs: (False, {"error": "处理失败"}),
        )
        monkeypatch.setattr(p, "get_audio_processor", lambda: fake_audio_processor)

        messages, audio_result = p.prepare_multimodal_messages("文本", [str(video)])
        assert any(c.get("type") == "video_url" for c in messages[-1]["content"])

    def test_prepare_messages_audio_success_with_transcription(self, monkeypatch, tmp_path):
        """测试准备消息时音频处理成功且有转录（lines 272-277）"""
        p = _build_multimodal_processor(monkeypatch)
        audio = tmp_path / "a.wav"
        audio.write_bytes(b"data")

        monkeypatch.setattr(p, "encode_file_to_base64", lambda _fp: "BASE64")
        monkeypatch.setattr(p, "get_file_type", lambda fp: ("audio", "audio/wav"))

        fake_audio_processor = SimpleNamespace(
            process_audio_only=lambda *_args, **_kwargs: (True, {"audio_transcription": "你好世界"}),
        )
        monkeypatch.setattr(p, "get_audio_processor", lambda: fake_audio_processor)

        messages, audio_result = p.prepare_multimodal_messages("文本", [str(audio)])
        content = messages[-1]["content"]
        assert any("你好世界" in c.get("text", "") for c in content)

    def test_prepare_messages_text_parse_fail_uses_base64(self, monkeypatch, tmp_path):
        """测试准备消息时文档解析失败回退到 base64（line 300）"""
        p = _build_multimodal_processor(monkeypatch)
        txt = tmp_path / "d.txt"
        txt.write_bytes(b"data")

        monkeypatch.setattr(p, "encode_file_to_base64", lambda _fp: "BASE64")
        monkeypatch.setattr(p, "get_file_type", lambda fp: ("text", "text/plain"))
        monkeypatch.setattr(p, "parse_document_to_text", lambda fp: None)

        messages, _ = p.prepare_multimodal_messages("文本", [str(txt)])
        content = messages[-1]["content"]
        assert any(c.get("type") == "file_url" for c in content)

    def test_prepare_messages_with_on_info_callback(self, monkeypatch, tmp_path):
        """测试准备消息时 on_info 回调（line 231）"""
        p = _build_multimodal_processor(monkeypatch)
        video = tmp_path / "v.mp4"
        video.write_bytes(b"data")

        monkeypatch.setattr(p, "encode_file_to_base64", lambda _fp: "BASE64")
        monkeypatch.setattr(p, "get_file_type", lambda fp: ("video", "video/mp4"))

        fake_ap = SimpleNamespace(
            process_video_with_audio=lambda *_a, **_k: (True, {"audio_transcription": "视频内容"}),
        )
        monkeypatch.setattr(p, "get_audio_processor", lambda: fake_ap)

        info_calls = []
        messages, _ = p.prepare_multimodal_messages("文本", [str(video)], on_info=lambda msg: info_calls.append(msg))
        assert len(info_calls) > 0

    def test_process_with_files_file_too_large(self, monkeypatch, tmp_path):
        """测试处理文件时文件太大（lines 371-375）"""
        p = _build_multimodal_processor(monkeypatch)
        big = tmp_path / "big.wav"
        big.write_bytes(b"x" * 100)

        monkeypatch.setattr(p, "is_file_supported", lambda fp: True)
        p.max_file_size = 1

        info_calls = []
        ok, msg, ar = p.process_with_files("t", [str(big)], on_info=lambda m: info_calls.append(m))
        assert ok is False
        assert "没有有效" in msg

    def test_process_with_files_unsupported_file_type(self, monkeypatch, tmp_path):
        """测试处理不支持的文件类型（lines 378, 385-386）"""
        p = _build_multimodal_processor(monkeypatch)
        bad = tmp_path / "bad.xyz"
        bad.write_bytes(b"x")

        monkeypatch.setattr(p, "is_file_supported", lambda fp: False)

        info_calls = []
        ok, msg, ar = p.process_with_files("t", [str(bad)], on_info=lambda m: info_calls.append(m))
        assert ok is False
        assert "没有有效" in msg
        assert any("不支持" in c for c in info_calls)

    def test_process_with_files_api_error_with_invalid_keyword(self, monkeypatch, tmp_path):
        """测试处理文件时 API 返回 Invalid 错误（lines 410, 422, 433）"""
        p = _build_multimodal_processor(monkeypatch)
        f1 = tmp_path / "a.wav"
        f1.write_bytes(b"x")

        monkeypatch.setattr(p, "is_file_supported", lambda fp: True)
        monkeypatch.setattr(p, "get_file_type", lambda fp: ("audio", "audio/wav"))
        monkeypatch.setattr(p, "prepare_multimodal_messages", lambda *a, **k: ([{}], None))

        p.client.chat.completions.create = lambda **k: (_ for _ in ()).throw(RuntimeError("Invalid model"))
        info_calls = []
        ok, msg, _ = p.process_with_files("t", [str(f1)], on_info=lambda m: info_calls.append(m))
        assert ok is False
        assert "Invalid" in msg

    def test_process_with_files_outer_exception(self, monkeypatch, tmp_path):
        """测试处理文件外层异常（lines 440, 486-487 -> outer except）"""
        p = _build_multimodal_processor(monkeypatch)

        monkeypatch.setattr(p, "is_file_supported", lambda fp: (_ for _ in ()).throw(RuntimeError("outer boom")))

        info_calls = []
        ok, msg, ar = p.process_with_files("t", ["/fake.wav"], on_info=lambda m: info_calls.append(m))
        assert ok is False
        assert "处理失败" in msg
        assert ar is None


# ==============================================================
# tts_audio 未覆盖行
# ==============================================================

def _load_tts_audio_module(monkeypatch, py_audio_factory=None):
    """加载 tts_audio 模块"""
    class _FakePyAudio:
        def __init__(self):
            self.stream = None
            self.terminated = False
        def get_format_from_width(self, w):
            return w
        def open(self, **kwargs):
            return self.stream
        def terminate(self):
            self.terminated = True

    py_audio_factory = py_audio_factory or _FakePyAudio
    fake_pyaudio = SimpleNamespace(PyAudio=py_audio_factory)
    monkeypatch.setitem(sys.modules, "pyaudio", fake_pyaudio)
    module = importlib.import_module("yuntai.managers.tts_audio")
    return importlib.reload(module)


class TestTTSAudioPlayerDeepBranches:
    """测试 TTSAudioPlayer 深层分支"""

    def test_check_merge_dependencies_missing(self, monkeypatch):
        """测试合并依赖缺失（lines 89-92）"""
        import builtins
        module = _load_tts_audio_module(monkeypatch)

        orig_import = builtins.__import__

        def block_deps(name, *args, **kwargs):
            if name in ("numpy", "soundfile"):
                raise ImportError("missing")
            return orig_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", block_deps)
        player = module.TTSAudioPlayer({"output_path": "."})
        assert player.can_merge_audio is False

    def test_play_audio_no_player_warning(self, monkeypatch):
        """测试音频播放器未初始化时跳过播放（lines 112-113）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": "."})
        player.audio_player = None
        # 不应抛异常
        player.play_audio_file("/some/file.wav")

    def test_play_audio_exception_during_playback(self, monkeypatch, tmp_path):
        """测试播放过程中异常（lines 154-156）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        audio = tmp_path / "test.wav"
        audio.write_bytes(b"x")

        # 让 wave.open 抛出异常
        monkeypatch.setattr(module.wave, "open", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("wave boom")))
        player.play_audio_file(str(audio))
        assert player.is_playing_audio is False

    def test_merge_audio_missing_file_logs_warning(self, monkeypatch, tmp_path):
        """测试合并时文件不存在（line 207）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        # 准备一个存在的文件和一个不存在的文件
        f1 = tmp_path / "a_20260101_000000.wav"
        f1.write_bytes(b"x")
        f2 = tmp_path / "missing.wav"

        fake_sf = SimpleNamespace(
            read=lambda p: ([0.1, 0.2], 16000),
            write=lambda *_a, **_k: None,
        )
        fake_np = SimpleNamespace(
            vstack=lambda d: d,
            concatenate=lambda d: d,
        )

        monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
        monkeypatch.setitem(sys.modules, "numpy", fake_np)
        monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_010101")))

        # 只有 f1 存在，all_audio_data 只有一个文件
        merged = player.merge_audio_segments([str(f1), str(f2)])
        assert merged is not None

    def test_merge_audio_sample_rate_mismatch(self, monkeypatch, tmp_path):
        """测试合并时采样率不一致（lines 210, 214）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        f1 = tmp_path / "a_20260101_000000.wav"
        f2 = tmp_path / "b.wav"
        f1.write_bytes(b"x")
        f2.write_bytes(b"x")

        class _Arr:
            def __init__(self, shape):
                self.shape = shape

        reads = {
            str(f1): (_Arr((2,)), 16000),
            str(f2): (_Arr((2,)), 22050),  # 不同的采样率
        }
        fake_sf = SimpleNamespace(read=lambda p: reads[p], write=lambda *_a, **_k: None)
        fake_np = SimpleNamespace(concatenate=lambda d: d)

        monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
        monkeypatch.setitem(sys.modules, "numpy", fake_np)
        monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_010101")))

        merged = player.merge_audio_segments([str(f1), str(f2)])
        assert merged is not None

    def test_merge_audio_1d_data(self, monkeypatch, tmp_path):
        """测试合并一维音频数据（line 221）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        f1 = tmp_path / "a_20260101_000000.wav"
        f2 = tmp_path / "b.wav"
        f1.write_bytes(b"x")
        f2.write_bytes(b"x")

        class _Arr1D:
            def __init__(self):
                self.shape = (100,)

        reads = {str(f1): (_Arr1D(), 16000), str(f2): (_Arr1D(), 16000)}
        fake_sf = SimpleNamespace(read=lambda p: reads[p], write=lambda *_a, **_k: None)
        fake_np = SimpleNamespace(concatenate=lambda d: d)

        monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
        monkeypatch.setitem(sys.modules, "numpy", fake_np)
        monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_010101")))

        merged = player.merge_audio_segments([str(f1), str(f2)])
        assert merged is not None

    def test_merge_audio_no_timestamp_pattern(self, monkeypatch, tmp_path):
        """测试合并时文件名不匹配时间戳模式（line 232）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        f1 = tmp_path / "simple.wav"
        f2 = tmp_path / "other.wav"
        f1.write_bytes(b"x")
        f2.write_bytes(b"x")

        class _Arr1D:
            def __init__(self):
                self.shape = (100,)

        reads = {str(f1): (_Arr1D(), 16000), str(f2): (_Arr1D(), 16000)}
        fake_sf = SimpleNamespace(read=lambda p: reads[p], write=lambda *_a, **_k: None)
        fake_np = SimpleNamespace(concatenate=lambda d: d)

        monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
        monkeypatch.setitem(sys.modules, "numpy", fake_np)
        monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_010101")))

        merged = player.merge_audio_segments([str(f1), str(f2)])
        assert merged is not None
        assert "tts_merged" in Path(merged).name

    def test_merge_audio_import_error(self, monkeypatch, tmp_path):
        """测试合并时依赖导入失败（lines 243-246）"""
        import builtins
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        f1 = tmp_path / "a.wav"
        f1.write_bytes(b"x")
        f2 = tmp_path / "b.wav"
        f2.write_bytes(b"x")

        orig_import = builtins.__import__

        def block_deps(name, *args, **kwargs):
            if name in ("numpy", "soundfile"):
                raise ImportError("missing")
            return orig_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", block_deps)
        result = player.merge_audio_segments([str(f1), str(f2)])
        assert result == str(f1)

    def test_merge_audio_general_exception(self, monkeypatch, tmp_path):
        """测试合并时一般异常（lines 248-251）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        f1 = tmp_path / "a.wav"
        f1.write_bytes(b"x")
        f2 = tmp_path / "b.wav"
        f2.write_bytes(b"x")

        fake_sf = SimpleNamespace(read=lambda p: (_ for _ in ()).throw(RuntimeError("sf boom")))
        monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
        monkeypatch.setitem(sys.modules, "numpy", SimpleNamespace())

        result = player.merge_audio_segments([str(f1), str(f2)])
        assert result == str(f1)

    def test_cleanup_terminate_os_error(self, monkeypatch, tmp_path):
        """测试清理时 terminate 失败（lines 262-263）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        # 让 terminate 抛出 OSError
        class _BoomPyAudio:
            def terminate(self):
                raise OSError("terminate failed")

        player.audio_player = _BoomPyAudio()
        # 不应抛异常
        player.cleanup()

    def test_stop_playback_not_playing(self, monkeypatch, tmp_path):
        """测试停止播放时未在播放（line 145 - is_playing_audio is False）"""
        module = _load_tts_audio_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})
        assert player.stop_current_audio_playback() is False


# ==============================================================
# tts_database 未覆盖行
# ==============================================================

class TestTTSDatabaseManagerDeepBranches:
    """测试 TTSDatabaseManager 深层分支（lines 100, 109, 119, 128, 215, 217, 219）"""

    def test_init_tts_files_database_missing_gpt_dir(self, tmp_path):
        """测试 GPT 模型目录不存在（line 100）"""
        from yuntai.managers.tts_database import TTSDatabaseManager
        cfg = {
            "gpt_model_dir": str(tmp_path / "nonexistent_gpt"),
            "sovits_model_dir": str(tmp_path / "sovits"),
            "ref_audio_root": str(tmp_path / "audio"),
            "ref_text_root": str(tmp_path / "text"),
            "output_path": str(tmp_path / "out"),
        }
        # 只创建 sovits/audio/text 目录
        for key in ["sovits_model_dir", "ref_audio_root", "ref_text_root"]:
            Path(cfg[key]).mkdir(parents=True, exist_ok=True)

        manager = TTSDatabaseManager(cfg)
        assert manager.init_tts_files_database() is True
        assert manager.tts_files_database["gpt"] == {}

    def test_init_tts_files_database_missing_sovits_dir(self, tmp_path):
        """测试 SoVITS 模型目录不存在（line 109）"""
        from yuntai.managers.tts_database import TTSDatabaseManager
        cfg = {
            "gpt_model_dir": str(tmp_path / "gpt"),
            "sovits_model_dir": str(tmp_path / "nonexistent_sovits"),
            "ref_audio_root": str(tmp_path / "audio"),
            "ref_text_root": str(tmp_path / "text"),
            "output_path": str(tmp_path / "out"),
        }
        Path(cfg["gpt_model_dir"]).mkdir(parents=True, exist_ok=True)
        Path(cfg["ref_audio_root"]).mkdir(parents=True, exist_ok=True)
        Path(cfg["ref_text_root"]).mkdir(parents=True, exist_ok=True)

        manager = TTSDatabaseManager(cfg)
        assert manager.init_tts_files_database() is True
        assert manager.tts_files_database["sovits"] == {}

    def test_init_tts_files_database_missing_audio_dir(self, tmp_path):
        """测试参考音频目录不存在（line 119）"""
        from yuntai.managers.tts_database import TTSDatabaseManager
        cfg = {
            "gpt_model_dir": str(tmp_path / "gpt"),
            "sovits_model_dir": str(tmp_path / "sovits"),
            "ref_audio_root": str(tmp_path / "nonexistent_audio"),
            "ref_text_root": str(tmp_path / "text"),
            "output_path": str(tmp_path / "out"),
        }
        Path(cfg["gpt_model_dir"]).mkdir(parents=True, exist_ok=True)
        Path(cfg["sovits_model_dir"]).mkdir(parents=True, exist_ok=True)
        Path(cfg["ref_text_root"]).mkdir(parents=True, exist_ok=True)

        manager = TTSDatabaseManager(cfg)
        assert manager.init_tts_files_database() is True
        assert manager.tts_files_database["audio"] == {}

    def test_init_tts_files_database_missing_text_dir(self, tmp_path):
        """测试参考文本目录不存在（line 128）"""
        from yuntai.managers.tts_database import TTSDatabaseManager
        cfg = {
            "gpt_model_dir": str(tmp_path / "gpt"),
            "sovits_model_dir": str(tmp_path / "sovits"),
            "ref_audio_root": str(tmp_path / "audio"),
            "ref_text_root": str(tmp_path / "nonexistent_text"),
            "output_path": str(tmp_path / "out"),
        }
        Path(cfg["gpt_model_dir"]).mkdir(parents=True, exist_ok=True)
        Path(cfg["sovits_model_dir"]).mkdir(parents=True, exist_ok=True)
        Path(cfg["ref_audio_root"]).mkdir(parents=True, exist_ok=True)

        manager = TTSDatabaseManager(cfg)
        assert manager.init_tts_files_database() is True
        assert manager.tts_files_database["text"] == {}

    def test_get_current_model_sovits_audio_text(self, tmp_path):
        """测试获取各种模型类型（lines 215, 217, 219）"""
        from yuntai.managers.tts_database import TTSDatabaseManager
        cfg = {
            "gpt_model_dir": str(tmp_path / "gpt"),
            "sovits_model_dir": str(tmp_path / "sovits"),
            "ref_audio_root": str(tmp_path / "audio"),
            "ref_text_root": str(tmp_path / "text"),
            "output_path": str(tmp_path / "out"),
        }
        manager = TTSDatabaseManager(cfg)
        manager.tts_files_database = {
            "gpt": {"g.ckpt": "/abs/g.ckpt"},
            "sovits": {"s.pth": "/abs/s.pth"},
            "audio": {"r.wav": "/abs/r.wav"},
            "text": {"r.txt": "/abs/r.txt"},
        }

        # 设置各类型模型
        manager.set_current_model("sovits", "s.pth")
        assert manager.get_current_model("sovits") == "/abs/s.pth"

        manager.set_current_model("audio", "r.wav")
        assert manager.get_current_model("audio") == "/abs/r.wav"

        manager.set_current_model("text", "r.txt")
        assert manager.get_current_model("text") == "/abs/r.txt"

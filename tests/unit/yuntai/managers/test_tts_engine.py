import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_module(monkeypatch, cuda_available=False):
    fake_torch = SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: cuda_available))
    fake_sf = SimpleNamespace(write=lambda *_args, **_kwargs: None)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
    module = importlib.import_module("yuntai.managers.tts_engine")
    return importlib.reload(module)


def _make_engine(module, tmp_path):
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


@pytest.fixture(autouse=True)
def _isolate_tts_env(monkeypatch):
    keys = [
        "TRANSFORMERS_OFFLINE",
        "HF_HUB_OFFLINE",
        "TQDM_DISABLE",
        "TOKENIZERS_PARALLELISM",
        "bert_path",
        "cnhubert_base_path",
        "gpt_path",
        "sovits_path",
        "version",
        "is_half",
        "language",
        "infer_ttswebui",
        "is_share",
        "PROGRESS_BAR",
    ]
    snapshot = {k: os.environ.get(k) for k in keys}
    for k in keys:
        monkeypatch.delenv(k, raising=False)
    yield
    for k, v in snapshot.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)


def test_load_tts_modules_success_and_custom_fallback(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    engine = _make_engine(module, tmp_path)

    monkeypatch.setattr(engine, "_load_custom_tts_modules", lambda: (_ for _ in ()).throw(RuntimeError("x")))
    called = {"original": 0}
    monkeypatch.setattr(engine, "_load_original_tts_modules", lambda: called.__setitem__("original", called["original"] + 1))

    ok, msg = engine.load_tts_modules()
    assert ok is True
    assert msg == "模块加载成功"
    assert called["original"] == 1
    assert engine.tts_modules_loaded is True
    assert engine.tts_available is True

    ok2, msg2 = engine.load_tts_modules()
    assert ok2 is True
    assert msg2 == "模块已加载"


def test_load_tts_modules_failure(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    engine = _make_engine(module, tmp_path)

    monkeypatch.setattr(engine, "_setup_environment", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    ok, msg = engine.load_tts_modules()
    assert ok is False
    assert "模块加载失败" in msg
    assert engine.tts_available is False


def test_setup_model_paths_and_tts_config(monkeypatch, tmp_path):
    module = _load_module(monkeypatch, cuda_available=True)
    engine = _make_engine(module, tmp_path)
    Path(engine.default_tts_config["bert_model_path"]).mkdir(parents=True)
    Path(engine.default_tts_config["hubert_model_path"]).mkdir(parents=True)

    engine._setup_model_paths()
    assert "bert_path" in module.os.environ
    assert "cnhubert_base_path" in module.os.environ
    assert module.os.environ["gpt_path"] == "/g.pt"
    assert module.os.environ["sovits_path"] == "/s.pth"

    engine._setup_tts_config()
    assert module.os.environ["is_half"] == "True"
    assert module.os.environ["language"] == "Auto"


def test_synthesize_text_busy_and_reset_state(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    engine = _make_engine(module, tmp_path)
    engine.is_tts_synthesizing = True

    ok, msg = engine.synthesize_text("x", "a.wav", "b.txt")
    assert ok is False
    assert "正在合成中" in msg

    engine.is_tts_synthesizing = False
    monkeypatch.setattr(engine, "_do_synthesis", lambda *_args: (True, "ok.wav"))
    ok2, msg2 = engine.synthesize_text("x", "a.wav", "b.txt")
    assert ok2 is True
    assert msg2 == "ok.wav"
    assert engine.is_tts_synthesizing is False


def test_synthesize_text_with_retry_branches(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    engine = _make_engine(module, tmp_path)

    engine.is_tts_synthesizing = True
    monkeypatch.setattr(module.time, "sleep", lambda *_args: None)
    ok, msg = engine.synthesize_text_with_retry("x", "a", "b", max_retries=0, retry_delay=0)
    assert ok is False
    assert "TTS正忙" in msg

    engine.is_tts_synthesizing = False
    seq = iter([(False, "合成中"), (True, "done.wav")])
    monkeypatch.setattr(engine, "_do_synthesis", lambda *_args: next(seq))
    ok2, msg2 = engine.synthesize_text_with_retry("x", "a", "b", max_retries=2, retry_delay=0)
    assert ok2 is True
    assert msg2 == "done.wav"

    monkeypatch.setattr(engine, "_do_synthesis", lambda *_args: (_ for _ in ()).throw(RuntimeError("err")))
    ok3, msg3 = engine.synthesize_text_with_retry("x", "a", "b", max_retries=0, retry_delay=0)
    assert ok3 is False
    assert "合成异常" in msg3


def test_do_synthesis_error_and_fallback_paths(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    engine = _make_engine(module, tmp_path)

    engine.tts_modules_loaded = False
    monkeypatch.setattr(engine, "load_tts_modules", lambda: (False, "load failed"))
    assert engine._do_synthesis("abc", "a.wav", "b.txt") == (False, "load failed")

    engine.tts_modules_loaded = True
    engine.tts_available = False
    assert engine._do_synthesis("abc", "a.wav", "b.txt") == (False, "TTS模块不可用")

    engine.tts_available = True
    assert "参考音频文件不存在" in engine._do_synthesis("abc", "no.wav", "no.txt")[1]

    ref_audio = tmp_path / "ref.wav"
    ref_text = tmp_path / "ref.txt"
    ref_audio.write_bytes(b"x")
    ref_text.write_text("x", encoding="utf-8")

    engine.database_manager.get_cached_text = lambda _p: ""
    assert engine._do_synthesis("abc", str(ref_audio), str(ref_text)) == (False, "参考文本内容为空")

    engine.database_manager.get_cached_text = lambda _p: "有效参考"
    engine.tts_modules = {}
    assert engine._do_synthesis("abc", str(ref_audio), str(ref_text)) == (False, "TTS合成函数未初始化")

    engine.tts_modules = {"get_tts_wav": object(), "i18n": lambda x: x}
    engine.text_processor.clean_text_for_tts = lambda _t: "a"
    monkeypatch.setattr(engine, "_execute_synthesis", lambda cleaned, *_args: [(16000, [0.1])] if "你好" in cleaned else [])
    monkeypatch.setattr(engine, "_save_synthesis_result", lambda *_args: (True, "ok.wav"))
    assert engine._do_synthesis("abc", str(ref_audio), str(ref_text)) == (True, "ok.wav")

    monkeypatch.setattr(engine, "_execute_synthesis", lambda *_args: None)
    assert engine._do_synthesis("abc", str(ref_audio), str(ref_text)) == (False, "合成失败：无音频数据返回")


def test_save_synthesis_result_branches(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    engine = _make_engine(module, tmp_path)

    ok, msg = engine._save_synthesis_result([], "ref.wav")
    assert ok is False
    assert "无音频数据返回" in msg

    writes = []
    monkeypatch.setattr(module.sf, "write", lambda *args, **kwargs: writes.append((args, kwargs)))
    monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_020202")))
    added = []
    engine.database_manager.add_synthesized_file = lambda p: added.append(p)

    ok2, out = engine._save_synthesis_result([(16000, [0.1]), (24000, [0.2])], "ref.wav")
    assert ok2 is True
    assert out.endswith("ref_20260101_020202.wav")
    assert writes
    assert added and added[0].endswith(".wav")

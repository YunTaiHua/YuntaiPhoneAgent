import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace


class _FakeZhipuAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: []))


def _build_processor(monkeypatch):
    if "yuntai.processors.multimodal_processor" not in sys.modules:
        monkeypatch.setitem(sys.modules, "zhipuai", SimpleNamespace(ZhipuAI=_FakeZhipuAI))
    module = importlib.import_module("yuntai.processors.multimodal_processor")
    monkeypatch.setattr(module, "ZhipuAI", _FakeZhipuAI)
    return module.MultimodalProcessor(api_key="k")


def test_encode_file_and_file_type_helpers(monkeypatch, tmp_path):
    p = _build_processor(monkeypatch)

    audio = tmp_path / "a.wav"
    audio.write_bytes(b"123")
    img = tmp_path / "a.jpg"
    img.write_bytes(b"123")
    txt = tmp_path / "a.txt"
    txt.write_text("x", encoding="utf-8")
    other = tmp_path / "a.bin"
    other.write_bytes(b"123")

    assert p.encode_file_to_base64(str(audio))
    p.max_file_size = 1
    assert p.encode_file_to_base64(str(audio)) is None

    p.max_file_size = 10_000
    assert p.get_file_type(str(audio))[0] == "audio"
    assert p.get_file_type(str(img))[0] == "image"
    assert p.get_file_type(str(txt))[0] == "text"
    assert p.get_file_type(str(other))[0] == "file"


def test_prepare_multimodal_messages_video_audio_text_and_fallback(monkeypatch, tmp_path):
    p = _build_processor(monkeypatch)

    video = tmp_path / "v.mp4"
    audio = tmp_path / "a.wav"
    txt = tmp_path / "d.txt"
    img = tmp_path / "i.jpg"
    binf = tmp_path / "x.bin"
    for f in [video, audio, txt, img, binf]:
        f.write_bytes(b"data")

    monkeypatch.setattr(p, "encode_file_to_base64", lambda _fp: "BASE64")
    monkeypatch.setattr(
        p,
        "get_file_type",
        lambda fp: (
            "video" if fp.endswith(".mp4") else
            "audio" if fp.endswith(".wav") else
            "text" if fp.endswith(".txt") else
            "image" if fp.endswith(".jpg") else
            "file",
            "application/octet-stream",
        ),
    )
    monkeypatch.setattr(p, "parse_document_to_text", lambda fp: "文档内容" if fp.endswith(".txt") else None)

    fake_audio_processor = SimpleNamespace(
        process_video_with_audio=lambda *_args, **_kwargs: (True, {"audio_transcription": "视频转录"}),
        process_audio_only=lambda *_args, **_kwargs: (False, {"error": "audio fail"}),
        cleanup_temp_files=lambda **_kwargs: None,
    )
    monkeypatch.setattr(p, "get_audio_processor", lambda: fake_audio_processor)

    messages, audio_result = p.prepare_multimodal_messages(
        "用户文本",
        [str(video), str(audio), str(txt), str(img), str(binf)],
        history=[{"role": "assistant", "content": "hi"}],
    )

    assert len(messages) == 2
    user_content = messages[-1]["content"]
    assert any(c.get("type") == "video_url" for c in user_content)
    assert any(c.get("type") == "image_url" for c in user_content)
    assert any(c.get("type") == "file_url" for c in user_content)
    assert any(c.get("type") == "text" and "文档内容" in c.get("text", "") for c in user_content)
    assert any(c.get("type") == "text" and "用户文本" in c.get("text", "") for c in user_content)
    assert audio_result is not None


def test_process_with_files_success_api_error_and_outer_error(monkeypatch, tmp_path):
    p = _build_processor(monkeypatch)

    f1 = tmp_path / "a.wav"
    f1.write_bytes(b"x")
    f2 = tmp_path / "b.unsupported"
    f2.write_bytes(b"x")

    monkeypatch.setattr(p, "is_file_supported", lambda fp: fp.endswith(".wav"))
    monkeypatch.setattr(p, "get_file_type", lambda _fp: ("audio", "audio/wav"))
    monkeypatch.setattr(p, "prepare_multimodal_messages", lambda *args, **kwargs: ([{"role": "user", "content": []}], {"audio": 1}))

    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="你"))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="好"))]),
    ]
    p.client.chat.completions.create = lambda **kwargs: chunks

    fake_audio_processor = SimpleNamespace(cleanup_temp_files=lambda **_kwargs: None)
    p.audio_processor = fake_audio_processor
    monkeypatch.setattr(p, "get_audio_processor", lambda: fake_audio_processor)

    ok, text, audio_result = p.process_with_files("t", [str(f1), str(f2)], history=[])
    assert ok is True
    assert text == "你好"
    assert audio_result == {"audio": 1}

    p.client.chat.completions.create = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("Invalid file"))
    ok2, msg2, _ = p.process_with_files("t", [str(f1)], history=[])
    assert ok2 is False
    assert "API调用失败" in msg2
    assert "a.wav" in msg2

    monkeypatch.setattr(p, "is_file_supported", lambda _fp: (_ for _ in ()).throw(RuntimeError("boom")))
    ok3, msg3, ar3 = p.process_with_files("t", [str(f1)], history=[])
    assert ok3 is False
    assert "处理失败" in msg3
    assert ar3 is None


def test_support_checks_and_api_connection(monkeypatch, tmp_path):
    p = _build_processor(monkeypatch)
    good = tmp_path / "a.jpg"
    bad = tmp_path / "a.xyz"
    good.write_bytes(b"x")
    bad.write_bytes(b"x")

    assert p.is_file_supported(str(good)) is True
    assert p.is_file_supported(str(bad)) is False
    assert p.is_file_supported(str(tmp_path / "missing.jpg")) is False

    ok_size, msg = p.check_file_size(str(good))
    assert ok_size is True and msg == ""

    p.max_file_size = 0
    ok_size2, msg2 = p.check_file_size(str(good))
    assert ok_size2 is False
    assert "限制" in msg2

    stream = [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="ok"))])]
    p.client.chat.completions.create = lambda **kwargs: stream
    assert p.test_api_connection() is True

    p.client.chat.completions.create = lambda **kwargs: []
    assert p.test_api_connection() is False

    p.client.chat.completions.create = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("x"))
    assert p.test_api_connection() is False


def test_parse_document_audio_processor_cache_and_no_valid_files(monkeypatch, tmp_path):
    p = _build_processor(monkeypatch)

    class _FakeMarkDown:
        def convert(self, _path):
            return SimpleNamespace(text_content="x" * 12000)

    monkeypatch.setitem(sys.modules, "markitdown", SimpleNamespace(MarkItDown=lambda: _FakeMarkDown()))
    doc = tmp_path / "doc.txt"
    doc.write_text("content", encoding="utf-8")
    parsed = p.parse_document_to_text(str(doc))
    assert parsed and "已截断" in parsed

    monkeypatch.setitem(sys.modules, "markitdown", SimpleNamespace(MarkItDown=lambda: (_ for _ in ()).throw(RuntimeError("boom"))))
    if hasattr(p, "_markitdown"):
        delattr(p, "_markitdown")
    assert p.parse_document_to_text(str(doc)) is None

    fake_audio_module = SimpleNamespace(AudioProcessor=lambda ffmpeg_path: SimpleNamespace(ffmpeg_path=ffmpeg_path))
    monkeypatch.setitem(sys.modules, "yuntai.processors.audio_processor", fake_audio_module)
    a1 = p.get_audio_processor()
    a2 = p.get_audio_processor()
    assert a1 is a2

    bad = tmp_path / "bad.xyz"
    bad.write_bytes(b"x")
    ok, msg, ar = p.process_with_files("t", [str(bad)], history=[])
    assert ok is False and "没有有效" in msg and ar is None

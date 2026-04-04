import importlib
import sys
from pathlib import Path
from types import SimpleNamespace


class _FakeStream:
    def __init__(self):
        self.writes = []
        self.stopped = False
        self.closed = False

    def write(self, data):
        self.writes.append(data)

    def stop_stream(self):
        self.stopped = True

    def close(self):
        self.closed = True


class _FakePyAudio:
    def __init__(self):
        self.stream = _FakeStream()
        self.terminated = False

    def get_format_from_width(self, width):
        return width

    def open(self, **kwargs):
        return self.stream

    def terminate(self):
        self.terminated = True


def _load_module(monkeypatch, py_audio_factory=None):
    py_audio_factory = py_audio_factory or _FakePyAudio
    fake_pyaudio = SimpleNamespace(PyAudio=py_audio_factory)
    monkeypatch.setitem(sys.modules, "pyaudio", fake_pyaudio)
    module = importlib.import_module("yuntai.managers.tts_audio")
    return importlib.reload(module)


def test_init_fallback_when_pyaudio_init_fails(monkeypatch):
    class _BoomPyAudio:
        def __init__(self):
            raise RuntimeError("boom")

    module = _load_module(monkeypatch, _BoomPyAudio)
    player = module.TTSAudioPlayer({"output_path": "."})
    assert player.audio_player is None


def test_play_audio_file_handles_missing_file_and_busy_state(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

    player.play_audio_file(str(tmp_path / "missing.wav"))
    assert player.is_playing_audio is False

    player.is_playing_audio = True
    player.play_audio_file(str(tmp_path / "any.wav"))
    assert player.is_playing_audio is True


def test_play_audio_file_happy_path_and_stop_playback(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

    audio_file = tmp_path / "ok.wav"
    audio_file.write_bytes(b"x")

    class _FakeWaveRead:
        def __init__(self):
            self._chunks = [b"a", b"b", b""]

        def getsampwidth(self):
            return 2

        def getnchannels(self):
            return 1

        def getframerate(self):
            return 16000

        def readframes(self, _chunk):
            return self._chunks.pop(0)

        def close(self):
            return None

    monkeypatch.setattr(module.wave, "open", lambda *_args, **_kwargs: _FakeWaveRead())

    player.play_audio_file(str(audio_file))

    stream = player.audio_player.stream
    assert stream.writes == [b"a", b"b"]
    assert stream.stopped is True
    assert stream.closed is True
    assert player.stop_current_audio_playback() is False


def test_merge_audio_segments_branches(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

    assert player.merge_audio_segments([]) is None
    assert player.merge_audio_segments(["one.wav"]) == "one.wav"

    f1 = tmp_path / "a_20260101_000000.wav"
    f2 = tmp_path / "b.wav"
    f1.write_bytes(b"x")
    f2.write_bytes(b"x")

    class _FakeArray:
        def __init__(self, shape):
            self.shape = shape

    reads = {
        str(f1): (_FakeArray((2, 2)), 16000),
        str(f2): (_FakeArray((2, 2)), 22050),
    }

    fake_sf = SimpleNamespace(
        read=lambda p: reads[p],
        write=lambda *_args, **_kwargs: None,
    )
    fake_np = SimpleNamespace(
        vstack=lambda data: data,
        concatenate=lambda data: data,
    )

    monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
    monkeypatch.setitem(sys.modules, "numpy", fake_np)
    monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_010101")))

    merged = player.merge_audio_segments([str(f1), str(f2)])
    assert merged is not None
    assert Path(merged).name.startswith("a_merged_20260101_010101")

    monkeypatch.delitem(sys.modules, "soundfile", raising=False)
    monkeypatch.delitem(sys.modules, "numpy", raising=False)
    fallback = player.merge_audio_segments([str(f1), str(f2)])
    assert fallback == str(f1)


def test_cleanup_terminates_audio_player(monkeypatch, tmp_path):
    module = _load_module(monkeypatch)
    player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

    player.is_playing_audio = True
    player.cleanup()

    assert player.audio_player.terminated is True


class TestTTSAudioPlayerDeepBranches:
    def test_check_merge_dependencies_missing(self, monkeypatch):
        import builtins
        module = _load_module(monkeypatch)
        orig_import = builtins.__import__

        def block_deps(name, *args, **kwargs):
            if name in ("numpy", "soundfile"):
                raise ImportError("missing")
            return orig_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", block_deps)
        player = module.TTSAudioPlayer({"output_path": "."})
        assert player.can_merge_audio is False

    def test_play_audio_no_player_warning(self, monkeypatch):
        module = _load_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": "."})
        player.audio_player = None
        player.play_audio_file("/some/file.wav")

    def test_play_audio_exception_during_playback(self, monkeypatch, tmp_path):
        module = _load_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"x")
        monkeypatch.setattr(module.wave, "open", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("wave boom")))
        player.play_audio_file(str(audio))
        assert player.is_playing_audio is False

    def test_merge_audio_missing_file_logs_warning(self, monkeypatch, tmp_path):
        module = _load_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})
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
        merged = player.merge_audio_segments([str(f1), str(f2)])
        assert merged is not None

    def test_merge_audio_sample_rate_mismatch(self, monkeypatch, tmp_path):
        module = _load_module(monkeypatch)
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
            str(f2): (_Arr((2,)), 22050),
        }
        fake_sf = SimpleNamespace(read=lambda p: reads[p], write=lambda *_a, **_k: None)
        fake_np = SimpleNamespace(concatenate=lambda d: d)
        monkeypatch.setitem(sys.modules, "soundfile", fake_sf)
        monkeypatch.setitem(sys.modules, "numpy", fake_np)
        monkeypatch.setattr(module.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda _f: "20260101_010101")))
        merged = player.merge_audio_segments([str(f1), str(f2)])
        assert merged is not None

    def test_merge_audio_1d_data(self, monkeypatch, tmp_path):
        module = _load_module(monkeypatch)
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
        module = _load_module(monkeypatch)
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
        import builtins
        module = _load_module(monkeypatch)
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
        module = _load_module(monkeypatch)
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
        module = _load_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})

        class _BoomPyAudio:
            def terminate(self):
                raise OSError("terminate failed")

        player.audio_player = _BoomPyAudio()
        player.cleanup()

    def test_stop_playback_not_playing(self, monkeypatch, tmp_path):
        module = _load_module(monkeypatch)
        player = module.TTSAudioPlayer({"output_path": str(tmp_path)})
        assert player.stop_current_audio_playback() is False

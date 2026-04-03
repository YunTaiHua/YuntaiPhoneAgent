from types import SimpleNamespace

import yuntai.gui.controller.tts_integration as mod


class _Sig:
    def __init__(self):
        self.events = []

    def emit(self, *args):
        self.events.append(args)


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self.target = target

    def start(self):
        if self.target:
            self.target()


class _Obj(mod.TTSIntegrationMixin):
    pass


def _make_obj(tts_manager):
    o = _Obj()
    o.task_manager = SimpleNamespace(
        preload_tts_modules=lambda: True,
        tts_manager=tts_manager,
    )
    o._show_tts_loading_signal = _Sig()
    o._update_tts_indicator_signal = _Sig()
    o._hide_tts_loading_signal = _Sig()
    o._synthesize_welcome_message_called = 0
    o._synthesize_welcome_message = lambda: setattr(o, "_synthesize_welcome_message_called", o._synthesize_welcome_message_called + 1)
    return o


def test_preload_tts_modules_success(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    tts = SimpleNamespace()
    o = _make_obj(tts)
    o.preload_tts_modules()
    assert o._show_tts_loading_signal.events
    assert o._update_tts_indicator_signal.events[-1] == (True,)
    assert o._synthesize_welcome_message_called == 1


def test_preload_tts_modules_failure(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    o = _Obj()
    o.task_manager = SimpleNamespace(preload_tts_modules=lambda: False, tts_manager=SimpleNamespace())
    o._show_tts_loading_signal = _Sig()
    o._update_tts_indicator_signal = _Sig()
    o._hide_tts_loading_signal = _Sig()
    o._synthesize_welcome_message = lambda: None
    o.preload_tts_modules()
    assert o._update_tts_indicator_signal.events[-1] == (False,)
    assert o._hide_tts_loading_signal.events


def test_wait_audio_then_hide(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(mod.time, "sleep", lambda _s: None)
    tts = SimpleNamespace(is_playing_audio=False)
    o = _Obj()
    o.task_manager = SimpleNamespace(tts_manager=tts)
    o._hide_tts_loading_signal = _Sig()
    o._wait_audio_then_hide()
    assert o._hide_tts_loading_signal.events

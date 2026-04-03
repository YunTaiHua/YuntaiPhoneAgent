from types import SimpleNamespace

from yuntai.gui.view.toast_widget import ToastWidget


class _Anim:
    def __init__(self):
        self.start_value = None
        self.end_value = None
        self.started = False

    def setStartValue(self, value):
        self.start_value = value

    def setEndValue(self, value):
        self.end_value = value

    def start(self):
        self.started = True


class _Timer:
    def __init__(self):
        self.stopped = False
        self.started_with = None

    def stop(self):
        self.stopped = True

    def start(self, duration):
        self.started_with = duration


class _Rect:
    def width(self):
        return 1000

    def height(self):
        return 700


class _Parent:
    def rect(self):
        return _Rect()


def _make_toast_with_stubs():
    toast = ToastWidget.__new__(ToastWidget)
    toast.is_dark_theme = False
    toast._is_showing = False
    toast._pending_messages = []
    toast.message_label = SimpleNamespace(
        setText=lambda _v: None,
        setStyleSheet=lambda _v: None,
    )
    toast.setStyleSheet = lambda _v: None
    toast.adjustSize = lambda: None
    toast.width = lambda: 220
    toast.height = lambda: 48
    toast.y = lambda: 111
    toast.move = lambda *_args: None
    toast.show = lambda: None
    toast.hide = lambda: None
    toast.parent = lambda: _Parent()
    toast.show_animation = _Anim()
    toast.hide_animation = _Anim()
    toast.hide_timer = _Timer()
    return toast


def test_toast_style_and_show_hide_paths():
    toast = _make_toast_with_stubs()

    toast._update_style("success")
    toast.is_dark_theme = True
    toast._update_style("error")

    toast._show_message("hello", "info", 1234)
    assert toast.show_animation.started is True
    assert toast.hide_timer.started_with == 1234

    toast._start_hide_animation()
    assert toast.hide_animation.started is True

    toast._on_hide_finished()
    assert toast._is_showing is False


def test_toast_show_toast_force_replaces_current_message():
    toast = _make_toast_with_stubs()
    calls = []
    toast._show_message = lambda message, msg_type, duration: calls.append((message, msg_type, duration))

    toast._is_showing = False
    toast.show_toast("first", "info", 100)
    assert calls == [("first", "info", 100)]

    toast._is_showing = True
    toast._force_hide_and_show_new = lambda m, t, d: calls.append(("force", m, t, d))
    toast.show_toast("second", "warning", 200)
    assert toast.hide_timer.stopped is True
    assert calls[-1] == ("force", "second", "warning", 200)

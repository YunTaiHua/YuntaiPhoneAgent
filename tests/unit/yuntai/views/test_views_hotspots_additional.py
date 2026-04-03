from types import SimpleNamespace
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from yuntai.views.connection import ConnectionBuilder
from yuntai.views.dashboard import CommandTextEdit, DashboardBuilder
from yuntai.views.dynamic import DynamicBuilder
from yuntai.views.pages import PageBuilder
from yuntai.views.settings import HoverCard
from yuntai.views.tts import TTSBuilder


_APP = QApplication.instance() or QApplication([])


class _FakeView:
    def __init__(self):
        from PyQt6.QtWidgets import QFrame

        self.components = {}
        self.colors = SimpleNamespace(
            BG_NAV="#1",
            BG_MAIN="#2",
            BG_CARD="#3",
            BG_CARD_ALT="#4",
            BG_HOVER="#5",
            BG_INPUT="#6",
            BG_SCROLLBAR="#7",
            BORDER_LIGHT="#8",
            BORDER_MEDIUM="#9",
            BORDER_FOCUS="#a",
            TEXT_PRIMARY="#b",
            TEXT_SECONDARY="#c",
            TEXT_DISABLED="#d",
            TEXT_LIGHT="#e",
            PRIMARY="#f",
            PRIMARY_HOVER="#10",
            SECONDARY="#11",
            SECONDARY_HOVER="#12",
            DANGER="#13",
            DANGER_HOVER="#14",
            SUCCESS="#15",
            SUCCESS_HOVER="#16",
            WARNING="#17",
            WARNING_HOVER="#18",
            ACCENT="#19",
            ACCENT_HOVER="#1a",
            STATUS_ACTIVE="#1b",
            STATUS_INACTIVE="#1c",
            NAV_HIGHLIGHT_BG="#1d",
            NAV_HIGHLIGHT_HOVER="#1e",
        )
        self.content_pages = [QFrame() for _ in range(6)]
        self.highlighted = []

    def _highlight_nav_button(self, idx):
        self.highlighted.append(idx)

    def _apply_shadow(self, *_args, **_kwargs):
        return None

    def _on_device_type_change(self, *_args, **_kwargs):
        return None

    def show_attached_files(self, *_args, **_kwargs):
        return None


class _Input:
    def __init__(self, text=""):
        self.text = text
        self.heights = []

    def toPlainText(self):
        return self.text

    def setFixedHeight(self, value):
        self.heights.append(value)


class _Event:
    def __init__(self, key, modifiers):
        self._key = key
        self._mod = modifiers
        self.accepted = False

    def key(self):
        return self._key

    def modifiers(self):
        return self._mod

    def accept(self):
        self.accepted = True


def test_builders_create_pages_and_key_components():
    view = _FakeView()

    DashboardBuilder(view).create_page()
    ConnectionBuilder(view).create_page()
    TTSBuilder(view).create_page(object())
    DynamicBuilder(view).create_page()

    assert "execute_button" in view.components
    assert "connect_device_btn" in view.components
    assert "tts_audio_listbox" in view.components
    assert "generate_video_btn" in view.components
    assert view.highlighted[:4] == [0, 1, 2, 4]


def test_dashboard_input_height_adjustment_branches():
    view = _FakeView()
    builder = DashboardBuilder(view)

    inp = _Input("")
    view.components["command_input"] = inp

    builder._last_line_count = 1
    builder._on_input_text_changed()
    assert inp.heights == []

    builder._last_line_count = 3
    builder._on_input_text_changed()
    assert inp.heights[-1] == 42

    inp.text = "a\nb\nc"
    builder._on_input_text_changed()
    assert inp.heights[-1] >= 42


def test_command_text_edit_enter_paths():
    from PyQt6.QtCore import Qt

    widget = CommandTextEdit()
    signals = []
    widget.enter_pressed.connect(lambda: signals.append("enter"))

    widget.keyPressEvent(_Event(Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
    assert signals == ["enter"]

    widget.keyPressEvent(_Event(Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier))
    assert signals == ["enter"]


def test_page_builder_create_methods_only_once():
    calls = {"d": 0, "c": 0, "t": 0, "h": 0, "dy": 0, "s": 0}

    pb = PageBuilder.__new__(PageBuilder)
    pb.page_initialized = [False] * 6
    pb.dashboard = SimpleNamespace(create_page=lambda: calls.__setitem__("d", calls["d"] + 1))
    pb.connection = SimpleNamespace(create_page=lambda: calls.__setitem__("c", calls["c"] + 1))
    pb.tts = SimpleNamespace(create_page=lambda _tm: calls.__setitem__("t", calls["t"] + 1))
    pb.history = SimpleNamespace(create_page=lambda: calls.__setitem__("h", calls["h"] + 1))
    pb.dynamic = SimpleNamespace(create_page=lambda: calls.__setitem__("dy", calls["dy"] + 1))
    pb.settings = SimpleNamespace(create_page=lambda: calls.__setitem__("s", calls["s"] + 1))

    pb.create_dashboard_page()
    pb.create_dashboard_page()
    pb.create_connection_page()
    pb.create_connection_page()
    pb.create_tts_page(object())
    pb.create_tts_page(object())
    pb.create_history_page()
    pb.create_dynamic_page()
    pb.create_settings_page()

    assert calls == {"d": 1, "c": 1, "t": 1, "h": 1, "dy": 1, "s": 1}


def test_hover_card_enter_leave_and_click():
    title = SimpleNamespace(setStyleSheet=lambda *_: None)
    card = HoverCard(0, "#abc", lambda: SimpleNamespace(TEXT_LIGHT="#fff", TEXT_PRIMARY="#000"))
    card.set_styles("normal", "hover")
    card.set_title_label(title)
    card.set_hoverable(False)

    assert card.normal_style == "normal"
    assert card.hover_style == "hover"
    assert card._title_label is title
    assert card._is_hoverable is False

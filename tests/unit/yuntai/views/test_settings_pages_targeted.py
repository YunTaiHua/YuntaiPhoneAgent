from types import SimpleNamespace

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QFrame

from yuntai.views.pages import PageBuilder
from yuntai.views.settings import HoverCard, SettingsBuilder


_APP = QApplication.instance() or QApplication([])


class _Page(QFrame):
    def __init__(self, layout=None):
        super().__init__()
        self._layout = layout

    def layout(self):
        if self._layout is not None:
            return self._layout
        return super().layout()


class _View:
    def __init__(self):
        self.components = {}
        self.colors = SimpleNamespace(
            BG_CARD="#111",
            BORDER_LIGHT="#222",
            TEXT_PRIMARY="#333",
            TEXT_SECONDARY="#444",
            TEXT_LIGHT="#eee",
            PRIMARY="#10",
            SUCCESS="#20",
            SECONDARY="#30",
            ACCENT="#40",
        )
        self.content_pages = [_Page() for _ in range(6)]
        self.highlighted = []
        self.shadow_calls = []

    def _highlight_nav_button(self, idx):
        self.highlighted.append(idx)

    def _apply_shadow(self, card, shadow_type):
        self.shadow_calls.append((card, shadow_type))


class _MouseEvent:
    def __init__(self, button):
        self._button = button

    def button(self):
        return self._button


def test_settings_builder_create_page_builds_components():
    view = _View()
    builder = SettingsBuilder(view)

    builder.create_page()

    assert view.highlighted == [5]
    for idx in range(4):
        assert f"settings_btn_{idx}" in view.components
        assert f"settings_card_{idx}" in view.components
    assert view.shadow_calls


def test_settings_builder_create_page_returns_when_layout_exists():
    view = _View()
    view.content_pages[5] = _Page(layout=object())
    builder = SettingsBuilder(view)

    builder.create_page()

    assert view.highlighted == [5]
    assert view.components == {}


def test_hover_card_events_emit_and_style_changes(monkeypatch):
    from yuntai.views import settings as mod

    monkeypatch.setattr(mod.QFrame, "enterEvent", lambda self, event: None, raising=False)
    monkeypatch.setattr(mod.QFrame, "leaveEvent", lambda self, event: None, raising=False)
    monkeypatch.setattr(mod.QFrame, "mousePressEvent", lambda self, event: None, raising=False)

    title_styles = []
    clicked = []
    title = SimpleNamespace(setStyleSheet=lambda s: title_styles.append(s))
    card = HoverCard(1, "#abc", lambda: SimpleNamespace(TEXT_LIGHT="#fff", TEXT_PRIMARY="#000"))
    card.set_styles("normal-style", "hover-style")
    card.set_title_label(title)
    card.clicked.connect(lambda: clicked.append(True))

    card.enterEvent(object())
    card.leaveEvent(object())
    card.mousePressEvent(_MouseEvent(mod.Qt.MouseButton.LeftButton))
    card.mousePressEvent(_MouseEvent(999))

    assert any("#fff" in s for s in title_styles)
    assert any("#000" in s for s in title_styles)
    assert len(clicked) == 1


def test_page_builder_init_and_theme_noop(monkeypatch):
    import yuntai.views.pages as mod

    class _B:
        def __init__(self, v):
            self.view = v

        def create_page(self, *args, **kwargs):
            return None

    monkeypatch.setattr(mod, "TYPE_CHECKING", False, raising=False)

    # patch delayed imports by injecting modules into sys.modules
    import sys
    import types

    for name, cls_name in [
        ("dashboard", "DashboardBuilder"),
        ("connection", "ConnectionBuilder"),
        ("tts", "TTSBuilder"),
        ("history", "HistoryBuilder"),
        ("settings", "SettingsBuilder"),
        ("dynamic", "DynamicBuilder"),
    ]:
        m = types.ModuleType(f"yuntai.views.{name}")
        setattr(m, cls_name, _B)
        monkeypatch.setitem(sys.modules, f"yuntai.views.{name}", m)

    view = _View()
    pb = PageBuilder(view)

    assert pb.view is view
    assert pb.components is view.components
    assert pb.page_initialized == [False] * 6
    assert pb.tts_manager is None

    # explicit no-op path
    assert pb._apply_current_theme_to_page(2) is None

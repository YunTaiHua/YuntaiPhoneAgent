import os
from types import SimpleNamespace

from PyQt6.QtWidgets import QFrame, QLabel
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QColor

from yuntai.gui.view.navigation import NavigationMixin
from yuntai.gui.view.theme_manager import ThemeManagerMixin


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_APP = QApplication.instance() or QApplication([])


class _Btn:
    def __init__(self):
        self.style = ""

    def setStyleSheet(self, value):
        self.style = value


class _Host(NavigationMixin):
    def __init__(self):
        self.components = {}
        self.colors = SimpleNamespace(
            BG_NAV="#11",
            BG_HOVER="#12",
            BG_MAIN="#13",
            BG_CARD="#14",
            BG_CARD_ALT="#15",
            PRIMARY="#16",
            TEXT_PRIMARY="#17",
            TEXT_SECONDARY="#18",
            TEXT_DISABLED="#19",
            BORDER_LIGHT="#1A",
            STATUS_INACTIVE="#1B",
            NAV_HIGHLIGHT_BG="#1C",
            NAV_HIGHLIGHT_HOVER="#1D",
        )
        self.central = None

    def setCentralWidget(self, widget):
        self.central = widget


def test_navigation_setup_main_layout_populates_expected_components():
    host = _Host()
    host._setup_main_layout()

    assert host.central is not None
    assert host.components["connection_indicator"].text() == "● 未连接"
    assert host.components["tts_indicator"].text() == "● TTS: 关闭"
    assert len(host.components["nav_buttons"]) == 6
    assert host.page_stack.count() == 6


def test_theme_update_global_component_styles_covered_branches():
    host = ThemeManagerMixin()
    nav = QFrame()
    phone_title = QLabel("Phone Agent", nav)
    helper = QLabel("智能移动助手", nav)
    version = QLabel("Version 1.0", nav)

    conn = QLabel("● 已连接")
    tts = QLabel("● TTS: 开启")
    theme_btn = QLabel()
    card = QFrame()
    status = QFrame()
    main_container = QFrame()
    overlay = QFrame()
    overlay_card = QFrame(overlay)
    overlay_card.setObjectName("overlayCard")
    loading_label = QLabel()

    host.colors = SimpleNamespace(
        BG_NAV="#1",
        BG_HOVER="#2",
        BG_CARD_ALT="#3",
        BG_MAIN="#4",
        BG_CARD="#5",
        BORDER_LIGHT="#6",
        PRIMARY="#7",
        TEXT_PRIMARY="#8",
        TEXT_SECONDARY="#9",
        TEXT_DISABLED="#10",
        STATUS_ACTIVE="#11",
        STATUS_INACTIVE="#12",
        NAV_HIGHLIGHT_BG="#13",
        NAV_HIGHLIGHT_HOVER="#14",
    )
    host.is_dark_theme = True
    host.current_page_index = 1
    host.nav_frame = nav
    host.main_container = main_container
    host.status_bar = status
    host.tts_loading_overlay = overlay
    host.components = {
        "nav_buttons": [_Btn(), _Btn()],
        "connection_indicator": conn,
        "tts_indicator": tts,
        "theme_toggle_button": theme_btn,
        "content_card": card,
        "tts_loading_label": loading_label,
    }

    host._update_global_components_style()

    assert "#13" in host.components["nav_buttons"][1].style
    assert "#11" in conn.styleSheet()
    assert "#11" in tts.styleSheet()
    assert host.components["theme_toggle_button"].text() == "☀️"
    assert "rgba(26, 26, 46, 200)" in overlay.styleSheet()


def test_theme_apply_shadow_apply_theme_refresh_and_apply_all_pages(monkeypatch):
    host = ThemeManagerMixin()
    host.is_dark_theme = False

    applied = []
    monkeypatch.setattr("yuntai.gui.view.theme_manager.apply_light_theme", lambda app: applied.append(("light", app is _APP)))
    monkeypatch.setattr("yuntai.gui.view.theme_manager.apply_dark_theme", lambda app: applied.append(("dark", app is _APP)))
    monkeypatch.setattr("yuntai.gui.view.theme_manager.get_main_stylesheet", lambda _c: "x-style")

    host._apply_theme()
    assert applied[0][0] == "light"
    assert _APP.styleSheet() == "x-style"

    host.is_dark_theme = True
    host._apply_theme()
    assert applied[-1][0] == "dark"

    w = QFrame()
    host._apply_shadow(w, "lg")
    effect = w.graphicsEffect()
    assert effect is not None
    assert isinstance(effect.color(), QColor)

    host.colors = SimpleNamespace()
    host.content_pages = [QFrame(), QFrame()]
    host.nav_frame = QFrame()
    host.status_bar = QFrame()
    host.update = lambda: setattr(host, "_updated", True)
    host._refresh_all_pages()
    assert getattr(host, "_updated", False) is True

    calls = []
    host.page_initialized = [True, False, True, False, False, True]
    host.page_builder = SimpleNamespace(_apply_current_theme_to_page=lambda i: calls.append(i))
    host._apply_theme_to_all_pages()
    assert calls == [0, 2, 5]

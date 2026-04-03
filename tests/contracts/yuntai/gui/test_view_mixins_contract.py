from types import SimpleNamespace

from yuntai.gui.view.dialogs import DialogsMixin
from yuntai.gui.view.loading_overlay import LoadingOverlayMixin
from yuntai.gui.view.navigation import NavigationMixin
from yuntai.gui.view.page_manager import PageManagerMixin
from yuntai.gui.view.theme_manager import ThemeManagerMixin
from yuntai.gui.view.toast_widget import ToastWidget


class _Host(
    DialogsMixin,
    LoadingOverlayMixin,
    NavigationMixin,
    PageManagerMixin,
    ThemeManagerMixin,
):
    def __init__(self):
        self.components = {}
        self.colors = SimpleNamespace(
            BG_NAV="#1",
            BG_MAIN="#2",
            BG_CARD="#3",
            BG_CARD_ALT="#4",
            BG_HOVER="#5",
            BORDER_LIGHT="#6",
            BORDER_MEDIUM="#7",
            BORDER_FOCUS="#8",
            TEXT_PRIMARY="#9",
            TEXT_SECONDARY="#a",
            TEXT_DISABLED="#b",
            PRIMARY="#c",
            PRIMARY_HOVER="#d",
            SECONDARY="#e",
            SECONDARY_HOVER="#f",
            STATUS_ACTIVE="#10",
            STATUS_INACTIVE="#11",
            NAV_HIGHLIGHT_BG="#12",
            NAV_HIGHLIGHT_HOVER="#13",
        )
        self.is_dark_theme = False
        self.current_page_index = 0
        self.page_builder = SimpleNamespace(
            page_initialized=[False] * 6,
            create_dashboard_page=lambda: None,
            create_connection_page=lambda: None,
            create_tts_page=lambda _tm: None,
            create_history_page=lambda: None,
            create_dynamic_page=lambda: None,
            create_settings_page=lambda: None,
            _apply_current_theme_to_page=lambda _i: None,
        )
        self.page_initialized = [False] * 6
        self.content_pages = []
        self.nav_frame = SimpleNamespace(findChildren=lambda _cls: [], setStyleSheet=lambda _s: None)
        self.main_container = SimpleNamespace(setStyleSheet=lambda _s: None)
        self.status_bar = SimpleNamespace(setStyleSheet=lambda _s: None)
        self.page_stack = SimpleNamespace(setCurrentIndex=lambda _i: None)
        self._highlight_nav_button = lambda _i: None
        self.setCentralWidget = lambda _w: None
        self.setWindowState = lambda _s: None
        self.windowState = lambda: 0
        self.setFixedSize = lambda *_a, **_k: None
        self.setMinimumSize = lambda *_a, **_k: None
        self.setMaximumSize = lambda *_a, **_k: None
        self.size = lambda: SimpleNamespace()
        self.width = lambda: 1200
        self.height = lambda: 800
        self.update = lambda: None


def test_mixins_have_expected_methods_and_basic_runtime_contracts():
    assert callable(getattr(DialogsMixin, "show_file_upload_dialog"))
    assert callable(getattr(LoadingOverlayMixin, "show_tts_loading"))
    assert callable(getattr(NavigationMixin, "_highlight_nav_button"))
    assert callable(getattr(PageManagerMixin, "show_page"))
    assert callable(getattr(ThemeManagerMixin, "toggle_theme"))
    assert isinstance(ToastWidget, type)

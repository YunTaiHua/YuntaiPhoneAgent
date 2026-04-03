from types import SimpleNamespace

from yuntai.views.connection import ConnectionBuilder
from yuntai.views.dashboard import CommandTextEdit, DashboardBuilder
from yuntai.views.dynamic import DynamicBuilder, DynamicLayoutConstants
from yuntai.views.history import HistoryBuilder
from yuntai.views.settings import HoverCard, SettingsBuilder, SettingsLayoutConstants
from yuntai.views.tts import TTSBuilder, TTSLayoutConstants


class _Page:
    def __init__(self):
        self._layout = None

    def layout(self):
        return self._layout

    def setLayout(self, layout):
        self._layout = layout


class _View:
    def __init__(self):
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
        )
        self.content_pages = [_Page() for _ in range(6)]
        self._highlight_nav_button = lambda _i: None
        self._apply_shadow = lambda *_args, **_kwargs: None
        self._on_device_type_change = lambda *_args, **_kwargs: None
        self.show_attached_files = lambda *_args, **_kwargs: None


def test_view_builders_can_be_constructed_and_create_methods_are_callable():
    view = _View()
    assert isinstance(ConnectionBuilder(view), ConnectionBuilder)
    assert isinstance(DashboardBuilder(view), DashboardBuilder)
    assert isinstance(HistoryBuilder(view), HistoryBuilder)
    assert isinstance(SettingsBuilder(view), SettingsBuilder)
    assert isinstance(DynamicBuilder(view), DynamicBuilder)
    assert isinstance(TTSBuilder(view), TTSBuilder)

    assert callable(ConnectionBuilder.create_page)
    assert callable(DashboardBuilder.create_page)
    assert callable(HistoryBuilder.create_page)
    assert callable(SettingsBuilder.create_page)
    assert callable(DynamicBuilder.create_page)
    assert callable(TTSBuilder.create_page)


def test_constants_and_helper_classes_contract():
    assert DynamicLayoutConstants.LEFT_MARGIN > 0
    assert SettingsLayoutConstants.CARD_MIN_HEIGHT > 0
    assert TTSLayoutConstants.FORM_LABEL_WIDTH > 0
    assert hasattr(HoverCard, "clicked")
    assert callable(CommandTextEdit.keyPressEvent)

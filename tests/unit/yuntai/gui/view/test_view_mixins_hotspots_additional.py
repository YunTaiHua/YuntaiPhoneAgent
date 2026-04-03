from types import SimpleNamespace
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from yuntai.gui.view.dialogs import DialogsMixin
from yuntai.gui.view.loading_overlay import LoadingOverlayMixin
from yuntai.gui.view.navigation import NavigationMixin
from yuntai.gui.view.page_manager import PageManagerMixin
from yuntai.gui.view.theme_manager import ThemeManagerMixin
from yuntai.gui.view.toast_widget import ToastWidget


_APP = QApplication.instance() or QApplication([])


class _Btn:
    def __init__(self):
        self.style = ""

    def setStyleSheet(self, value):
        self.style = value


def test_navigation_highlight_sets_selected_and_unselected_styles():
    host = NavigationMixin()
    host.colors = SimpleNamespace(
        NAV_HIGHLIGHT_BG="#1",
        NAV_HIGHLIGHT_HOVER="#2",
        PRIMARY="#3",
        TEXT_PRIMARY="#4",
        BG_HOVER="#5",
    )
    host.components = {"nav_buttons": [_Btn(), _Btn(), _Btn()]}

    host._highlight_nav_button(1)

    assert "border-left: 3px solid #3" in host.components["nav_buttons"][1].style
    assert "border-left: 3px solid transparent" in host.components["nav_buttons"][0].style


def test_dialogs_show_attached_files_handles_missing_frame():
    host = DialogsMixin()
    host.colors = SimpleNamespace()
    host.get_component = lambda _name: None
    host.show_attached_files(["a.txt"], None)


def test_dialogs_show_attached_files_renders_items_and_clear_action(tmp_path):
    from PyQt6.QtWidgets import QFrame, QVBoxLayout

    frame = QFrame()
    frame.setLayout(QVBoxLayout())

    calls = []
    host = DialogsMixin()
    host.colors = SimpleNamespace(
        BG_HOVER="#1",
        TEXT_PRIMARY="#2",
        DANGER="#3",
        DANGER_HOVER="#4",
        WARNING="#5",
        WARNING_HOVER="#6",
        TEXT_LIGHT="#7",
    )
    host.get_component = lambda name: frame if name == "files_list_scroll_frame" else None

    controller = SimpleNamespace(
        remove_attached_file=lambda f: calls.append(("remove", f)),
        clear_attached_files=lambda: calls.append(("clear", None)),
    )

    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")
    host.show_attached_files([str(f)], controller)

    assert frame.layout().count() > 0


def test_page_manager_init_callbacks_and_guard():
    calls = []
    host = PageManagerMixin()
    host.page_builder = SimpleNamespace(
        page_initialized=[False] * 6,
        tts_manager=object(),
        create_dashboard_page=lambda: calls.append(0),
        create_connection_page=lambda: calls.append(1),
        create_tts_page=lambda _tm: calls.append(2),
        create_history_page=lambda: calls.append(3),
        create_dynamic_page=lambda: calls.append(4),
        create_settings_page=lambda: calls.append(5),
    )

    for idx in range(6):
        host._call_page_init_callback(idx)

    assert calls == [0, 1, 2, 3, 4, 5]

    host.page_builder.page_initialized[3] = True
    host._call_page_init_callback(3)
    assert calls == [0, 1, 2, 3, 4, 5]


def test_loading_overlay_show_hide_and_resize():
    from PyQt6.QtWidgets import QWidget

    class _Window(QWidget, LoadingOverlayMixin):
        def __init__(self):
            super().__init__()
            self.components = {}
            self.colors = SimpleNamespace(BG_CARD="#1", BORDER_LIGHT="#2", TEXT_PRIMARY="#3")
            self._min = None

        def setMinimumSize(self, w, h):
            self._min = (w, h)
            return super().setMinimumSize(w, h)

    win = _Window()
    win._create_tts_loading_overlay()
    win.show_tts_loading("loading")
    assert "tts_loading_label" in win.components
    win.hide_tts_loading()
    assert win._min == (1200, 700)
    win.resizeEvent(None)


def test_theme_manager_toggle_theme_resets_pages_and_components():
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

    page = QFrame()
    page.setLayout(QVBoxLayout())
    page.layout().addWidget(QLabel("x"))

    host = ThemeManagerMixin()
    host.is_dark_theme = False
    host.page_initialized = [True] * 6
    host.page_builder = SimpleNamespace(page_initialized=[True] * 6)
    host.content_pages = [page]
    host.components = {"nav_buttons": [], "to_remove": object(), "theme_toggle_button": object()}
    host.current_page_index = 2
    host.toast_widget = SimpleNamespace(update_theme=lambda *_: None)
    host._apply_theme = lambda: None
    host._update_global_components_style = lambda: None
    seen = []
    host.show_page = lambda idx: seen.append(idx)

    host.toggle_theme()

    assert host.page_initialized == [False] * 6
    assert host.page_builder.page_initialized == [False] * 6
    assert "to_remove" not in host.components
    assert seen == [2]


def test_toast_widget_force_replace_and_theme_update():
    from PyQt6.QtWidgets import QWidget

    parent = QWidget()
    toast = ToastWidget(parent)
    calls = []
    toast._is_showing = True
    toast._force_hide_and_show_new = lambda m, t, d: calls.append((m, t, d))

    toast.show_toast("hello", "warning", 123)
    assert calls == [("hello", "warning", 123)]

    toast.update_theme(True)
    assert toast.is_dark_theme is True

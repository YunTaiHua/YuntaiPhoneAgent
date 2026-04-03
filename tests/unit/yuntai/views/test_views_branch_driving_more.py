from types import SimpleNamespace
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from yuntai.views.connection import ConnectionBuilder
from yuntai.views.dashboard import DashboardBuilder
from yuntai.views.dynamic import DynamicBuilder
from yuntai.views.tts import TTSBuilder


_APP = QApplication.instance() or QApplication([])


class _View:
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


def test_views_create_page_idempotency_and_extra_widgets():
    view = _View()

    d = DashboardBuilder(view)
    c = ConnectionBuilder(view)
    t = TTSBuilder(view)
    dy = DynamicBuilder(view)

    d.create_page()
    c.create_page()
    t.create_page(SimpleNamespace(tts_available=True, default_tts_config={"gpt_model_dir": "g", "sovits_model_dir": "s", "ref_audio_root": "a", "output_path": "o"}, tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}}))
    dy.create_page()

    first = {
        "dashboard_layout": view.content_pages[0].layout(),
        "connection_layout": view.content_pages[1].layout(),
        "dynamic_layout": view.content_pages[4].layout(),
    }

    d.create_page()
    c.create_page()
    dy.create_page()
    t.create_page(SimpleNamespace(tts_available=False, default_tts_config={"gpt_model_dir": "g", "sovits_model_dir": "s", "ref_audio_root": "a", "output_path": "o"}, tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}}))

    assert view.content_pages[0].layout() is first["dashboard_layout"]
    assert view.content_pages[1].layout() is first["connection_layout"]
    assert view.content_pages[4].layout() is first["dynamic_layout"]

    assert "image_log_text" in view.components
    assert "video_log_text" in view.components
    assert "tts_log_text" in view.components
    assert "device_type_menu" in view.components


def test_dashboard_enter_handler_and_attached_files_init():
    view = _View()
    calls = []
    d = DashboardBuilder(view)
    view.components["execute_button"] = SimpleNamespace(click=lambda: calls.append("clicked"))

    d._on_enter_pressed()
    assert calls == ["clicked"]

    d._init_attached_files_display()

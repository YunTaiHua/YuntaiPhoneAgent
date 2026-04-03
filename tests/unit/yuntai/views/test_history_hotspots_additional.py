from types import SimpleNamespace

from PyQt6.QtWidgets import QFrame

from yuntai.views.history import HistoryBuilder


class _View:
    def __init__(self):
        self.components = {}
        self.colors = SimpleNamespace(
            BG_CARD="#1",
            BORDER_LIGHT="#2",
            TEXT_PRIMARY="#3",
            TEXT_SECONDARY="#4",
            SECONDARY="#5",
            SECONDARY_HOVER="#6",
            DANGER="#7",
            DANGER_HOVER="#8",
            BG_CARD_ALT="#9",
            TEXT_LIGHT="#a",
        )
        self.content_pages = [QFrame() for _ in range(6)]
        self.highlighted = []
        self.shadow_calls = []

    def _highlight_nav_button(self, index):
        self.highlighted.append(index)

    def _apply_shadow(self, widget, shadow_type):
        self.shadow_calls.append((widget, shadow_type))


def test_history_builder_create_page_and_idempotent():
    view = _View()
    builder = HistoryBuilder(view)

    builder.create_page()
    first_layout = view.content_pages[3].layout()

    assert view.highlighted == [3]
    assert "refresh_history_btn" in view.components
    assert "clear_history_btn" in view.components
    assert "history_text" in view.components
    assert view.shadow_calls

    builder.create_page()
    assert view.content_pages[3].layout() is first_layout
    assert view.highlighted == [3, 3]


def test_history_builder_colors_property_and_create_card_shadow_type():
    view = _View()
    builder = HistoryBuilder(view)

    assert builder.colors is view.colors
    view.colors = SimpleNamespace(
        BG_CARD="#10",
        BORDER_LIGHT="#11",
        TEXT_PRIMARY="#12",
        TEXT_SECONDARY="#13",
        SECONDARY="#14",
        SECONDARY_HOVER="#15",
        DANGER="#16",
        DANGER_HOVER="#17",
        BG_CARD_ALT="#18",
        TEXT_LIGHT="#19",
    )
    assert builder.colors is view.colors

    card = builder._create_card(corner_radius=22, shadow_type="lg")
    assert card is not None
    assert view.shadow_calls[-1][1] == "lg"

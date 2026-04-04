from types import SimpleNamespace

from yuntai.gui.view import theme_manager as mod


class TestThemeManagerDeepBranches:
    def test_theme_manager_init(self):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False
        assert tm.is_dark_theme is False

    def test_theme_manager_apply_theme_light(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False

        class _FakeApp:
            def setStyleSheet(self, s):
                pass

            def setPalette(self, p):
                pass

        fake_app = _FakeApp()
        monkeypatch.setattr(mod.QApplication, "instance", lambda: fake_app)
        tm._apply_theme()
        assert hasattr(tm, "colors")

    def test_theme_manager_apply_theme_dark(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = True

        class _FakeApp:
            def setStyleSheet(self, s):
                pass

            def setPalette(self, p):
                pass

        fake_app = _FakeApp()
        monkeypatch.setattr(mod.QApplication, "instance", lambda: fake_app)
        tm._apply_theme()
        assert hasattr(tm, "colors")

    def test_theme_manager_toggle_theme(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False
        tm.page_initialized = [False] * 6
        tm.content_pages = []
        tm.components = {}
        tm.current_page_index = 0

        class _FakePageBuilder:
            page_initialized = [False] * 6

        tm.page_builder = _FakePageBuilder()

        class _FakeApp:
            def setStyleSheet(self, s):
                pass

            def setPalette(self, p):
                pass

        fake_app = _FakeApp()
        monkeypatch.setattr(mod.QApplication, "instance", lambda: fake_app)
        tm._apply_theme = lambda: None
        tm._update_global_components_style = lambda: None
        tm.show_page = lambda i: None
        tm.toggle_theme()
        assert tm.is_dark_theme is True

    def test_theme_manager_apply_shadow(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False

        class _FakeWidget:
            effect = None

            def setGraphicsEffect(self, effect):
                self.effect = effect

        widget = _FakeWidget()
        tm._apply_shadow(widget, "sm")
        assert widget.effect is not None

    def test_update_global_components_style_tts_indicator_closed(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False

        class _FakeColors:
            STATUS_INACTIVE = "#999"
            STATUS_ACTIVE = "#0f0"
            BG_HOVER = "#eee"
            TEXT_PRIMARY = "#333"
            TEXT_LIGHT = "#fff"
            BG_NAV = "#fff"
            PRIMARY = "#0078d4"
            TEXT_SECONDARY = "#666"
            TEXT_DISABLED = "#999"
            NAV_HIGHLIGHT_BG = "#e6f3ff"
            NAV_HIGHLIGHT_HOVER = "#d0e8ff"

        tm.colors = _FakeColors()
        tm.nav_frame = None
        tm.current_page_index = 0

        styles_set = []

        class _FakeTTSIndicator:
            def text(self):
                return "TTS已关闭"

            def setStyleSheet(self, s):
                styles_set.append(s)

        tts_ind = _FakeTTSIndicator()
        tm.components = {"tts_indicator": tts_ind, "nav_buttons": []}

        class _FakeApp:
            def setStyleSheet(self, s):
                pass

            def setPalette(self, p):
                pass

        monkeypatch.setattr(mod.QApplication, "instance", lambda: _FakeApp())
        tm._update_global_components_style()
        assert len(styles_set) > 0
        assert "#999" in styles_set[0]

    def test_update_global_components_style_tts_indicator_active(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False

        class _FakeColors:
            STATUS_INACTIVE = "#999"
            STATUS_ACTIVE = "#0f0"
            BG_HOVER = "#eee"
            TEXT_PRIMARY = "#333"
            TEXT_LIGHT = "#fff"
            BG_NAV = "#fff"
            PRIMARY = "#0078d4"
            TEXT_SECONDARY = "#666"
            TEXT_DISABLED = "#999"
            NAV_HIGHLIGHT_BG = "#e6f3ff"
            NAV_HIGHLIGHT_HOVER = "#d0e8ff"

        tm.colors = _FakeColors()
        tm.nav_frame = None
        tm.current_page_index = 0

        styles_set = []

        class _FakeTTSIndicator:
            def text(self):
                return "TTS已开启"

            def setStyleSheet(self, s):
                styles_set.append(s)

        tts_ind = _FakeTTSIndicator()
        tm.components = {"tts_indicator": tts_ind, "nav_buttons": []}

        class _FakeApp:
            def setStyleSheet(self, s):
                pass

            def setPalette(self, p):
                pass

        monkeypatch.setattr(mod.QApplication, "instance", lambda: _FakeApp())
        tm._update_global_components_style()
        assert len(styles_set) > 0
        assert "#0f0" in styles_set[0]

    def test_clear_layout(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)

        class _FakeItem:
            def __init__(self, has_widget, has_layout):
                self._has_widget = has_widget
                self._has_layout = has_layout

            def widget(self):
                if self._has_widget:
                    return SimpleNamespace(deleteLater=lambda: None)
                return None

            def layout(self):
                if self._has_layout:
                    return SimpleNamespace(count=lambda: 0)
                return None

        class _FakeLayout:
            def __init__(self):
                self._items = [_FakeItem(True, False), _FakeItem(False, True)]

            def count(self):
                return len(self._items)

            def takeAt(self, idx):
                if self._items:
                    return self._items.pop(0)
                return None

        tm._clear_layout(_FakeLayout())

    def test_refresh_all_pages(self, monkeypatch):
        tm = mod.ThemeManagerMixin.__new__(mod.ThemeManagerMixin)
        tm.is_dark_theme = False

        class _FakeColors:
            pass

        tm.colors = _FakeColors()
        tm.content_pages = [SimpleNamespace(update=lambda: None), None]
        tm.nav_frame = SimpleNamespace(update=lambda: None)

        class _FakeApp:
            def setStyleSheet(self, s):
                pass

        monkeypatch.setattr(mod.QApplication, "instance", lambda: _FakeApp())
        monkeypatch.setattr(mod, "get_main_stylesheet", lambda c: "stylesheet")
        tm.update = lambda: None
        tm._refresh_all_pages()

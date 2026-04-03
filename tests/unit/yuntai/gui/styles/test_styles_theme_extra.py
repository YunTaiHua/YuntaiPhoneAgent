from types import SimpleNamespace

from yuntai.gui.styles import stylesheets, theme


def test_dialog_button_stylesheet_supports_known_and_default_types():
    css_primary = stylesheets.get_dialog_button_stylesheet("primary")
    css_cancel = stylesheets.get_dialog_button_stylesheet("cancel")
    css_unknown = stylesheets.get_dialog_button_stylesheet("unknown")
    assert "QPushButton" in css_primary
    assert "QPushButton" in css_cancel
    assert "QPushButton" in css_unknown


def test_other_stylesheet_builders_return_css_strings():
    assert "QDialog" in stylesheets.get_dialog_stylesheet()
    assert "QFrame" in stylesheets.get_dialog_card_stylesheet()
    assert "QTextEdit" in stylesheets.get_dialog_textedit_stylesheet()
    assert "QListWidget" in stylesheets.get_dialog_list_stylesheet()
    assert "QTreeWidget" in stylesheets.get_dialog_tree_stylesheet()
    assert "QComboBox" in stylesheets.get_dialog_combobox_stylesheet()
    assert "QCheckBox" in stylesheets.get_dialog_checkbox_stylesheet()
    assert "QFrame#overlayFrame" in stylesheets.get_overlay_stylesheet()


def test_apply_theme_functions_set_palette():
    class _App:
        def __init__(self):
            self.palette = None

        def setPalette(self, palette):
            self.palette = palette

    app = _App()
    theme.apply_light_theme(app)
    assert app.palette is not None

    app2 = _App()
    theme.apply_dark_theme(app2)
    assert app2.palette is not None


def test_show_confirm_dialog_and_warning_dialog_execute(monkeypatch):
    class _Dialog:
        def __init__(self, *_args, **_kwargs):
            self._accepted = False

        def setWindowTitle(self, *_args, **_kwargs):
            return None

        def setFixedSize(self, *_args, **_kwargs):
            return None

        def setModal(self, *_args, **_kwargs):
            return None

        def setStyleSheet(self, *_args, **_kwargs):
            return None

        def accept(self):
            self._accepted = True

        def reject(self):
            self._accepted = False

        def exec(self):
            return 0

    class _Layout:
        def __init__(self, *_args, **_kwargs):
            self.items = []

        def setContentsMargins(self, *_args, **_kwargs):
            return None

        def setSpacing(self, *_args, **_kwargs):
            return None

        def addWidget(self, *_args, **_kwargs):
            return None

        def addStretch(self, *_args, **_kwargs):
            return None

        def addLayout(self, *_args, **_kwargs):
            return None

    class _Label:
        def __init__(self, *_args, **_kwargs):
            return None

        def setFont(self, *_args, **_kwargs):
            return None

        def setAlignment(self, *_args, **_kwargs):
            return None

        def setWordWrap(self, *_args, **_kwargs):
            return None

        def setStyleSheet(self, *_args, **_kwargs):
            return None

    class _Button:
        def __init__(self, *_args, **_kwargs):
            self.clicked = SimpleNamespace(connect=lambda _fn: None)

        def setFont(self, *_args, **_kwargs):
            return None

        def setFixedHeight(self, *_args, **_kwargs):
            return None

        def setFixedWidth(self, *_args, **_kwargs):
            return None

        def setStyleSheet(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(stylesheets, "QDialog", _Dialog)
    monkeypatch.setattr(stylesheets, "QVBoxLayout", _Layout)
    monkeypatch.setattr(stylesheets, "QHBoxLayout", _Layout)
    monkeypatch.setattr(stylesheets, "QLabel", _Label)
    monkeypatch.setattr(stylesheets, "QPushButton", _Button)
    parent = SimpleNamespace(colors=stylesheets.ThemeColors)

    stylesheets.show_warning_dialog(parent, "t", "m")
    result = stylesheets.show_confirm_dialog(parent, "t", "m")
    assert result in (True, False)

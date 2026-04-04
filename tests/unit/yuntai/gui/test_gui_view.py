import importlib
import inspect
import sys
from types import SimpleNamespace

import pytest

import yuntai.gui.gui_view as mod


def test_gui_view_class_and_mixins_declared():
    assert inspect.isclass(mod.GUIView)
    mro_names = [c.__name__ for c in mod.GUIView.__mro__]
    assert "ThemeManagerMixin" in mro_names
    assert "NavigationMixin" in mro_names
    assert "LoadingOverlayMixin" in mro_names
    assert "PageManagerMixin" in mro_names
    assert "DialogsMixin" in mro_names


def test_gui_view_init_source_contains_expected_steps():
    src = inspect.getsource(mod.GUIView.__init__)
    assert "self.components = {}" in src
    assert "self.is_dark_theme = False" in src
    assert "self.current_page_index = -1" in src
    assert "self.page_initialized = [False] * 6" in src
    assert "self._apply_theme()" in src
    assert "self._create_tts_loading_overlay()" in src
    assert "self._setup_main_layout()" in src
    assert "self._create_toast_widget()" in src


def test_gui_view_init_executes_expected_setup(monkeypatch):
    monkeypatch.setattr(mod.QMainWindow, "__init__", lambda self: None)
    monkeypatch.setattr(mod.GUIView, "setWindowTitle", lambda self, text: setattr(self, "_title", text))
    monkeypatch.setattr(mod.GUIView, "setGeometry", lambda self, *_a: None)
    monkeypatch.setattr(mod.GUIView, "setMinimumSize", lambda self, *_a: None)

    monkeypatch.setattr(mod.GUIView, "_apply_theme", lambda self: setattr(self, "_theme_applied", True))
    monkeypatch.setattr(mod.GUIView, "_create_tts_loading_overlay", lambda self: setattr(self, "_overlay", True))
    monkeypatch.setattr(mod.GUIView, "_setup_main_layout", lambda self: setattr(self, "_layout_done", True))
    monkeypatch.setattr(mod.GUIView, "_create_toast_widget", lambda self: setattr(self, "_toast", True))

    class _PageBuilder:
        def __init__(self, view):
            self.view = view

    fake_pages = SimpleNamespace(PageBuilder=_PageBuilder)
    monkeypatch.setitem(sys.modules, "yuntai.views.pages", fake_pages)

    view = mod.GUIView()
    assert isinstance(view.components, dict)
    assert view.is_dark_theme is False
    assert view.current_page_index == -1
    assert view.page_initialized == [False] * 6
    assert getattr(view, "_theme_applied", False) is True
    assert getattr(view, "_overlay", False) is True
    assert getattr(view, "_layout_done", False) is True
    assert getattr(view, "_toast", False) is True
    assert hasattr(view, "page_builder")


def test_gui_controller_class_mro_and_main(monkeypatch):
    gui_mod = importlib.import_module("yuntai.gui.gui_controller")
    assert issubclass(gui_mod.GUIController, gui_mod.ControllerCore)
    assert issubclass(gui_mod.GUIController, gui_mod.CommandMixin)

    created = {}

    class _FakeController:
        def __init__(self, project_root, scrcpy_path):
            created["project_root"] = project_root
            created["scrcpy_path"] = scrcpy_path

        def run(self):
            return 7

    cfg = importlib.import_module("yuntai.core.config")
    monkeypatch.setattr(cfg, "PROJECT_ROOT", "ROOT_X", raising=False)
    monkeypatch.setattr(cfg, "SCRCPY_PATH", "SCRCPY_X", raising=False)
    monkeypatch.setattr(gui_mod, "GUIController", _FakeController)

    def _raise_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", _raise_exit)

    with pytest.raises(SystemExit) as excinfo:
        gui_mod.main()

    assert excinfo.value.code == 7
    assert created == {"project_root": "ROOT_X", "scrcpy_path": "SCRCPY_X"}

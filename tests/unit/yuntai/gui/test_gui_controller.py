import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import yuntai.gui.gui_controller as mod


class TestGUIController:
    def test_gui_controller_class_mro(self):
        from yuntai.gui.controller.core import ControllerCore

        assert issubclass(mod.GUIController, ControllerCore)

    def test_main_function_creates_controller_and_exits(self, monkeypatch):
        created = {}

        class _FakeController:
            def __init__(self, project_root, scrcpy_path):
                created["project_root"] = project_root
                created["scrcpy_path"] = scrcpy_path

            def run(self):
                return 42

        fake_config = types.ModuleType("yuntai.core.config")
        fake_config.PROJECT_ROOT = "ROOT_X"
        fake_config.SCRCPY_PATH = "SCRCPY_X"
        monkeypatch.setitem(sys.modules, "yuntai.core.config", fake_config)
        monkeypatch.setattr(mod, "GUIController", _FakeController)

        exits = []
        monkeypatch.setattr(sys, "exit", lambda code: exits.append(code))

        mod.main()

        assert created == {"project_root": "ROOT_X", "scrcpy_path": "SCRCPY_X"}
        assert exits == [42]

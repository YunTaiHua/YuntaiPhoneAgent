import importlib
import sys
import types

import pytest


@pytest.mark.parametrize(
    "name,module_path,attr_name",
    [
        ("GUIView", "yuntai.gui.gui_view", "GUIView"),
        ("GUIController", "yuntai.gui.gui_controller", "GUIController"),
        ("TaskManager", "yuntai.services.task_manager", "TaskManager"),
        ("MainApp", "yuntai.core.main_app", "MainApp"),
        ("MultimodalProcessor", "yuntai.processors.multimodal_processor", "MultimodalProcessor"),
        ("MediaGenerator", "yuntai.processors.media_generator", "MediaGenerator"),
        ("ImagePreviewWindow", "yuntai.views.dynamic", "ImagePreviewWindow"),
        ("VideoPreviewWindow", "yuntai.views.dynamic", "VideoPreviewWindow"),
        ("AudioProcessor", "yuntai.processors.audio_processor", "AudioProcessor"),
    ],
)
def test_yuntai_lazy_getattr_paths(monkeypatch, name, module_path, attr_name):
    yuntai_mod = importlib.import_module("yuntai")

    sentinel = object()
    fake_module = types.ModuleType(module_path)
    setattr(fake_module, attr_name, sentinel)
    monkeypatch.setitem(sys.modules, module_path, fake_module)

    assert yuntai_mod.__getattr__(name) is sentinel


def test_yuntai_lazy_getattr_unknown_raises_attribute_error():
    yuntai_mod = importlib.import_module("yuntai")
    with pytest.raises(AttributeError):
        yuntai_mod.__getattr__("__not_existing__")


def test_yuntai_public_exports_contain_expected_symbols():
    yuntai_mod = importlib.import_module("yuntai")
    assert "GUIController" in yuntai_mod.__all__
    assert "MainApp" in yuntai_mod.__all__
    assert "TimeTool" in yuntai_mod.__all__


def test_handlers_protocols_module_contracts():
    mod = importlib.import_module("yuntai.handlers.protocols")

    assert hasattr(mod, "ViewCallbacks")
    assert hasattr(mod, "ControllerCallbacks")
    assert callable(getattr(mod.ViewCallbacks, "show_toast", None))
    assert callable(getattr(mod.ControllerCallbacks, "update_tts_indicator", None))


def test_gui_controller_class_mro_and_main(monkeypatch):
    mod = importlib.import_module("yuntai.gui.gui_controller")
    assert issubclass(mod.GUIController, mod.ControllerCore)
    assert issubclass(mod.GUIController, mod.CommandMixin)

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
    monkeypatch.setattr(mod, "GUIController", _FakeController)

    def _raise_exit(code):
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", _raise_exit)

    with pytest.raises(SystemExit) as excinfo:
        mod.main()

    assert excinfo.value.code == 7
    assert created == {"project_root": "ROOT_X", "scrcpy_path": "SCRCPY_X"}

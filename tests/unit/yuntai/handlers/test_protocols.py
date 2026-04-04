import importlib


def test_handlers_protocols_module_contracts():
    mod = importlib.import_module("yuntai.handlers.protocols")
    assert hasattr(mod, "ViewCallbacks")
    assert hasattr(mod, "ControllerCallbacks")
    assert callable(getattr(mod.ViewCallbacks, "show_toast", None))
    assert callable(getattr(mod.ControllerCallbacks, "update_tts_indicator", None))

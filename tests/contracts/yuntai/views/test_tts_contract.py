import importlib
import inspect


def test_views_module_exports_tts_builder_contract():
    views_module = importlib.import_module("yuntai.views")
    tts_module = importlib.import_module("yuntai.views.tts")

    assert "TTSBuilder" in views_module.__all__
    assert hasattr(views_module, "TTSBuilder")
    assert views_module.TTSBuilder is tts_module.TTSBuilder


def test_tts_module_exports_layout_constants_contract():
    tts_module = importlib.import_module("yuntai.views.tts")

    assert hasattr(tts_module, "TTSLayoutConstants")
    assert isinstance(tts_module.TTSLayoutConstants, type)


def test_tts_builder_methods_are_callable_contracts():
    tts_module = importlib.import_module("yuntai.views.tts")
    builder = tts_module.TTSBuilder

    expected_methods = [
        "create_page",
        "_create_card",
        "_create_button",
        "_create_tts_form",
    ]

    for method_name in expected_methods:
        method = getattr(builder, method_name, None)
        assert callable(method), method_name


def test_tts_builder_signature_contracts():
    tts_module = importlib.import_module("yuntai.views.tts")
    builder = tts_module.TTSBuilder

    init_sig = inspect.signature(builder.__init__)
    assert list(init_sig.parameters) == ["self", "view_instance"]

    create_page_sig = inspect.signature(builder.create_page)
    assert list(create_page_sig.parameters) == ["self", "tts_manager"]

    create_card_sig = inspect.signature(builder._create_card)
    assert list(create_card_sig.parameters) == ["self", "corner_radius", "shadow_type"]

    create_button_sig = inspect.signature(builder._create_button)
    assert list(create_button_sig.parameters) == ["self", "text", "style_type", "height"]

    create_form_sig = inspect.signature(builder._create_tts_form)
    assert list(create_form_sig.parameters) == ["self", "parent_layout", "tts_manager"]

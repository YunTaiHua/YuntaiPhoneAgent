import importlib
import inspect


def test_views_module_exports_page_builder_contract():
    views_module = importlib.import_module("yuntai.views")
    pages_module = importlib.import_module("yuntai.views.pages")

    assert "PageBuilder" in views_module.__all__
    assert hasattr(views_module, "PageBuilder")
    assert views_module.PageBuilder is pages_module.PageBuilder


def test_page_builder_methods_are_callable_contracts():
    pages_module = importlib.import_module("yuntai.views.pages")
    page_builder = pages_module.PageBuilder

    expected_methods = [
        "create_dashboard_page",
        "create_connection_page",
        "create_tts_page",
        "create_history_page",
        "create_settings_page",
        "create_dynamic_page",
    ]

    for method_name in expected_methods:
        method = getattr(page_builder, method_name, None)
        assert callable(method), method_name


def test_page_builder_signature_contracts():
    pages_module = importlib.import_module("yuntai.views.pages")
    page_builder = pages_module.PageBuilder

    init_sig = inspect.signature(page_builder.__init__)
    assert list(init_sig.parameters) == ["self", "view_instance"]

    create_tts_sig = inspect.signature(page_builder.create_tts_page)
    assert list(create_tts_sig.parameters) == ["self", "tts_manager"]

    zero_arg_methods = [
        "create_dashboard_page",
        "create_connection_page",
        "create_history_page",
        "create_settings_page",
        "create_dynamic_page",
    ]
    for method_name in zero_arg_methods:
        method_sig = inspect.signature(getattr(page_builder, method_name))
        assert list(method_sig.parameters) == ["self"], method_name

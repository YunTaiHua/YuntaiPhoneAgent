import importlib
import inspect


def test_views_module_exports_connection_builder_contract():
    views_module = importlib.import_module("yuntai.views")
    connection_module = importlib.import_module("yuntai.views.connection")

    assert "ConnectionBuilder" in views_module.__all__
    assert hasattr(views_module, "ConnectionBuilder")
    assert views_module.ConnectionBuilder is connection_module.ConnectionBuilder


def test_connection_builder_methods_are_callable_contracts():
    connection_module = importlib.import_module("yuntai.views.connection")
    builder = connection_module.ConnectionBuilder

    expected_methods = [
        "create_page",
        "_create_card",
        "_create_connection_form",
        "_create_button",
    ]

    for method_name in expected_methods:
        method = getattr(builder, method_name, None)
        assert callable(method), method_name


def test_connection_builder_signature_contracts():
    connection_module = importlib.import_module("yuntai.views.connection")
    builder = connection_module.ConnectionBuilder

    init_sig = inspect.signature(builder.__init__)
    assert list(init_sig.parameters) == ["self", "view_instance"]

    create_page_sig = inspect.signature(builder.create_page)
    assert list(create_page_sig.parameters) == ["self"]

    create_card_sig = inspect.signature(builder._create_card)
    assert list(create_card_sig.parameters) == ["self", "corner_radius", "shadow_type"]

    create_form_sig = inspect.signature(builder._create_connection_form)
    assert list(create_form_sig.parameters) == ["self", "parent_layout"]

    create_button_sig = inspect.signature(builder._create_button)
    assert list(create_button_sig.parameters) == ["self", "text", "style_type"]

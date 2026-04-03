from yuntai.gui.view.navigation import NavigationMixin


def test_navigation_mixin_exports_class_contract():
    assert isinstance(NavigationMixin, type)


def test_navigation_mixin_declares_expected_methods():
    required_methods = [
        "_setup_main_layout",
        "_create_navigation_frame",
        "_create_main_content_frame",
        "_create_status_bar",
        "_highlight_nav_button",
    ]

    for method_name in required_methods:
        method = getattr(NavigationMixin, method_name, None)
        assert callable(method), method_name

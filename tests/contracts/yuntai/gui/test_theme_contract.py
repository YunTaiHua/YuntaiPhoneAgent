import importlib


def test_theme_module_exports_expected_public_api():
    module = importlib.import_module("yuntai.views.theme")

    expected = {
        "ThemeColors",
        "DarkThemeColors",
        "ThemeSpacing",
        "ThemeCorner",
        "ThemeHeight",
        "ThemeFonts",
        "get_theme_colors",
        "apply_light_theme",
        "apply_dark_theme",
        "get_main_stylesheet",
        "get_overlay_stylesheet",
    }

    assert set(module.__all__) == expected
    for name in expected:
        assert hasattr(module, name)


def test_theme_module_callable_contracts():
    module = importlib.import_module("yuntai.views.theme")

    assert callable(module.get_theme_colors)
    assert callable(module.apply_light_theme)
    assert callable(module.apply_dark_theme)
    assert callable(module.get_main_stylesheet)
    assert callable(module.get_overlay_stylesheet)

from types import SimpleNamespace

from yuntai.gui.view import page_manager as mod


def test_page_manager_mixin_show_toast():
    pm = mod.PageManagerMixin.__new__(mod.PageManagerMixin)
    pm.is_dark_theme = False
    pm.toast_widget = SimpleNamespace(show_toast=lambda msg, t, d: None)
    pm.show_toast("test message")


def test_page_manager_mixin_show_page():
    pm = mod.PageManagerMixin.__new__(mod.PageManagerMixin)
    pm.current_page_index = -1
    pm.page_stack = SimpleNamespace(setCurrentIndex=lambda i: None)
    pm.page_initialized = [False] * 6
    pm.page_builder = SimpleNamespace(
        page_initialized=[False] * 6,
        tts_manager=None,
        create_dashboard_page=lambda: None,
        create_connection_page=lambda: None,
        create_tts_page=lambda m: None,
        create_history_page=lambda: None,
        create_dynamic_page=lambda: None,
        create_settings_page=lambda: None,
    )
    pm._highlight_nav_button = lambda i: None
    pm.show_page(0)
    assert pm.current_page_index == 0


def test_page_manager_mixin_create_pages_delegate():
    pm = mod.PageManagerMixin.__new__(mod.PageManagerMixin)
    pm.show_page = lambda i: None
    pm.page_builder = SimpleNamespace(tts_manager=None)
    pm.create_dashboard_page()
    pm.create_connection_page()
    pm.create_tts_page(None)
    pm.create_history_page()
    pm.create_dynamic_page()
    pm.create_settings_page()

import importlib
import sys
import types
from types import SimpleNamespace

from yuntai.core import main_app as main_app_mod
from yuntai.gui.controller import core as controller_core_mod
from yuntai.gui.view import dialogs as dialogs_mod
from yuntai.gui.view import page_manager as page_manager_mod
from yuntai.handlers import system_handler as system_handler_mod


def test_gpt_sovits_custom_init_success_and_import_error(monkeypatch):
    pkg = "yuntai.managers.gpt_sovits_custom"
    dep = "yuntai.managers.gpt_sovits_custom.inference_webui"

    ok_dep = types.ModuleType(dep)
    ok_dep.get_tts_wav = object()
    ok_dep.change_gpt_weights = object()
    ok_dep.change_sovits_weights = object()
    ok_dep.I18nAuto = object()

    monkeypatch.setitem(sys.modules, dep, ok_dep)
    monkeypatch.delitem(sys.modules, pkg, raising=False)
    mod = importlib.import_module(pkg)
    assert mod.get_tts_wav is ok_dep.get_tts_wav
    assert "I18nAuto" in mod.__all__

    bad_dep = types.ModuleType(dep)
    monkeypatch.setitem(sys.modules, dep, bad_dep)
    monkeypatch.delitem(sys.modules, pkg, raising=False)
    mod2 = importlib.import_module(pkg)
    assert mod2.get_tts_wav is None
    assert mod2.change_gpt_weights is None
    assert mod2.change_sovits_weights is None
    assert mod2.I18nAuto is None


def test_main_app_init_registers_controller_and_timer(monkeypatch):
    calls = []

    class _FakeApp:
        _instance = None

        def __init__(self, _argv):
            self.name = None
            self.version = None
            _FakeApp._instance = self

        @classmethod
        def instance(cls):
            return cls._instance

        def setApplicationName(self, v):
            self.name = v

        def setApplicationVersion(self, v):
            self.version = v

    class _FakeController:
        def __init__(self, root, scrcpy):
            self.root = root
            self.scrcpy = scrcpy
            self.view = SimpleNamespace(show=lambda: calls.append("show"))

        def show_dashboard(self):
            calls.append("dashboard")

    fake_registry = SimpleNamespace(register=lambda name, _obj: calls.append(("register", name)))

    monkeypatch.setattr(main_app_mod, "validate_config", lambda: False)
    monkeypatch.setattr(main_app_mod, "print_config_summary", lambda: calls.append("summary"))
    monkeypatch.setattr(main_app_mod, "QApplication", _FakeApp)
    monkeypatch.setattr(main_app_mod, "get_registry", lambda: fake_registry)
    monkeypatch.setattr(main_app_mod.QTimer, "singleShot", lambda ms, cb: calls.append(("timer", ms, cb.__name__)))
    monkeypatch.setattr(main_app_mod.atexit, "register", lambda fn: calls.append(("atexit", fn.__name__)))

    fake_gui_mod = types.ModuleType("yuntai.gui.gui_controller")
    fake_gui_mod.GUIController = _FakeController
    monkeypatch.setitem(sys.modules, "yuntai.gui.gui_controller", fake_gui_mod)

    monkeypatch.setattr(main_app_mod.MainApp, "_register_foundation_services", lambda self, _r: calls.append("f0"))
    monkeypatch.setattr(main_app_mod.MainApp, "_register_business_services", lambda self, _r: calls.append("f12"))

    app = main_app_mod.MainApp()
    assert app.app.name == "Phone Agent"
    assert app.app.version == main_app_mod.APP_VERSION
    assert ("register", "gui_controller") in calls
    assert ("timer", 500, "check_initial_connection") in calls
    assert "show" in calls and "dashboard" in calls


def test_main_app_delegates_and_cleanup_without_hook():
    app = object.__new__(main_app_mod.MainApp)
    called = []
    app.controller = SimpleNamespace(check_initial_connection=lambda: called.append("check"))
    app.check_initial_connection()
    assert called == ["check"]

    app.controller = SimpleNamespace()
    app.cleanup()


def test_page_manager_show_page_invalid_and_delegate_methods(monkeypatch):
    host = page_manager_mod.PageManagerMixin()
    called = []
    host.page_stack = SimpleNamespace(setCurrentIndex=lambda idx: called.append(("set", idx)))
    host._highlight_nav_button = lambda idx: called.append(("hi", idx))
    host._call_page_init_callback = lambda idx: called.append(("init", idx))
    host.current_page_index = 0

    host.show_page(99)
    assert ("set", 99) not in called
    assert host.current_page_index == 99
    assert ("hi", 99) in called and ("init", 99) in called

    class _FakeToast:
        def __init__(self, _parent):
            self.theme = None
            self.shown = None

        def update_theme(self, is_dark):
            self.theme = is_dark

        def show_toast(self, message, msg_type, duration):
            self.shown = (message, msg_type, duration)

    monkeypatch.setattr(page_manager_mod, "ToastWidget", _FakeToast)
    host.is_dark_theme = True
    host._create_toast_widget()
    host.show_toast("m", "warning", 7)
    assert host.toast_widget.theme is True
    assert host.toast_widget.shown == ("m", "warning", 7)

    show_calls = []
    host.show_page = lambda idx: show_calls.append(idx)
    host.page_builder = SimpleNamespace(tts_manager=None)
    tm = object()
    host.create_dashboard_page()
    host.create_connection_page()
    host.create_tts_page(tm)
    host.create_history_page()
    host.create_dynamic_page()
    host.create_settings_page()
    assert show_calls == [0, 1, 2, 3, 4, 5]
    assert host.page_builder.tts_manager is tm


def test_dialogs_file_dialog_component_updates_and_device_callback(monkeypatch):
    host = dialogs_mod.DialogsMixin()
    host.components = {}

    seen = []
    monkeypatch.setattr(
        dialogs_mod.QFileDialog,
        "getOpenFileNames",
        lambda *_a, **_k: (seen.append(_a[3]) or ["a.txt", "b.txt"], "unused"),
    )
    files = host.show_file_upload_dialog()
    assert files == ["a.txt", "b.txt"]
    assert "所有支持的文件" in seen[0]
    assert "所有文件 (*.*)" in seen[0]

    changed = []
    host._device_type_callback = lambda dtype: changed.append(dtype)
    host._on_device_type_change("android")
    assert changed == ["android"]

    class _Comp:
        def __init__(self):
            self.value = 0
            self._text = ""
            self._style = ""

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, _v):
            raise TypeError("setter blocked")

        @property
        def style(self):
            return self._style

        @style.setter
        def style(self, _v):
            raise AttributeError("setter blocked")

        def setText(self, v):
            self._text = v

        def setStyleSheet(self, v):
            self._style = v

        def show(self):
            self.value += 1

        def hide(self):
            self.value -= 1

    comp = _Comp()
    host.components = {"x": comp, "enter_button": comp}
    host.update_component("x", value=2, text="T", style="S")
    assert comp.value == 2
    assert comp._text == "T"
    assert comp._style == "S"
    host.show_enter_button()
    host.hide_enter_button()
    assert comp.value == 2


def test_system_check_dialog_slots_and_format_action_lines():
    dlg = system_handler_mod.SystemCheckDialog.__new__(system_handler_mod.SystemCheckDialog)

    class _Cursor:
        MoveOperation = SimpleNamespace(End=1)

        def __init__(self):
            self.moves = 0

        def movePosition(self, _op):
            self.moves += 1

    class _Text:
        def __init__(self):
            self.lines = []
            self.cursor = _Cursor()

        def append(self, text):
            self.lines.append(text)

        def textCursor(self):
            return self.cursor

        def setTextCursor(self, _cursor):
            return None

    dlg.result_text = _Text()
    dlg.status_label = SimpleNamespace(text="", style="", setText=lambda v: setattr(dlg.status_label, "text", v), setStyleSheet=lambda v: setattr(dlg.status_label, "style", v))
    dlg._on_append_text("ok")
    dlg._on_set_status("s")
    dlg._on_set_status_color("red")
    dlg.scroll_to_bottom()
    assert dlg.result_text.lines == ["ok"]
    assert dlg.status_label.text == "s"
    assert "red" in dlg.status_label.style
    assert dlg.result_text.cursor.moves == 2

    dlg.append_text_signal = SimpleNamespace(emit=lambda v: setattr(dlg, "_emit1", v))
    dlg.set_status_signal = SimpleNamespace(emit=lambda v: setattr(dlg, "_emit2", v))
    dlg.set_status_color_signal = SimpleNamespace(emit=lambda v: setattr(dlg, "_emit3", v))
    dlg.append_text("a")
    dlg.set_status("b")
    dlg.set_status_color("c")
    assert dlg._emit1 == "a" and dlg._emit2 == "b" and dlg._emit3 == "c"

    assert controller_core_mod._format_action_lines("x") == "x"
    assert controller_core_mod._format_action_lines({"a": 1, "b": 2}) == "a: 1\nb: 2"

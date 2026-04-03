from types import SimpleNamespace

from yuntai.core import main_app as main_app_mod
from yuntai.core.registry import ServiceRegistry, get_registry


def test_service_registry_register_get_create_and_has():
    reg = ServiceRegistry()
    reg.register("x", 123)
    assert reg.get("x") == 123
    assert reg.has("x") is True

    reg.register_factory("maker", lambda value="n": {"name": value})
    created = reg.create("maker", value="ok")
    assert created == {"name": "ok"}
    assert reg.has("maker") is True


def test_service_registry_raises_for_missing():
    reg = ServiceRegistry()
    try:
        reg.get("missing")
    except KeyError as exc:
        assert "未注册" in str(exc)
    else:
        assert False

    try:
        reg.create("missing")
    except KeyError as exc:
        assert "未注册" in str(exc)
    else:
        assert False


def test_get_registry_returns_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_main_app_run_and_cleanup_error_branch(monkeypatch):
    app = object.__new__(main_app_mod.MainApp)

    class _App:
        def exec(self):
            raise RuntimeError("boom")

    called = {"cleanup": 0}
    app.app = _App()
    app.controller = SimpleNamespace(cleanup_on_exit=lambda: called.__setitem__("cleanup", called["cleanup"] + 1))

    assert app.run() == 1
    app.cleanup()
    assert called["cleanup"] == 1


def test_main_app_register_layers(monkeypatch):
    app = object.__new__(main_app_mod.MainApp)
    reg_calls = {"register": [], "factory": []}
    registry = SimpleNamespace(
        register=lambda name, obj: reg_calls["register"].append(name),
        register_factory=lambda name, fn: reg_calls["factory"].append(name),
    )

    monkeypatch.setattr("yuntai.services.connection_manager.ConnectionManager", lambda: "cm")
    monkeypatch.setattr("yuntai.services.file_manager.FileManager", lambda: "fm")
    monkeypatch.setattr("yuntai.callbacks.get_callback_manager", lambda: "cb")
    monkeypatch.setattr("yuntai.models.get_chat_model", lambda: "chat")
    monkeypatch.setattr("yuntai.models.get_judgement_model", lambda: "judge")

    app._register_foundation_services(registry)
    app._register_business_services(registry)

    assert "connection_manager" in reg_calls["register"]
    assert "file_manager" in reg_calls["register"]
    assert "callback_manager" in reg_calls["register"]
    assert "chat_model" in reg_calls["factory"]
    assert "judgement_model" in reg_calls["factory"]

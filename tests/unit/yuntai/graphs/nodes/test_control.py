import os
import threading

os.environ.setdefault("ZHIPU_API_KEY", "test-key")


def test_check_continue_stops_on_terminate_flag(monkeypatch):
    from yuntai.graphs.nodes import control

    monkeypatch.setattr(control, "emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(control, "check_terminate", lambda: False)

    result = control.check_continue({"cycle_count": 1, "max_cycles": 5, "terminate_flag": True})

    assert result == {"should_continue": False, "terminate_flag": True}


def test_check_continue_stops_on_max_cycles(monkeypatch):
    from yuntai.graphs.nodes import control

    monkeypatch.setattr(control, "emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(control, "check_terminate", lambda: False)

    result = control.check_continue({"cycle_count": 5, "max_cycles": 5, "terminate_flag": False})

    assert result == {"should_continue": False}


def test_check_continue_returns_true_when_should_continue(monkeypatch):
    from yuntai.graphs.nodes import control

    monkeypatch.setattr(control, "check_terminate", lambda: False)
    result = control.check_continue({"cycle_count": 1, "max_cycles": 5, "terminate_flag": False})
    assert result == {"should_continue": True}


def test_do_wait_sleeps_expected_times(monkeypatch):
    from yuntai.graphs.nodes import control

    sleeps = []
    monkeypatch.setattr(control, "emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(control, "check_terminate", lambda: False)
    monkeypatch.setattr(control.time, "sleep", lambda sec: sleeps.append(sec))

    result = control.do_wait({"wait_seconds": 3, "terminate_flag": False})

    assert result == {}
    assert len(sleeps) >= 1
    assert sum(sleeps) == 3


def test_do_wait_breaks_when_terminated(monkeypatch):
    from yuntai.graphs.nodes import control

    calls = {"n": 0}

    def _check_terminate():
        calls["n"] += 1
        return calls["n"] >= 2

    sleeps = []
    monkeypatch.setattr(control, "emit_agent_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(control, "check_terminate", _check_terminate)
    monkeypatch.setattr(control.time, "sleep", lambda sec: sleeps.append(sec))

    control.do_wait({"wait_seconds": 5, "terminate_flag": False})

    assert sleeps == [1]


def test_check_terminate_uses_global_event(monkeypatch):
    from yuntai.graphs.nodes import control

    event = threading.Event()
    control.set_terminate_event(event)
    assert control.check_terminate() is False
    event.set()
    assert control.check_terminate() is True

from types import SimpleNamespace

from yuntai.graphs.nodes import extract as mod


def test_phone_agent_cache_lru_and_stats(monkeypatch):
    times = iter([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    monkeypatch.setattr(mod.time, "time", lambda: next(times))

    cache = mod.PhoneAgentCache(max_size=2, expire_seconds=100)
    a1 = SimpleNamespace(name="a1")
    a2 = SimpleNamespace(name="a2")
    a3 = SimpleNamespace(name="a3")

    cache.put("d1", a1)
    cache.put("d2", a2)
    assert cache.get("d1") is a1
    cache.put("d3", a3)
    assert cache.get("d2") is None
    assert cache.size() == 2

    stats = cache.get_stats()
    assert stats["size"] == 2
    assert stats["max_size"] == 2


def test_phone_agent_cache_expire_remove_cleanup(monkeypatch):
    now = {"v": 0}
    monkeypatch.setattr(mod.time, "time", lambda: now["v"])
    cache = mod.PhoneAgentCache(max_size=3, expire_seconds=2)
    cache.put("d1", SimpleNamespace())
    cache.put("d2", SimpleNamespace())

    now["v"] = 10
    assert cache.get("d1") is None
    removed = cache.cleanup_expired()
    assert removed >= 1
    assert cache.remove("missing") is False
    cache.clear()
    assert cache.size() == 0


def test_get_phone_agent_uses_cache(monkeypatch):
    created = []

    class _Phone:
        def __init__(self, device_id):
            created.append(device_id)

    monkeypatch.setattr(mod, "PhoneAgent", _Phone)
    mod._cache = mod.PhoneAgentCache(max_size=10, expire_seconds=999)

    a1 = mod._get_phone_agent("dev-x")
    a2 = mod._get_phone_agent("dev-x")
    assert a1 is a2
    assert created == ["dev-x"]


def test_extract_records_terminate_and_failure_and_success(monkeypatch):
    events = []
    monkeypatch.setattr(mod, "emit_agent_event", lambda *args, **kwargs: events.append((args, kwargs)))

    state = {
        "app_name": "qq",
        "chat_object": "alice",
        "device_id": "dev",
        "cycle_count": 0,
        "max_cycles": 3,
        "terminate_flag": False,
    }

    monkeypatch.setattr("yuntai.graphs.nodes.control.check_terminate", lambda: True)
    out = mod.extract_records(state)
    assert out["should_continue"] is False
    assert out["terminate_flag"] is True

    monkeypatch.setattr("yuntai.graphs.nodes.control.check_terminate", lambda: False)
    monkeypatch.setattr(mod, "_get_phone_agent", lambda _device: SimpleNamespace(extract_chat_records=lambda _a, _o: (False, "bad")))
    out2 = mod.extract_records(state)
    assert out2["error"] == "bad"
    assert out2["extracted_records"] == ""

    monkeypatch.setattr(mod, "_get_phone_agent", lambda _device: SimpleNamespace(extract_chat_records=lambda _a, _o: (True, "records")))
    out3 = mod.extract_records(state)
    assert out3["error"] is None
    assert out3["extracted_records"] == "records"

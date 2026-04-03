import json
import subprocess
from types import SimpleNamespace

from yuntai.services.connection_manager import ConnectionManager, sanitize_device_id


def test_sanitize_device_id_length_limit(monkeypatch):
    monkeypatch.setattr("yuntai.services.connection_manager.MAX_DEVICE_ID_LENGTH", 3)
    try:
        sanitize_device_id("abcd")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "长度超过限制" in str(e)


def test_load_and_save_connection_config_branches(tmp_path, monkeypatch):
    cfg_file = tmp_path / "conn.json"
    monkeypatch.setattr("yuntai.services.connection_manager.CONNECTION_CONFIG_FILE", cfg_file)

    m = ConnectionManager()
    cfg = m.load_connection_config()
    assert cfg["connection_type"] == "wireless"

    cfg_file.write_text(json.dumps({"connection_type": "usb"}), encoding="utf-8")
    cfg2 = m.load_connection_config()
    assert cfg2["connection_type"] == "usb"
    assert "wireless_port" in cfg2

    m.save_connection_config({"x": "y"})
    assert json.loads(cfg_file.read_text(encoding="utf-8"))["x"] == "y"

    bad = tmp_path / "bad"
    bad.mkdir(parents=True)
    monkeypatch.setattr("yuntai.services.connection_manager.CONNECTION_CONFIG_FILE", bad)
    m.save_connection_config({"x": "y"})


def test_get_devices_exception_and_harmony_invalid_lines(monkeypatch):
    m = ConnectionManager("android")
    monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert m.get_available_devices() == []

    m2 = ConnectionManager("harmony")
    monkeypatch.setattr(
        "yuntai.services.connection_manager.subprocess.run",
        lambda *a, **k: SimpleNamespace(stdout="ok-id\n bad;id \n", returncode=0),
    )
    assert m2.get_available_devices() == ["ok-id"]


def test_connect_android_usb_and_wireless_branches(monkeypatch):
    m = ConnectionManager("android")
    monkeypatch.setattr(m, "_get_android_devices", lambda: ["d1"])

    ok, dev, msg = m._connect_android_device("d1", "usb", {})
    assert ok is True and dev == "d1"
    ok, dev, msg = m._connect_android_device("d2", "usb", {})
    assert ok is False and dev == ""

    ok, dev, msg = m._connect_android_device("x", "wireless", {"wireless_ip": "bad ip", "wireless_port": "5555"})
    assert ok is False and "IP地址无效" in msg

    monkeypatch.setattr(
        "yuntai.services.connection_manager.subprocess.run",
        lambda *a, **k: SimpleNamespace(stdout="already connected to 1.2.3.4:5555", returncode=0),
    )
    ok, dev, msg = m._connect_android_device("x", "wireless", {"wireless_ip": "1.2.3.4", "wireless_port": "5555"})
    assert ok is True and dev == "1.2.3.4:5555"

    monkeypatch.setattr(
        "yuntai.services.connection_manager.subprocess.run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd=["adb"], timeout=1)),
    )
    ok, dev, msg = m._connect_android_device("x", "wireless", {"wireless_ip": "1.2.3.4", "wireless_port": "5555"})
    assert ok is False and "超时" in msg


def test_connect_harmony_and_adb_connect_windows_branches(monkeypatch):
    m = ConnectionManager("harmony")
    monkeypatch.setattr(m, "_get_harmony_devices", lambda: ["h1"])

    ok, dev, _ = m._connect_harmony_device("h1", "usb", {})
    assert ok is True and dev == "h1"
    ok, dev, _ = m._connect_harmony_device("h2", "usb", {})
    assert ok is False and dev == ""

    monkeypatch.setattr(
        "yuntai.services.connection_manager.subprocess.run",
        lambda *a, **k: SimpleNamespace(stdout="", returncode=0),
    )
    ok, dev, msg = m._connect_harmony_device("x", "wireless", {"wireless_ip": "1.2.3.4", "wireless_port": "5555"})
    assert ok is True and dev == "1.2.3.4:5555"

    monkeypatch.setattr(
        "yuntai.services.connection_manager.subprocess.run",
        lambda *a, **k: SimpleNamespace(stdout="err", returncode=1),
    )
    ok, dev, msg = m._connect_harmony_device("x", "wireless", {"wireless_ip": "1.2.3.4", "wireless_port": "5555"})
    assert ok is False and "HDC连接失败" in msg

    ok, msg = m.adb_connect_windows("bad;id")
    assert ok is False and "无效" in msg

    monkeypatch.setattr(
        "yuntai.services.connection_manager.subprocess.run",
        lambda *a, **k: SimpleNamespace(stdout="already connected", returncode=0),
    )
    ok, msg = m.adb_connect_windows("1.2.3.4:5555")
    assert ok is True

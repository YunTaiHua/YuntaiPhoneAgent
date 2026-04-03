import subprocess
from types import SimpleNamespace

import pytest

from yuntai.services.connection_manager import (
    ConnectionManager,
    build_safe_command,
    sanitize_device_id,
    sanitize_ip_address,
)


def test_sanitize_device_id_valid_and_invalid():
    assert sanitize_device_id(" emulator-5554 ") == "emulator-5554"

    with pytest.raises(ValueError):
        sanitize_device_id("")
    with pytest.raises(ValueError):
        sanitize_device_id("bad;id")


def test_sanitize_ip_address_valid_and_invalid():
    assert sanitize_ip_address("192.168.1.2") == "192.168.1.2"
    assert sanitize_ip_address("192.168.1.2:5555") == "192.168.1.2:5555"

    with pytest.raises(ValueError):
        sanitize_ip_address("")
    with pytest.raises(ValueError):
        sanitize_ip_address("bad ip")


def test_build_safe_command_appends_non_empty_args():
    assert build_safe_command(["adb"], "connect", "1.1.1.1:5555", "") == [
        "adb",
        "connect",
        "1.1.1.1:5555",
    ]


def test_get_android_devices_skips_invalid_ids(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            stdout="List of devices attached\nvalid-1\tdevice\nbad;id\tdevice\n",
            returncode=0,
        )

    monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", fake_run)
    manager = ConnectionManager("android")

    assert manager.get_available_devices() == ["valid-1"]


def test_get_harmony_devices_timeout_returns_empty(monkeypatch):
    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["hdc"], timeout=1)

    monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
    manager = ConnectionManager("harmony")

    assert manager.get_available_devices() == []


def test_connect_to_device_missing_or_invalid_device():
    manager = ConnectionManager()

    ok, device, msg = manager.connect_to_device({"connection_type": "usb", "usb_device_id": ""})
    assert (ok, device) == (False, "")
    assert "未配置设备ID" in msg

    ok, device, msg = manager.connect_to_device({"connection_type": "usb", "usb_device_id": "bad;id"})
    assert (ok, device) == (False, "")
    assert "设备ID无效" in msg


def test_connect_android_wireless_success_and_failure(monkeypatch):
    manager = ConnectionManager("android")

    def run_ok(*args, **kwargs):
        return SimpleNamespace(stdout="connected to 192.168.1.8:5555", returncode=0)

    monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
    ok, device, msg = manager.connect_to_device(
        {
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        }
    )
    assert ok is True
    assert device == "192.168.1.8:5555"
    assert "已连接" in msg

    def run_fail(*args, **kwargs):
        return SimpleNamespace(stdout="failed to connect", returncode=1)

    monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_fail)
    ok, device, msg = manager.connect_to_device(
        {
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        }
    )
    assert ok is False
    assert device == ""
    assert "无线连接失败" in msg


def test_connect_harmony_usb_found_and_not_found(monkeypatch):
    manager = ConnectionManager("harmony")
    monkeypatch.setattr(manager, "_get_harmony_devices", lambda: ["h-001"])

    ok, device, msg = manager.connect_to_device(
        {
            "device_type": "harmony",
            "connection_type": "usb",
            "usb_device_id": "h-001",
        }
    )
    assert ok is True
    assert device == "h-001"
    assert "已连接" in msg

    ok, device, msg = manager.connect_to_device(
        {
            "device_type": "harmony",
            "connection_type": "usb",
            "usb_device_id": "h-404",
        }
    )
    assert ok is False
    assert device == ""
    assert "未找到USB设备" in msg

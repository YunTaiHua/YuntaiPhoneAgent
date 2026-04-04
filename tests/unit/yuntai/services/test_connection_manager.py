import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from yuntai.services.connection_manager import (
    CONNECTION_CONFIG_FILE,
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


class TestConnectionManagerDeepBranches:
    def test_get_android_devices_empty_output(self, monkeypatch):
        def fake_run(*args, **kwargs):
            return SimpleNamespace(stdout="List of devices attached\n", returncode=0)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", fake_run)
        manager = ConnectionManager("android")
        assert manager.get_available_devices() == []

    def test_get_android_devices_exception(self, monkeypatch):
        def raise_error(*args, **kwargs):
            raise RuntimeError("adb crash")
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        manager = ConnectionManager("android")
        assert manager.get_available_devices() == []

    def test_connect_android_usb_success(self, monkeypatch):
        manager = ConnectionManager("android")
        monkeypatch.setattr(manager, "_get_android_devices", lambda: ["dev-001"])
        ok, device, msg = manager.connect_to_device({
            "device_type": "android",
            "connection_type": "usb",
            "usb_device_id": "dev-001",
        })
        assert ok is True
        assert device == "dev-001"

    def test_connect_android_usb_not_found(self, monkeypatch):
        manager = ConnectionManager("android")
        monkeypatch.setattr(manager, "_get_android_devices", lambda: ["other-dev"])
        ok, device, msg = manager.connect_to_device({
            "device_type": "android",
            "connection_type": "usb",
            "usb_device_id": "dev-001",
        })
        assert ok is False
        assert "未找到USB设备" in msg

    def test_connect_harmony_wireless_timeout(self, monkeypatch):
        manager = ConnectionManager("harmony")

        def raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["hdc"], timeout=1)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        ok, device, msg = manager.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.1",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "超时" in msg

    def test_connect_android_device_type_fallback(self, monkeypatch):
        manager = ConnectionManager("android")
        monkeypatch.setattr(manager, "_get_android_devices", lambda: ["dev-001"])
        ok, device, msg = manager.connect_to_device({
            "connection_type": "usb",
            "usb_device_id": "dev-001",
        })
        assert ok is True
        assert device == "dev-001"

    def test_connect_missing_connection_type_defaults_to_wireless(self, monkeypatch):
        manager = ConnectionManager("android")

        def run_ok(*args, **kwargs):
            return SimpleNamespace(stdout="connected to 192.168.1.1:5555", returncode=0)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        ok, device, msg = manager.connect_to_device({
            "device_type": "android",
            "wireless_ip": "192.168.1.1",
            "wireless_port": "5555",
        })
        assert ok is True

    def test_load_connection_config_exception(self, monkeypatch, tmp_path):
        manager = ConnectionManager("android")
        config_file = tmp_path / "config.json"
        monkeypatch.setattr("yuntai.services.connection_manager.CONNECTION_CONFIG_FILE", str(config_file))
        monkeypatch.setattr(Path, "exists", lambda self: True)
        monkeypatch.setattr(Path, "read_text", lambda self, encoding: (_ for _ in ()).throw(RuntimeError("read boom")))
        result = manager.load_connection_config()
        assert "connection_type" in result

    def test_save_connection_config_exception(self, monkeypatch, tmp_path):
        manager = ConnectionManager("android")
        config_file = tmp_path / "config.json"
        monkeypatch.setattr("yuntai.services.connection_manager.CONNECTION_CONFIG_FILE", str(config_file))
        monkeypatch.setattr(Path, "write_text", lambda self, content, encoding: (_ for _ in ()).throw(RuntimeError("write boom")))
        manager.save_connection_config({"test": "value"})

    def test_get_android_devices_timeout(self, monkeypatch):
        manager = ConnectionManager("android")

        def raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["adb"], timeout=1)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        result = manager._get_android_devices()
        assert result == []

    def test_get_harmony_devices_exception(self, monkeypatch):
        manager = ConnectionManager("harmony")

        def raise_error(*args, **kwargs):
            raise RuntimeError("hdc crash")
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        result = manager._get_harmony_devices()
        assert result == []

    def test_connect_android_wireless_already_connected(self, monkeypatch):
        manager = ConnectionManager("android")

        def run_already(*args, **kwargs):
            return SimpleNamespace(stdout="already connected to 192.168.1.8:5555", returncode=0)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_already)
        ok, device, msg = manager.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is True
        assert "已连接" in msg

    def test_connect_android_wireless_exception(self, monkeypatch):
        manager = ConnectionManager("android")

        def raise_error(*args, **kwargs):
            raise RuntimeError("connect boom")
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        ok, device, msg = manager.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "失败" in msg

    def test_connect_android_wireless_invalid_ip(self, monkeypatch):
        manager = ConnectionManager("android")
        ok, device, msg = manager.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "invalid ip",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "无效" in msg

    def test_connect_harmony_wireless_invalid_ip(self, monkeypatch):
        manager = ConnectionManager("harmony")
        ok, device, msg = manager.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "invalid ip",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "无效" in msg

    def test_connect_harmony_wireless_success(self, monkeypatch):
        manager = ConnectionManager("harmony")

        def run_ok(*args, **kwargs):
            return SimpleNamespace(stdout="connect ok", returncode=0)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        ok, device, msg = manager.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is True

    def test_connect_harmony_wireless_fail(self, monkeypatch):
        manager = ConnectionManager("harmony")

        def run_fail(*args, **kwargs):
            return SimpleNamespace(stdout="connect failed", returncode=1)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_fail)
        ok, device, msg = manager.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False

    def test_connect_harmony_wireless_exception(self, monkeypatch):
        manager = ConnectionManager("harmony")

        def raise_error(*args, **kwargs):
            raise RuntimeError("hdc connect boom")
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        ok, device, msg = manager.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "失败" in msg

    def test_adb_connect_windows_success(self, monkeypatch):
        manager = ConnectionManager("android")

        def run_ok(*args, **kwargs):
            return SimpleNamespace(stdout="connected to 192.168.1.8:5555", returncode=0)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        ok, msg = manager.adb_connect_windows("192.168.1.8:5555")
        assert ok is True

    def test_adb_connect_windows_already_connected(self, monkeypatch):
        manager = ConnectionManager("android")

        def run_already(*args, **kwargs):
            return SimpleNamespace(stdout="already connected to 192.168.1.8:5555", returncode=0)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_already)
        ok, msg = manager.adb_connect_windows("192.168.1.8:5555")
        assert ok is True

    def test_adb_connect_windows_fail(self, monkeypatch):
        manager = ConnectionManager("android")

        def run_fail(*args, **kwargs):
            return SimpleNamespace(stdout="connection refused", returncode=1)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_fail)
        ok, msg = manager.adb_connect_windows("192.168.1.8:5555")
        assert ok is False

    def test_adb_connect_windows_timeout(self, monkeypatch):
        manager = ConnectionManager("android")

        def raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["adb"], timeout=1)
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        ok, msg = manager.adb_connect_windows("192.168.1.8:5555")
        assert ok is False
        assert "超时" in msg

    def test_adb_connect_windows_exception(self, monkeypatch):
        manager = ConnectionManager("android")

        def raise_error(*args, **kwargs):
            raise RuntimeError("adb boom")
        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        ok, msg = manager.adb_connect_windows("192.168.1.8:5555")
        assert ok is False
        assert "错误" in msg

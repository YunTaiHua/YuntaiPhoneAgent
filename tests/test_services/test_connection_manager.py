"""
测试 ConnectionManager
"""
import pytest
import os
import json
from unittest.mock import MagicMock, patch, mock_open
import subprocess

from yuntai.services.connection_manager import ConnectionManager


class TestConnectionManager:
    """测试 ConnectionManager"""

    def test_init(self):
        """测试初始化"""
        manager = ConnectionManager()
        
        assert manager is not None

    def test_init_with_device_type(self):
        """测试使用设备类型初始化"""
        manager = ConnectionManager(device_type="android")
        
        assert manager is not None
        assert manager.device_type == "android"

    def test_set_device_type(self):
        """测试设置设备类型"""
        manager = ConnectionManager()
        
        manager.set_device_type("harmony")
        
        assert manager.device_type == "harmony"


class TestConnectionManagerConfig:
    """测试 ConnectionManager 配置"""

    @patch('os.path.exists', return_value=True)
    def test_load_connection_config_with_file(self, mock_exists):
        """测试加载连接配置 - 有配置文件"""
        config_data = {
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "usb_device_id": "",
            "device_type": "android",
            "device_type_display": "Android (ADB)"
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            manager = ConnectionManager()
            config = manager.load_connection_config()
            
            assert isinstance(config, dict)
            assert config["connection_type"] == "wireless"
            assert config["wireless_ip"] == "192.168.1.100"

    @patch('os.path.exists', return_value=False)
    def test_load_connection_config_no_file(self, mock_exists):
        """测试加载连接配置 - 无配置文件"""
        manager = ConnectionManager()
        config = manager.load_connection_config()
        
        assert isinstance(config, dict)
        assert "connection_type" in config
        assert "wireless_ip" in config

    @patch('os.path.exists', return_value=True)
    def test_load_connection_config_partial(self, mock_exists):
        """测试加载连接配置 - 部分配置"""
        partial_config = {"connection_type": "usb"}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(partial_config))):
            manager = ConnectionManager()
            config = manager.load_connection_config()
            
            # 应该填充默认值
            assert "wireless_ip" in config
            assert "wireless_port" in config

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', side_effect=Exception("read error"))
    def test_load_connection_config_error(self, mock_open_file, mock_exists):
        """测试加载连接配置 - 读取错误"""
        manager = ConnectionManager()
        config = manager.load_connection_config()
        
        # 应该返回默认配置
        assert isinstance(config, dict)

    @patch('builtins.open', new_callable=mock_open)
    def test_save_connection_config(self, mock_file):
        """测试保存连接配置"""
        manager = ConnectionManager()
        manager.save_connection_config({"device_id": "test_device"})
        
        # 验证文件被打开
        mock_file.assert_called()

    @patch('builtins.open', side_effect=Exception("write error"))
    def test_save_connection_config_error(self, mock_open_file):
        """测试保存连接配置 - 写入错误"""
        manager = ConnectionManager()
        # 不应该抛出异常
        manager.save_connection_config({"device_id": "test_device"})


class TestConnectionManagerGetDevices:
    """测试 ConnectionManager 获取设备"""

    @patch('subprocess.run')
    def test_get_available_devices_android(self, mock_run):
        """测试获取可用设备 - Android"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\ndevice1\tdevice\ndevice2\tdevice\n"
        )
        
        manager = ConnectionManager(device_type="android")
        devices = manager.get_available_devices()
        
        assert isinstance(devices, list)
        assert "device1" in devices
        assert "device2" in devices

    @patch('subprocess.run')
    def test_get_available_devices_android_empty(self, mock_run):
        """测试获取可用设备 - Android空列表"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\n"
        )
        
        manager = ConnectionManager(device_type="android")
        devices = manager.get_available_devices()
        
        assert devices == []

    @patch('subprocess.run', side_effect=Exception("adb error"))
    def test_get_available_devices_android_error(self, mock_run):
        """测试获取可用设备 - Android错误"""
        manager = ConnectionManager(device_type="android")
        devices = manager.get_available_devices()
        
        assert devices == []

    @patch('subprocess.run')
    def test_get_available_devices_harmony(self, mock_run):
        """测试获取可用设备 - HarmonyOS"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="device1\ndevice2\n"
        )
        
        manager = ConnectionManager(device_type="harmony")
        devices = manager.get_available_devices()
        
        assert isinstance(devices, list)
        assert "device1" in devices
        assert "device2" in devices

    @patch('subprocess.run', side_effect=Exception("hdc error"))
    def test_get_available_devices_harmony_error(self, mock_run):
        """测试获取可用设备 - HarmonyOS错误"""
        manager = ConnectionManager(device_type="harmony")
        devices = manager.get_available_devices()
        
        assert devices == []


class TestConnectionManagerConnect:
    """测试 ConnectionManager 连接"""

    @patch('subprocess.run')
    def test_connect_to_device_no_device_id(self, mock_run):
        """测试连接设备 - 无设备ID"""
        manager = ConnectionManager(device_type="android")
        config = {"connection_type": "usb"}
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False
        assert "未配置设备ID" in message

    @patch('subprocess.run')
    def test_connect_android_usb_device_in_list(self, mock_run):
        """测试连接Android USB设备 - 设备在列表中"""
        # 模拟获取设备列表
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\ndevice1\tdevice\n"
        )
        
        manager = ConnectionManager(device_type="android")
        config = {
            "usb_device_id": "device1",
            "connection_type": "usb"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is True
        assert device_id == "device1"

    @patch('subprocess.run')
    def test_connect_android_usb_device_not_in_list(self, mock_run):
        """测试连接Android USB设备 - 设备不在列表中"""
        # 第一次调用返回设备列表，第二次调用返回连接结果
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="List of devices attached\n"),
            MagicMock(returncode=0, stdout="connected to device1")
        ]
        
        manager = ConnectionManager(device_type="android")
        config = {
            "usb_device_id": "device1",
            "connection_type": "usb"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is True

    @patch('subprocess.run')
    def test_connect_android_usb_error(self, mock_run):
        """测试连接Android USB设备 - 错误"""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="List of devices attached\n"),
            MagicMock(returncode=1, stderr="connection failed")
        ]
        
        manager = ConnectionManager(device_type="android")
        config = {
            "usb_device_id": "device1",
            "connection_type": "usb"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False

    @patch('subprocess.run')
    def test_connect_android_wireless_success(self, mock_run):
        """测试连接Android无线设备 - 成功"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="connected to 192.168.1.100:5555"
        )
        
        manager = ConnectionManager(device_type="android")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is True

    @patch('subprocess.run')
    def test_connect_android_wireless_already_connected(self, mock_run):
        """测试连接Android无线设备 - 已连接"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="already connected to 192.168.1.100:5555"
        )
        
        manager = ConnectionManager(device_type="android")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is True

    @patch('subprocess.run')
    def test_connect_android_wireless_failed(self, mock_run):
        """测试连接Android无线设备 - 失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="connection refused"
        )
        
        manager = ConnectionManager(device_type="android")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False

    @patch('subprocess.run')
    def test_connect_android_wireless_exception(self, mock_run):
        """测试连接Android无线设备 - 异常"""
        mock_run.side_effect = Exception("connection error")
        
        manager = ConnectionManager(device_type="android")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False

    @patch('subprocess.run')
    def test_connect_harmony_usb_device_in_list(self, mock_run):
        """测试连接HarmonyOS USB设备 - 设备在列表中"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="device1\n"
        )
        
        manager = ConnectionManager(device_type="harmony")
        config = {
            "usb_device_id": "device1",
            "connection_type": "usb"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is True

    @patch('subprocess.run')
    def test_connect_harmony_usb_device_not_in_list(self, mock_run):
        """测试连接HarmonyOS USB设备 - 设备不在列表中"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=""
        )
        
        manager = ConnectionManager(device_type="harmony")
        config = {
            "usb_device_id": "device1",
            "connection_type": "usb"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False

    @patch('subprocess.run')
    def test_connect_harmony_wireless_success(self, mock_run):
        """测试连接HarmonyOS无线设备 - 成功"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Connect OK"
        )
        
        manager = ConnectionManager(device_type="harmony")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is True

    @patch('subprocess.run')
    def test_connect_harmony_wireless_failed(self, mock_run):
        """测试连接HarmonyOS无线设备 - 失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="Connect Fail"
        )
        
        manager = ConnectionManager(device_type="harmony")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False

    @patch('subprocess.run')
    def test_connect_harmony_wireless_exception(self, mock_run):
        """测试连接HarmonyOS无线设备 - 异常"""
        mock_run.side_effect = Exception("hdc error")
        
        manager = ConnectionManager(device_type="harmony")
        config = {
            "wireless_ip": "192.168.1.100",
            "wireless_port": "5555",
            "connection_type": "wireless"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        assert success is False


class TestConnectionManagerAdbConnect:
    """测试 ConnectionManager ADB连接"""

    @patch('subprocess.run')
    def test_adb_connect_windows_success(self, mock_run):
        """测试ADB连接 - Windows成功"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="connected to 192.168.1.100:5555"
        )
        
        manager = ConnectionManager(device_type="android")
        success, message = manager.adb_connect_windows("192.168.1.100:5555")
        
        assert success is True
        assert "成功" in message

    @patch('subprocess.run')
    def test_adb_connect_windows_already_connected(self, mock_run):
        """测试ADB连接 - Windows已连接"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="already connected to 192.168.1.100:5555"
        )
        
        manager = ConnectionManager(device_type="android")
        success, message = manager.adb_connect_windows("192.168.1.100:5555")
        
        assert success is True

    @patch('subprocess.run')
    def test_adb_connect_windows_failure(self, mock_run):
        """测试ADB连接失败 - Windows"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="error: cannot connect"
        )
        
        manager = ConnectionManager(device_type="android")
        success, message = manager.adb_connect_windows("invalid_ip")
        
        assert success is False

    @patch('subprocess.run', side_effect=Exception("unknown error"))
    def test_adb_connect_windows_exception(self, mock_run):
        """测试ADB连接异常 - Windows"""
        manager = ConnectionManager(device_type="android")
        success, message = manager.adb_connect_windows("192.168.1.100:5555")
        
        assert success is False
        assert "未知错误" in message

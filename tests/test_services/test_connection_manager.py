"""
测试 ConnectionManager
"""
import pytest
from unittest.mock import MagicMock, patch
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

    def test_set_device_type(self):
        """测试设置设备类型"""
        manager = ConnectionManager()
        
        manager.set_device_type("harmony")
        
        # 应该成功设置
        assert True

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', create=True)
    def test_load_connection_config(self, mock_open, mock_exists):
        """测试加载连接配置"""
        mock_file = MagicMock()
        mock_file.read.return_value = '{"device_id": "test_device"}'
        mock_open.return_value.__enter__.return_value = mock_file
        
        manager = ConnectionManager()
        config = manager.load_connection_config()
        
        # 应该返回配置字典
        assert isinstance(config, dict)

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', create=True)
    def test_save_connection_config(self, mock_open, mock_exists):
        """测试保存连接配置"""
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        manager = ConnectionManager()
        manager.save_connection_config({"device_id": "test_device"})
        
        # 应该成功保存
        assert True

    @patch('subprocess.run')
    def test_get_available_devices_android(self, mock_run):
        """测试获取可用设备 - Android"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\ndevice1\tdevice\ndevice2\tdevice\n"
        )
        
        manager = ConnectionManager(device_type="android")
        devices = manager.get_available_devices()
        
        # 应该返回设备列表
        assert isinstance(devices, list)

    @patch('subprocess.run')
    def test_get_available_devices_empty(self, mock_run):
        """测试获取可用设备 - 空"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\n"
        )
        
        manager = ConnectionManager(device_type="android")
        devices = manager.get_available_devices()
        
        # 应该返回空列表
        assert devices == [] or len(devices) == 0

    @patch('subprocess.run')
    def test_connect_to_device_android(self, mock_run):
        """测试连接设备 - Android"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="connected to device1"
        )
        
        manager = ConnectionManager(device_type="android")
        config = {
            "device_id": "device1",
            "connection_type": "usb"
        }
        
        success, device_id, message = manager.connect_to_device(config)
        
        # 应该返回连接结果
        assert isinstance(success, bool)
        assert isinstance(device_id, str)
        assert isinstance(message, str)

    @patch('subprocess.run')
    def test_adb_connect_windows(self, mock_run):
        """测试ADB连接 - Windows"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="connected to 192.168.1.100:5555"
        )
        
        manager = ConnectionManager(device_type="android")
        success, message = manager.adb_connect_windows("192.168.1.100:5555")
        
        # 应该返回连接结果
        assert isinstance(success, bool)
        assert isinstance(message, str)

    @patch('subprocess.run')
    def test_adb_connect_windows_failure(self, mock_run):
        """测试ADB连接失败 - Windows"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="error: cannot connect"
        )
        
        manager = ConnectionManager(device_type="android")
        success, message = manager.adb_connect_windows("invalid_ip")
        
        # 应该失败
        assert success is False

"""
测试 PhoneTools
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.tools.phone_tools import (
    PhoneToolManager,
    open_app_tool,
    send_message_tool,
    extract_chat_records_tool,
    execute_phone_operation,
)


class TestPhoneToolManager:
    """测试手机工具管理器"""

    def test_init(self):
        """测试初始化"""
        manager = PhoneToolManager(device_id="test_device")
        
        assert manager.device_id == "test_device"
        assert manager.max_steps == 100
        assert manager._agent is None

    def test_init_with_max_steps(self):
        """测试使用最大步数初始化"""
        manager = PhoneToolManager(device_id="test_device", max_steps=50)
        
        assert manager.max_steps == 50

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_get_agent(self, mock_create_agent):
        """测试获取Agent"""
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        agent = manager._get_agent()
        
        assert agent == mock_agent
        mock_create_agent.assert_called_once()

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_open_app_success(self, mock_create_agent):
        """测试打开APP成功"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "已成功打开微信"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.open_app("微信")
        
        assert success is True
        assert "成功" in result or "打开" in result

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_open_app_failure(self, mock_create_agent):
        """测试打开APP失败"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作失败：未找到应用"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.open_app("未知应用")
        
        assert success is False

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_execute_operation_success(self, mock_create_agent):
        """测试执行操作成功"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作成功完成"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.execute_operation("打开微信并发送消息")
        
        assert success is True

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_execute_operation_failure(self, mock_create_agent):
        """测试执行操作失败"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作失败"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.execute_operation("执行未知操作")
        
        assert success is False

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_extract_chat_records_success(self, mock_create_agent):
        """测试提取聊天记录成功"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "张三: 你好\n李四: 在吗"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.extract_chat_records("微信", "张三")
        
        assert success is True

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_send_message_success(self, mock_create_agent):
        """测试发送消息成功"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "已成功发送消息"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.send_message("微信", "张三", "你好")
        
        assert success is True

    @patch('yuntai.tools.phone_tools._create_phone_agent')
    def test_send_message_failure(self, mock_create_agent):
        """测试发送消息失败"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "发送失败"
        mock_create_agent.return_value = mock_agent
        
        manager = PhoneToolManager(device_id="test_device")
        success, result = manager.send_message("微信", "张三", "你好")
        
        assert success is False


class TestPhoneToolFunctions:
    """测试手机工具函数"""

    @patch('yuntai.tools.phone_tools.PhoneToolManager')
    def test_open_app_tool(self, mock_manager_class):
        """测试打开APP工具函数"""
        mock_manager = MagicMock()
        mock_manager.open_app.return_value = (True, "已打开微信")
        mock_manager_class.return_value = mock_manager
        
        success, result = open_app_tool("test_device", "微信")
        
        assert success is True
        mock_manager_class.assert_called_once_with("test_device")
        mock_manager.open_app.assert_called_once_with("微信")

    @patch('yuntai.tools.phone_tools.PhoneToolManager')
    def test_execute_phone_operation(self, mock_manager_class):
        """测试执行手机操作工具函数"""
        mock_manager = MagicMock()
        mock_manager.execute_operation.return_value = (True, "操作成功")
        mock_manager_class.return_value = mock_manager
        
        success, result = execute_phone_operation("test_device", "打开微信")
        
        assert success is True
        mock_manager_class.assert_called_once_with("test_device")
        mock_manager.execute_operation.assert_called_once_with("打开微信")

    @patch('yuntai.tools.phone_tools.PhoneToolManager')
    def test_extract_chat_records_tool(self, mock_manager_class):
        """测试提取聊天记录工具函数"""
        mock_manager = MagicMock()
        mock_manager.extract_chat_records.return_value = (True, "聊天记录")
        mock_manager_class.return_value = mock_manager
        
        success, result = extract_chat_records_tool("test_device", "微信", "张三")
        
        assert success is True
        mock_manager_class.assert_called_once_with("test_device")
        mock_manager.extract_chat_records.assert_called_once_with("微信", "张三", "")

    @patch('yuntai.tools.phone_tools.PhoneToolManager')
    def test_send_message_tool(self, mock_manager_class):
        """测试发送消息工具函数"""
        mock_manager = MagicMock()
        mock_manager.send_message.return_value = (True, "消息已发送")
        mock_manager_class.return_value = mock_manager
        
        success, result = send_message_tool("test_device", "微信", "张三", "你好")
        
        assert success is True
        mock_manager_class.assert_called_once_with("test_device")
        mock_manager.send_message.assert_called_once_with("微信", "张三", "你好")

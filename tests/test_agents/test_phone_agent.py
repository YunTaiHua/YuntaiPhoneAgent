"""
测试 PhoneAgent
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from yuntai.agents.phone_agent import PhoneAgent, PhoneAgentWrapper


class TestPhoneAgentWrapper:
    """测试 PhoneAgentWrapper"""

    def test_init(self):
        """测试初始化"""
        wrapper = PhoneAgentWrapper(device_id="test_device", max_steps=50)
        
        assert wrapper.device_id == "test_device"
        assert wrapper.max_steps == 50
        assert wrapper._agent is None

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_execute_success(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试执行操作成功"""
        # Mock外部PhoneAgent
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "操作成功完成"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.execute("打开微信")
        
        assert success is True
        assert "成功" in result
        mock_setup.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_execute_failure(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试执行操作失败"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "操作失败：未找到应用"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.execute("打开未知应用")
        
        assert success is False
        assert "失败" in result

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_execute_exception(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试执行操作异常"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.side_effect = Exception("设备连接失败")
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.execute("打开微信")
        
        assert success is False
        assert "执行失败" in result

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_open_app(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试打开APP"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "已打开微信"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.open_app("微信")
        
        assert success is True
        mock_agent_instance.run.assert_called_once()

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_extract_chat_records_success(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试提取聊天记录成功"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "张三: 你好\n李四: 在吗"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.extract_chat_records("微信", "张三")
        
        assert success is True
        assert "张三" in result

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_extract_chat_records_failure(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试提取聊天记录失败"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.side_effect = Exception("提取失败")
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.extract_chat_records("微信", "张三")
        
        assert success is False
        assert "提取失败" in result

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_send_message_wechat(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试发送消息 - 微信"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "已成功发送消息"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.send_message("微信", "张三", "你好")
        
        assert success is True
        # 验证任务描述包含微信特定的发送按钮描述
        call_args = mock_agent_instance.run.call_args[0][0]
        assert "微信" in call_args
        assert "张三" in call_args
        assert "你好" in call_args

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_send_message_qq(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试发送消息 - QQ"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "消息已成功发送"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.send_message("QQ", "李四", "测试消息")
        
        assert success is True
        # 验证任务描述包含QQ特定的发送按钮描述
        call_args = mock_agent_instance.run.call_args[0][0]
        assert "QQ" in call_args
        assert "右下角的发送按钮" in call_args

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_send_message_other_app(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试发送消息 - 其他APP"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "发送了消息"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.send_message("抖音", "王五", "测试")
        
        assert success is True

    @patch('yuntai.agents.phone_agent.ExternalPhoneAgent')
    @patch('yuntai.agents.phone_agent.AgentExecutor._setup_stdin_pipe')
    @patch('yuntai.agents.phone_agent.AgentExecutor._cleanup_stdin_pipe')
    def test_send_message_failure(self, mock_cleanup, mock_setup, mock_external_agent):
        """测试发送消息失败"""
        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = "发送失败：网络错误"
        mock_external_agent.return_value = mock_agent_instance
        
        wrapper = PhoneAgentWrapper(device_id="test_device")
        success, result = wrapper.send_message("微信", "张三", "你好")
        
        assert success is False

    def test_reset_agent(self):
        """测试重置Agent"""
        wrapper = PhoneAgentWrapper(device_id="test_device")
        wrapper._agent = MagicMock()
        
        wrapper._reset_agent()
        
        assert wrapper._agent is None


class TestPhoneAgent:
    """测试 PhoneAgent"""

    def test_init(self):
        """测试初始化"""
        agent = PhoneAgent(device_id="test_device")
        
        assert agent.device_id == "test_device"
        assert agent._wrapper is None

    def test_set_device_id(self):
        """测试设置设备ID"""
        agent = PhoneAgent(device_id="old_device")
        agent._wrapper = MagicMock()  # 模拟已创建wrapper
        
        agent.set_device_id("new_device")
        
        assert agent.device_id == "new_device"
        assert agent._wrapper is None  # wrapper应该被重置

    @patch('yuntai.agents.phone_agent.PhoneAgentWrapper')
    def test_get_wrapper(self, mock_wrapper_class):
        """测试获取Wrapper"""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        agent = PhoneAgent(device_id="test_device")
        wrapper = agent._get_wrapper()
        
        assert wrapper == mock_wrapper_instance
        mock_wrapper_class.assert_called_once_with("test_device")

    @patch('yuntai.agents.phone_agent.PhoneAgentWrapper')
    def test_execute_operation(self, mock_wrapper_class):
        """测试执行操作"""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_instance.execute.return_value = (True, "操作成功")
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        agent = PhoneAgent(device_id="test_device")
        success, result = agent.execute_operation("打开微信")
        
        assert success is True
        assert result == "操作成功"
        mock_wrapper_instance.execute.assert_called_once_with("打开微信")

    @patch('yuntai.agents.phone_agent.PhoneAgentWrapper')
    def test_open_app(self, mock_wrapper_class):
        """测试打开APP"""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_instance.open_app.return_value = (True, "已打开")
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        agent = PhoneAgent(device_id="test_device")
        success, result = agent.open_app("微信")
        
        assert success is True
        mock_wrapper_instance.open_app.assert_called_once_with("微信")

    @patch('yuntai.agents.phone_agent.PhoneAgentWrapper')
    def test_extract_chat_records(self, mock_wrapper_class):
        """测试提取聊天记录"""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_instance.extract_chat_records.return_value = (True, "聊天记录")
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        agent = PhoneAgent(device_id="test_device")
        success, result = agent.extract_chat_records("微信", "张三")
        
        assert success is True
        mock_wrapper_instance.extract_chat_records.assert_called_once_with("微信", "张三")

    @patch('yuntai.agents.phone_agent.PhoneAgentWrapper')
    def test_send_message(self, mock_wrapper_class):
        """测试发送消息"""
        mock_wrapper_instance = MagicMock()
        mock_wrapper_instance.send_message.return_value = (True, "已发送")
        mock_wrapper_class.return_value = mock_wrapper_instance
        
        agent = PhoneAgent(device_id="test_device")
        success, result = agent.send_message("微信", "张三", "你好")
        
        assert success is True
        mock_wrapper_instance.send_message.assert_called_once_with("微信", "张三", "你好")

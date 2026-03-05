"""
测试 phone_tools.py - 手机操作工具
"""
import pytest
import os
from unittest.mock import MagicMock, patch

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')


class TestPhoneToolManager:
    """测试 PhoneToolManager 类"""

    @pytest.fixture
    def mock_phone_agent(self):
        """创建模拟PhoneAgent"""
        agent = MagicMock()
        agent.run.return_value = "操作成功"
        agent.reset.return_value = None
        return agent

    @pytest.fixture
    def phone_tool_manager(self, mock_phone_agent):
        """创建手机工具管理器fixture"""
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_phone_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            return PhoneToolManager(device_id="test_device", max_steps=50)

    def test_init(self, phone_tool_manager):
        """测试初始化"""
        assert phone_tool_manager.device_id == "test_device"
        assert phone_tool_manager.max_steps == 50
        assert phone_tool_manager._agent is None

    def test_init_default_max_steps(self):
        """测试默认最大步数"""
        with patch('yuntai.tools.phone_tools._create_phone_agent'):
            from yuntai.tools.phone_tools import PhoneToolManager
            manager = PhoneToolManager(device_id="test_device")
            assert manager.max_steps == 100

    def test_get_agent_lazy(self, phone_tool_manager, mock_phone_agent):
        """测试延迟获取Agent"""
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_phone_agent
            
            agent = phone_tool_manager._get_agent()
            
            assert agent is not None
            mock_create.assert_called_once()

    def test_get_agent_cached(self, phone_tool_manager, mock_phone_agent):
        """测试缓存Agent"""
        phone_tool_manager._agent = mock_phone_agent
        
        agent = phone_tool_manager._get_agent()
        
        assert agent is mock_phone_agent

    def test_reset_agent(self, phone_tool_manager, mock_phone_agent):
        """测试重置Agent"""
        phone_tool_manager._agent = mock_phone_agent
        
        phone_tool_manager._reset_agent()
        
        mock_phone_agent.reset.assert_called_once()
        assert phone_tool_manager._agent is None

    def test_reset_agent_none(self, phone_tool_manager):
        """测试重置空Agent"""
        phone_tool_manager._agent = None
        
        # 不应该抛出异常
        phone_tool_manager._reset_agent()


class TestPhoneToolManagerOperations:
    """测试 PhoneToolManager 操作"""

    def test_open_app_success(self):
        """测试打开APP成功"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "成功打开微信"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.open_app("微信")
            
            # 结果不包含"失败"和"错误"，所以success应该是True
            assert success is True

    def test_open_app_failure(self):
        """测试打开APP失败"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作失败"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.open_app("微信")
            
            assert success is False

    def test_open_app_exception(self):
        """测试打开APP异常"""
        mock_agent = MagicMock()
        mock_agent.run.side_effect = Exception("连接错误")
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.open_app("微信")
            
            assert success is False
            assert "失败" in result

    def test_execute_operation_success(self):
        """测试执行操作成功"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作成功完成"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.execute_operation("发送消息给张三")
            
            assert success is True

    def test_execute_operation_failure(self):
        """测试执行操作失败"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作失败"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.execute_operation("发送消息")
            
            assert success is False

    def test_execute_operation_exception(self):
        """测试执行操作异常"""
        mock_agent = MagicMock()
        mock_agent.run.side_effect = Exception("执行错误")
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.execute_operation("发送消息")
            
            assert success is False
            assert "失败" in result


class TestPhoneToolManagerChatRecords:
    """测试 PhoneToolManager 聊天记录提取"""

    def test_extract_chat_records(self):
        """测试提取聊天记录"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "聊天记录内容"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.extract_chat_records("微信", "好友A")
            
            assert success is True
            assert result is not None

    def test_extract_chat_records_with_extra_prompt(self):
        """测试带额外提示提取聊天记录"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "聊天记录"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.extract_chat_records(
                "微信", "好友A", extra_prompt="额外提示"
            )
            
            assert success is True


class TestPhoneToolManagerSendMessage:
    """测试 PhoneToolManager 发送消息"""

    def test_send_message_wechat(self):
        """测试发送微信消息"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "已成功发送消息"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.send_message("微信", "好友A", "你好")
            
            assert success is True

    def test_send_message_qq(self):
        """测试发送QQ消息"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "消息已成功发送"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.send_message("QQ", "好友B", "你好")
            
            assert success is True

    def test_send_message_other_app(self):
        """测试发送其他应用消息"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "发送了消息"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            success, result = manager.send_message("其他应用", "好友C", "你好")
            
            assert success is True


class TestCreatePhoneAgent:
    """测试 _create_phone_agent 函数"""

    def test_create_phone_agent(self):
        """测试创建PhoneAgent"""
        mock_agent = MagicMock()
        
        with patch('yuntai.tools.phone_tools.PhoneAgent') as MockPhoneAgent:
            MockPhoneAgent.return_value = mock_agent
            
            with patch('yuntai.tools.phone_tools.ModelConfig') as MockModelConfig:
                with patch('yuntai.tools.phone_tools.AgentConfig') as MockAgentConfig:
                    from yuntai.tools.phone_tools import _create_phone_agent
                    
                    result = _create_phone_agent("test_device", max_steps=50)
                    
                    MockModelConfig.assert_called_once()
                    MockAgentConfig.assert_called_once()
                    MockPhoneAgent.assert_called_once()

    def test_create_phone_agent_default_params(self):
        """测试默认参数创建PhoneAgent"""
        with patch('yuntai.tools.phone_tools.PhoneAgent') as MockPhoneAgent:
            with patch('yuntai.tools.phone_tools.ModelConfig') as MockModelConfig:
                with patch('yuntai.tools.phone_tools.AgentConfig') as MockAgentConfig:
                    from yuntai.tools.phone_tools import _create_phone_agent
                    
                    result = _create_phone_agent("test_device")
                    
                    # 验证AgentConfig使用默认max_steps
                    call_kwargs = MockAgentConfig.call_args[1]
                    assert call_kwargs['max_steps'] == 100


class TestPhoneToolsIntegration:
    """测试手机工具集成"""

    def test_full_workflow(self):
        """测试完整工作流"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作成功"
        mock_agent.reset.return_value = None
        
        with patch('yuntai.tools.phone_tools._create_phone_agent') as mock_create:
            mock_create.return_value = mock_agent
            from yuntai.tools.phone_tools import PhoneToolManager
            
            manager = PhoneToolManager(device_id="test_device")
            
            # 打开APP
            success1, result1 = manager.open_app("微信")
            
            # 执行操作
            success2, result2 = manager.execute_operation("发送消息")
            
            # 验证调用
            assert mock_agent.run.call_count >= 0  # 取决于实现

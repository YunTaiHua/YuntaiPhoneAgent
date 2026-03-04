"""
测试 ReplyChain
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.chains.reply_chain import ReplyChain


class TestReplyChain:
    """测试 ReplyChain"""

    def test_init(self):
        """测试初始化"""
        chain = ReplyChain(device_id="test_device")
        
        assert chain.device_id == "test_device"
        assert chain.file_manager is None
        assert chain.tts_manager is None
        assert chain._reply_graph is None

    def test_init_with_managers(self, mock_file_manager, mock_tts_manager):
        """测试使用管理器初始化"""
        chain = ReplyChain(
            device_id="test_device",
            file_manager=mock_file_manager,
            tts_manager=mock_tts_manager
        )
        
        assert chain.file_manager == mock_file_manager
        assert chain.tts_manager == mock_tts_manager

    def test_set_device_id(self):
        """测试设置设备ID"""
        chain = ReplyChain(device_id="old_device")
        
        chain.set_device_id("new_device")
        
        assert chain.device_id == "new_device"
        assert chain._reply_graph is None

    @patch('yuntai.agents.phone_agent.PhoneAgent')
    @patch('yuntai.chains.reply_chain.get_zhipu_client')
    @patch('yuntai.chains.reply_chain.parse_messages')
    @patch('yuntai.chains.reply_chain.generate_reply')
    def test_single_reply_success(
        self, 
        mock_generate_reply, 
        mock_parse_messages, 
        mock_get_client,
        mock_phone_agent_class
    ):
        """测试单次回复成功"""
        # Mock PhoneAgent
        mock_agent = MagicMock()
        mock_agent.extract_chat_records.return_value = (True, "聊天记录")
        mock_agent.send_message.return_value = (True, "消息已发送")
        mock_phone_agent_class.return_value = mock_agent
        
        # Mock parse_messages
        mock_parse_messages.return_value = [
            {"content": "你好", "position": "左侧有头像"},
            {"content": "在吗", "position": "右侧有头像"}
        ]
        
        # Mock generate_reply
        mock_generate_reply.return_value = "好的，明天见！"
        
        chain = ReplyChain(device_id="test_device")
        success, result = chain.single_reply("微信", "张三")
        
        assert success is True

    @patch('yuntai.agents.phone_agent.PhoneAgent')
    def test_single_reply_extract_failure(self, mock_phone_agent_class):
        """测试单次回复 - 提取失败"""
        mock_agent = MagicMock()
        mock_agent.extract_chat_records.return_value = (False, "提取失败")
        mock_phone_agent_class.return_value = mock_agent
        
        chain = ReplyChain(device_id="test_device")
        success, result = chain.single_reply("微信", "张三")
        
        assert success is False
        assert "提取聊天记录失败" in result

    @patch('yuntai.chains.reply_chain.ReplyGraph')
    def test_continuous_reply(self, mock_reply_graph_class):
        """测试持续回复"""
        mock_graph = MagicMock()
        mock_graph.run_continuous_reply.return_value = None
        mock_reply_graph_class.return_value = mock_graph
        
        chain = ReplyChain(device_id="test_device")
        chain.continuous_reply("微信", "张三")
        
        # 应该创建并运行graph
        assert True

    def test_stop(self):
        """测试停止"""
        chain = ReplyChain(device_id="test_device")
        
        # 应该不抛出异常
        chain.stop()

    def test_clear_messages(self):
        """测试清空消息"""
        chain = ReplyChain(device_id="test_device")
        
        # 应该不抛出异常
        chain.clear_messages()

    def test_is_running_false(self):
        """测试是否正在运行 - False"""
        chain = ReplyChain(device_id="test_device")
        
        result = chain.is_running()
        
        assert result is False

    @patch('yuntai.chains.reply_chain.ReplyGraph')
    def test_is_running_true(self, mock_reply_graph_class):
        """测试是否正在运行 - True"""
        mock_graph = MagicMock()
        mock_graph.is_running.return_value = True
        mock_reply_graph_class.return_value = mock_graph
        
        chain = ReplyChain(device_id="test_device")
        # 触发graph创建
        chain._get_graph()
        
        result = chain.is_running()
        
        assert result is True

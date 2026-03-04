"""
测试 Send Node
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.graphs.nodes.send import send_message


class TestSendNode:
    """测试发送节点"""

    @patch('yuntai.graphs.nodes.send._get_phone_agent')
    def test_send_success(self, mock_get_agent):
        """测试发送成功"""
        mock_agent = MagicMock()
        mock_agent.send_message.return_value = (True, "消息已发送")
        mock_get_agent.return_value = mock_agent
        
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "generated_reply": "好的，明天见！",
            "device_id": "test_device"
        }
        
        result = send_message(state)
        
        assert "send_success" in result
        assert result["send_success"] is True

    @patch('yuntai.graphs.nodes.send._get_phone_agent')
    def test_send_failure(self, mock_get_agent):
        """测试发送失败"""
        mock_agent = MagicMock()
        mock_agent.send_message.return_value = (False, "发送失败")
        mock_get_agent.return_value = mock_agent
        
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "generated_reply": "测试消息",
            "device_id": "test_device"
        }
        
        result = send_message(state)
        
        assert "send_success" in result
        assert result["send_success"] is False

    def test_send_missing_reply(self):
        """测试缺少回复内容"""
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "device_id": "test_device"
        }
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            send_message(state)

    def test_send_empty_reply(self):
        """测试空回复"""
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "generated_reply": "",
            "device_id": "test_device"
        }
        
        result = send_message(state)
        
        # 应该返回失败
        assert "send_success" in result
        assert result["send_success"] is False

    @patch('yuntai.graphs.nodes.send._get_phone_agent')
    def test_send_with_terminate_flag(self, mock_get_agent):
        """测试带终止标志的发送"""
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "generated_reply": "测试消息",
            "device_id": "test_device",
            "terminate_flag": True
        }
        
        result = send_message(state)
        
        # 应该返回失败
        assert "send_success" in result
        assert result["send_success"] is False

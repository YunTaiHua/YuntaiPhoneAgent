"""
测试 Reply Node
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.graphs.nodes.reply import generate_reply


class TestReplyNode:
    """测试回复生成节点"""

    @patch('yuntai.graphs.nodes.reply.get_zhipu_client')
    def test_reply_success(self, mock_get_client):
        """测试生成回复成功"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="好的，明天见！"))]
        )
        mock_get_client.return_value = mock_client
        
        state = {
            "latest_message": "你好",
            "current_other_messages": ["在吗", "你好"],
            "last_sent_reply": ""
        }
        
        result = generate_reply(state)
        
        assert "generated_reply" in result
        assert result["generated_reply"] is not None

    @patch('yuntai.graphs.nodes.reply.get_zhipu_client')
    def test_reply_with_context(self, mock_get_client):
        """测试带上下文生成回复"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="收到，谢谢！"))]
        )
        mock_get_client.return_value = mock_client
        
        state = {
            "latest_message": "文件已发送",
            "current_other_messages": ["收到", "文件已发送"],
            "last_sent_reply": ""
        }
        
        result = generate_reply(state)
        
        assert "generated_reply" in result

    def test_reply_missing_latest_message(self):
        """测试缺少最新消息"""
        state = {
            "latest_message": "",
            "current_other_messages": [],
            "last_sent_reply": ""
        }
        
        result = generate_reply(state)
        
        # 应该返回空回复
        assert "generated_reply" in result
        assert result["generated_reply"] == ""

    def test_reply_empty_messages(self):
        """测试空消息列表"""
        state = {
            "latest_message": "测",
            "current_other_messages": [],
            "last_sent_reply": ""
        }
        
        result = generate_reply(state)
        
        # 消息太短应该返回空回复
        assert "generated_reply" in result

    @patch('yuntai.graphs.nodes.reply.get_zhipu_client')
    def test_reply_with_model_error(self, mock_get_client):
        """测试模型调用错误"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API调用失败")
        mock_get_client.return_value = mock_client
        
        state = {
            "latest_message": "你好，这是一条测试消息",
            "current_other_messages": ["测试"],
            "last_sent_reply": ""
        }
        
        result = generate_reply(state)
        
        # 应该处理错误并返回空回复
        assert "generated_reply" in result
        assert result["generated_reply"] == ""

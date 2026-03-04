"""
测试 Parse Node
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.graphs.nodes.parse import parse_messages


class TestParseNode:
    """测试解析节点"""

    @patch('yuntai.graphs.nodes.parse.get_zhipu_client')
    def test_parse_success(self, mock_get_client):
        """测试解析成功"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='{"messages": [{"content": "你好", "position": "左侧有头像", "color": "白色"}]}'
                )
            )]
        )
        mock_get_client.return_value = mock_client
        
        state = {
            "extracted_records": "张三: 你好\n李四: 在吗\n张三: 明天见"
        }
        
        result = parse_messages(state)
        
        assert "parsed_messages" in result

    def test_parse_empty_records(self):
        """测试解析空记录"""
        state = {
            "extracted_records": ""
        }
        
        result = parse_messages(state)
        
        # 应该返回空列表
        assert "parsed_messages" in result

    @patch('yuntai.graphs.nodes.parse.get_zhipu_client')
    def test_parse_with_timestamps(self, mock_get_client):
        """测试解析带时间戳的记录"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='{"messages": [{"content": "你好", "position": "左侧有头像", "color": "白色"}]}'
                )
            )]
        )
        mock_get_client.return_value = mock_client
        
        state = {
            "extracted_records": "张三 10:30: 你好\n李四 10:31: 在吗"
        }
        
        result = parse_messages(state)
        
        assert "parsed_messages" in result

    def test_parse_missing_records(self):
        """测试缺少聊天记录"""
        state = {}
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            parse_messages(state)

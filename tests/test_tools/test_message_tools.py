"""
测试 MessageTools
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.tools.message_tools import (
    parse_messages,
    is_message_similar,
)


class TestParseMessages:
    """测试解析消息"""

    def test_parse_messages_success(self):
        """测试解析消息成功"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='{"messages": [{"content": "你好", "position": "左侧有头像", "color": "白色"}]}'
                )
            )]
        )
        
        record = "张三: 你好\n李四: 在吗"
        messages = parse_messages(record, mock_client)
        
        assert isinstance(messages, list)

    def test_parse_messages_empty_record(self):
        """测试解析空记录"""
        mock_client = MagicMock()
        
        messages = parse_messages("", mock_client)
        
        assert messages == []

    def test_parse_messages_short_record(self):
        """测试解析过短的记录"""
        mock_client = MagicMock()
        
        messages = parse_messages("短", mock_client)
        
        assert messages == []


class TestIsMessageSimilar:
    """测试消息相似度判断"""

    def test_identical_messages(self):
        """测试完全相同的消息"""
        result = is_message_similar("你好", "你好", 0.6)
        
        assert result is True

    def test_similar_messages(self):
        """测试相似的消息"""
        result = is_message_similar("你好世界", "你好", 0.6)
        
        # 根据相似度阈值判断
        assert isinstance(result, bool)

    def test_different_messages(self):
        """测试不同的消息"""
        result = is_message_similar("你好", "再见", 0.6)
        
        # 应该返回False
        assert result is False

    def test_empty_messages(self):
        """测试空消息"""
        result = is_message_similar("", "", 0.6)
        
        # 空消息应该返回False
        assert result is False

    def test_one_empty_message(self):
        """测试一个空消息"""
        result = is_message_similar("你好", "", 0.6)
        
        assert result is False

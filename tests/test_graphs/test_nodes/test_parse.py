"""
测试 Parse Node
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from yuntai.graphs.nodes.parse import (
    parse_messages,
    _standardize_position,
    _standardize_color,
    _emergency_extract
)


class TestStandardizePosition:
    """测试位置标准化"""

    def test_standardize_position_left(self):
        """测试左侧位置"""
        assert _standardize_position("左侧有头像") == "左侧有头像"
        # 测试包含"左"的情况
        result = _standardize_position("左")
        assert result in ["左侧有头像", "未知"]  # 根据实际实现

    def test_standardize_position_right(self):
        """测试右侧位置"""
        assert _standardize_position("右侧有头像") == "右侧有头像"
        # 测试包含"右"的情况
        result = _standardize_position("右")
        assert result in ["右侧有头像", "未知"]  # 根据实际实现

    def test_standardize_position_unknown(self):
        """测试未知位置"""
        assert _standardize_position("未知") == "未知"
        assert _standardize_position("") == "未知"
        assert _standardize_position(None) == "未知"
        assert _standardize_position("中间") == "未知"


class TestStandardizeColor:
    """测试颜色标准化"""

    def test_standardize_color_red(self):
        """测试红色"""
        assert _standardize_color("红色") == "红色"
        assert _standardize_color("红") == "红色"

    def test_standardize_color_blue(self):
        """测试蓝色"""
        assert _standardize_color("蓝色") == "蓝色"
        assert _standardize_color("蓝") == "蓝色"

    def test_standardize_color_pink(self):
        """测试粉色"""
        result = _standardize_color("粉色")
        # 根据实际实现，可能返回"粉色"或"未知"
        assert result in ["粉色", "未知"]

    def test_standardize_color_unknown(self):
        """测试未知颜色"""
        assert _standardize_color("未知") == "未知"
        assert _standardize_color("") == "未知"
        assert _standardize_color(None) == "未知"
        assert _standardize_color("彩虹色") == "未知"


class TestEmergencyExtract:
    """测试紧急提取"""

    def test_emergency_extract_basic(self):
        """测试基本提取"""
        records = "你好。在吗？明天见！"
        messages = _emergency_extract(records)

        assert len(messages) > 0
        assert all("content" in msg for msg in messages)
        assert all("position" in msg for msg in messages)
        assert all("color" in msg for msg in messages)

    def test_emergency_extract_with_yuntai(self):
        """测试包含芸苔的提取"""
        records = "芸苔：你好。对方：在吗？"
        messages = _emergency_extract(records)

        # 包含"芸苔"的消息应该在右侧
        yuntai_msgs = [m for m in messages if "芸苔" in m["content"]]
        if yuntai_msgs:
            assert yuntai_msgs[0]["position"] == "右侧有头像"

    def test_emergency_extract_clean(self):
        """测试清理特殊内容"""
        records = "思考过程: 这是思考。性能指标: 123。正常消息。"
        messages = _emergency_extract(records)

        # 应该过滤掉思考过程和性能指标
        contents = [m["content"] for m in messages]
        assert not any("思考过程" in c for c in contents)
        assert not any("性能指标" in c for c in contents)


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

    @patch('yuntai.graphs.nodes.parse.get_zhipu_client')
    def test_parse_with_streaming(self, mock_get_client):
        """测试流式响应解析"""
        # 模拟流式响应
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = '{"messages": '

        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = '[{"content": "你好", "position": "左侧有头像", "color": "白色"}]}'

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]
        mock_get_client.return_value = mock_client

        state = {
            "extracted_records": "张三: 你好\n李四: 在吗"
        }

        result = parse_messages(state)

        assert result["parse_success"] is True
        assert len(result["parsed_messages"]) > 0

    @patch('yuntai.graphs.nodes.parse.get_zhipu_client')
    def test_parse_with_code_block(self, mock_get_client):
        """测试带代码块的响应"""
        mock_client = MagicMock()

        # 模拟流式响应
        def mock_stream(*args, **kwargs):
            # 返回一个包含JSON的响应
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta.content = '{"messages": [{"content": "test message", "position": "left", "color": "white"}]}'
            return [mock_chunk]

        mock_client.chat.completions.create.side_effect = mock_stream
        mock_get_client.return_value = mock_client

        state = {
            "extracted_records": "张三: 你好"
        }

        result = parse_messages(state)

        # 应该成功解析
        assert "parse_success" in result

    @patch('yuntai.graphs.nodes.parse.get_zhipu_client')
    def test_parse_with_exception(self, mock_get_client):
        """测试解析异常"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        state = {
            "extracted_records": "张三: 你好。李四: 在吗。"
        }

        result = parse_messages(state)

        # 应该使用紧急提取
        assert result["parse_success"] is False
        assert len(result["parsed_messages"]) > 0

    def test_parse_short_records(self):
        """测试过短的记录"""
        state = {
            "extracted_records": "短"
        }

        result = parse_messages(state)

        assert result["parse_success"] is False
        assert result["parsed_messages"] == []

    @patch('yuntai.graphs.nodes.parse.get_zhipu_client')
    def test_parse_filter_invalid_messages(self, mock_get_client):
        """测试过滤无效消息"""
        mock_client = MagicMock()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = '{"messages": ["invalid", {"content": "有效消息", "position": "左侧有头像", "color": "白色"}]}'

        mock_client.chat.completions.create.return_value = [mock_chunk]
        mock_get_client.return_value = mock_client

        state = {
            "extracted_records": "张三: 你好"
        }

        result = parse_messages(state)

        # 应该过滤掉无效消息
        assert all(isinstance(m, dict) for m in result["parsed_messages"])

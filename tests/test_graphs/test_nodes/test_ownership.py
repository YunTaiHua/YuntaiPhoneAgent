"""
测试 Ownership Node
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.graphs.nodes.ownership import determine_ownership


class TestOwnershipNode:
    """测试归属判断节点"""

    def test_ownership_with_messages(self):
        """测试根据消息判断归属"""
        state = {
            "parsed_messages": [
                {"content": "你好", "position": "左侧有头像", "color": "白色"},
                {"content": "在吗", "position": "右侧有头像", "color": "绿色"},
            ],
            "other_messages": ["你好"],
            "my_messages": ["在吗"]
        }
        
        result = determine_ownership(state)
        
        assert "current_other_messages" in result
        assert "current_my_messages" in result

    def test_ownership_empty_messages(self):
        """测试空消息列表"""
        state = {
            "parsed_messages": [],
            "other_messages": [],
            "my_messages": []
        }
        
        result = determine_ownership(state)
        
        # 应该返回空结果
        assert "current_other_messages" in result
        assert "current_my_messages" in result
        assert result["current_other_messages"] == []
        assert result["current_my_messages"] == []

    def test_ownership_missing_parsed_messages(self):
        """测试缺少解析后的消息"""
        state = {
            "other_messages": [],
            "my_messages": []
        }
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            determine_ownership(state)

    def test_ownership_with_known_messages(self):
        """测试带已知消息的归属判断"""
        state = {
            "parsed_messages": [
                {"content": "你好世界", "position": "左侧有头像", "color": "白色"},
            ],
            "other_messages": ["你好"],
            "my_messages": []
        }
        
        result = determine_ownership(state)
        
        # 应该识别为对方消息（相似）
        assert "current_other_messages" in result

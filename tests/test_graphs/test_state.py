"""
测试 yuntai.graphs.state 模块
"""
import pytest

from yuntai.graphs.state import ReplyState, ReplyStateBuilder, merge_lists


class TestMergeLists:
    """测试列表合并函数"""
    
    def test_merge_empty_lists(self):
        """测试空列表合并"""
        result = merge_lists([], [])
        assert result == []
    
    def test_merge_with_new_items(self):
        """测试添加新元素"""
        result = merge_lists(["a", "b"], ["c"])
        assert result == ["a", "b", "c"]
    
    def test_merge_with_duplicates(self):
        """测试合并重复元素（应去重）"""
        result = merge_lists(["a", "b"], ["b", "c"])
        assert result == ["a", "b", "c"]
    
    def test_merge_no_duplicates(self):
        """测试无重复时正常追加"""
        result = merge_lists(["a"], ["b", "c"])
        assert result == ["a", "b", "c"]


class TestReplyStateBuilder:
    """测试状态构建器"""
    
    def test_create_default_state(self, mock_env_vars):
        """测试创建默认状态"""
        state = ReplyStateBuilder.create(
            app_name="微信",
            chat_object="张三"
        )
        
        assert state["app_name"] == "微信"
        assert state["chat_object"] == "张三"
        assert state["device_id"] == ""
        assert state["cycle_count"] == 0
        assert state["max_cycles"] == 30
        assert state["should_continue"] is True
        assert state["terminate_flag"] is False
        assert state["extracted_records"] == ""
        assert state["parse_success"] is False
        assert state["parsed_messages"] == []
        assert state["other_messages"] == []
        assert state["my_messages"] == []
        assert state["current_other_messages"] == []
        assert state["current_my_messages"] == []
        assert state["latest_message"] == ""
        assert state["previous_latest_message"] == ""
        assert state["is_new_message"] is False
        assert state["generated_reply"] == ""
        assert state["send_success"] is False
        assert state["last_sent_reply"] == ""
        assert state["error"] is None
        assert state["retry_count"] == 0
        assert state["wait_seconds"] == 1
        assert state["result_message"] == ""
        assert state["seen_other_messages"] == []
    
    def test_create_with_custom_params(self, mock_env_vars):
        """测试自定义参数创建状态"""
        state = ReplyStateBuilder.create(
            app_name="QQ",
            chat_object="李四",
            device_id="device123",
            max_cycles=50
        )
        
        assert state["app_name"] == "QQ"
        assert state["chat_object"] == "李四"
        assert state["device_id"] == "device123"
        assert state["max_cycles"] == 50
    
    def test_state_is_typed_dict(self, mock_env_vars):
        """测试状态是TypedDict类型"""
        state = ReplyStateBuilder.create(
            app_name="微信",
            chat_object="王五"
        )
        
        assert isinstance(state, dict)
        assert "app_name" in state
        assert "chat_object" in state


class TestReplyStateFields:
    """测试状态字段"""
    
    def test_state_has_required_fields(self, mock_env_vars):
        """测试状态包含所有必需字段"""
        state = ReplyStateBuilder.create(
            app_name="微信",
            chat_object="张三"
        )
        
        required_fields = [
            "app_name", "chat_object", "device_id",
            "cycle_count", "max_cycles", "should_continue", "terminate_flag",
            "extracted_records", "parse_success", "parsed_messages",
            "other_messages", "my_messages", "current_other_messages", "current_my_messages",
            "latest_message", "previous_latest_message", "is_new_message",
            "generated_reply", "send_success", "last_sent_reply",
            "error", "retry_count", "wait_seconds", "result_message",
            "seen_other_messages"
        ]
        
        for field in required_fields:
            assert field in state, f"Missing field: {field}"

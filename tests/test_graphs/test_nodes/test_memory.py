"""
测试 Memory Node
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.graphs.nodes import memory


class TestMemoryNode:
    """测试记忆更新节点"""

    def test_set_managers(self):
        """测试设置管理器"""
        mock_fm = MagicMock()
        
        memory.set_managers(file_manager=mock_fm)
        
        # 应该成功设置
        assert memory._file_manager == mock_fm

    def test_memory_update_success(self):
        """测试记忆更新成功"""
        # 设置file_manager
        mock_fm = MagicMock()
        mock_fm.save_conversation_history.return_value = None
        memory.set_managers(file_manager=mock_fm)
        
        from yuntai.graphs.nodes.memory import update_memory
        
        state = {
            "send_success": True,
            "generated_reply": "好的，明天见！",
            "latest_message": "你好",
            "current_other_messages": ["你好"],
            "current_my_messages": [],
            "app_name": "微信",
            "chat_object": "张三",
            "cycle_count": 1
        }
        
        result = update_memory(state)
        
        assert "last_sent_reply" in result
        assert result["last_sent_reply"] == "好的，明天见！"

    def test_memory_update_not_sent(self):
        """测试记忆更新 - 未发送"""
        from yuntai.graphs.nodes.memory import update_memory
        
        state = {
            "send_success": False,
            "generated_reply": "测试回复"
        }
        
        result = update_memory(state)
        
        # 应该返回空字典
        assert result == {}

    def test_memory_missing_fields(self):
        """测试缺少字段"""
        from yuntai.graphs.nodes.memory import update_memory
        
        state = {
            "send_success": True
        }
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            update_memory(state)

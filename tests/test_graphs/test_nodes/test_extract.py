"""
测试 Extract Node
"""
import pytest
from unittest.mock import MagicMock, patch

from yuntai.graphs.nodes.extract import extract_records, _get_phone_agent


class TestGetPhoneAgent:
    """测试获取 PhoneAgent"""

    def test_get_phone_agent_new(self):
        """测试创建新的 PhoneAgent"""
        # 清空缓存
        import yuntai.graphs.nodes.extract as extract_module
        extract_module._phone_agent_cache = {}

        with patch('yuntai.graphs.nodes.extract.PhoneAgent') as MockPhoneAgent:
            mock_agent = MagicMock()
            MockPhoneAgent.return_value = mock_agent

            agent = _get_phone_agent("device1")

            assert agent == mock_agent
            MockPhoneAgent.assert_called_once_with("device1")

    def test_get_phone_agent_cached(self):
        """测试使用缓存的 PhoneAgent"""
        import yuntai.graphs.nodes.extract as extract_module
        extract_module._phone_agent_cache = {}

        with patch('yuntai.graphs.nodes.extract.PhoneAgent') as MockPhoneAgent:
            mock_agent = MagicMock()
            MockPhoneAgent.return_value = mock_agent

            agent1 = _get_phone_agent("device1")
            agent2 = _get_phone_agent("device1")

            # 应该只创建一次
            assert MockPhoneAgent.call_count == 1
            assert agent1 == agent2


class TestExtractNode:
    """测试提取节点"""

    @patch('yuntai.graphs.nodes.extract._get_phone_agent')
    def test_extract_success(self, mock_get_agent):
        """测试提取成功"""
        mock_agent = MagicMock()
        mock_agent.extract_chat_records.return_value = (
            True,
            "张三: 你好\n李四: 在吗"
        )
        mock_get_agent.return_value = mock_agent
        
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "device_id": "test_device",
            "cycle_count": 0,
            "max_cycles": 10
        }
        
        result = extract_records(state)
        
        assert "extracted_records" in result
        assert result["extracted_records"] is not None

    @patch('yuntai.graphs.nodes.extract._get_phone_agent')
    def test_extract_failure(self, mock_get_agent):
        """测试提取失败"""
        mock_agent = MagicMock()
        mock_agent.extract_chat_records.return_value = (False, "提取失败")
        mock_get_agent.return_value = mock_agent
        
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "device_id": "test_device",
            "cycle_count": 0,
            "max_cycles": 10
        }
        
        result = extract_records(state)
        
        # 应该处理失败情况
        assert "extracted_records" in result

    def test_extract_missing_device_id(self):
        """测试缺少设备ID"""
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "cycle_count": 0,
            "max_cycles": 10
        }
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            extract_records(state)

    def test_extract_missing_app_name(self):
        """测试缺少APP名称"""
        state = {
            "chat_object": "张三",
            "device_id": "test_device",
            "cycle_count": 0,
            "max_cycles": 10
        }
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            extract_records(state)

    def test_extract_missing_chat_object(self):
        """测试缺少聊天对象"""
        state = {
            "app_name": "微信",
            "device_id": "test_device",
            "cycle_count": 0,
            "max_cycles": 10
        }
        
        # 应该抛出KeyError
        with pytest.raises(KeyError):
            extract_records(state)

    @patch('yuntai.graphs.nodes.extract._get_phone_agent')
    def test_extract_with_terminate_flag(self, mock_get_agent):
        """测试带终止标志的提取"""
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "device_id": "test_device",
            "cycle_count": 0,
            "max_cycles": 10,
            "terminate_flag": True
        }

        result = extract_records(state)

        # 应该返回终止标志
        assert result.get("terminate_flag") is True
        assert result.get("should_continue") is False

    @patch('yuntai.graphs.nodes.extract._get_phone_agent')
    def test_extract_with_terminate_signal(self, mock_get_agent):
        """测试带终止信号的提取"""
        # 直接设置 terminate_flag
        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "device_id": "test_device",
            "cycle_count": 0,
            "max_cycles": 10,
            "terminate_flag": True
        }

        result = extract_records(state)

        # 应该返回终止标志
        assert result.get("terminate_flag") is True
        assert result.get("should_continue") is False

    @patch('yuntai.graphs.nodes.extract._get_phone_agent')
    def test_extract_cycle_count_increment(self, mock_get_agent):
        """测试循环计数增加"""
        mock_agent = MagicMock()
        mock_agent.extract_chat_records.return_value = (True, "records")
        mock_get_agent.return_value = mock_agent

        state = {
            "app_name": "微信",
            "chat_object": "张三",
            "device_id": "test_device",
            "cycle_count": 5,
            "max_cycles": 10
        }

        result = extract_records(state)

        assert result["cycle_count"] == 6

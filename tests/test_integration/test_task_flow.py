"""
集成测试 - 简化版
测试核心功能的集成
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from yuntai.agents.judgement_agent import JudgementAgent
from yuntai.prompts import (
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
)


class TestJudgementIntegration:
    """测试判断Agent集成"""

    @patch('yuntai.agents.judgement_agent.get_judgement_model')
    def test_judgement_to_free_chat(self, mock_get_model):
        """测试判断为自由聊天"""
        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(
            content=json.dumps({
                "task_type": TASK_TYPE_FREE_CHAT,
                "target_app": "",
                "target_object": "",
                "is_auto": False,
                "specific_content": ""
            })
        )
        mock_get_model.return_value = mock_model
        
        agent = JudgementAgent()
        result = agent.judge("今天天气怎么样？")
        
        assert result.task_type == TASK_TYPE_FREE_CHAT

    @patch('yuntai.agents.judgement_agent.get_judgement_model')
    def test_judgement_to_basic_operation(self, mock_get_model):
        """测试判断为基础操作"""
        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(
            content=json.dumps({
                "task_type": TASK_TYPE_BASIC_OPERATION,
                "target_app": "微信",
                "target_object": "",
                "is_auto": False,
                "specific_content": ""
            })
        )
        mock_get_model.return_value = mock_model
        
        agent = JudgementAgent()
        result = agent.judge("打开微信")
        
        assert result.task_type == TASK_TYPE_BASIC_OPERATION
        assert result.target_app == "微信"

    @patch('yuntai.agents.judgement_agent.get_judgement_model')
    def test_judgement_to_single_reply(self, mock_get_model):
        """测试判断为单次回复"""
        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(
            content=json.dumps({
                "task_type": TASK_TYPE_SINGLE_REPLY,
                "target_app": "微信",
                "target_object": "张三",
                "is_auto": False,
                "specific_content": ""
            })
        )
        mock_get_model.return_value = mock_model
        
        agent = JudgementAgent()
        result = agent.judge("给微信的张三发消息")
        
        assert result.task_type == TASK_TYPE_SINGLE_REPLY
        assert result.target_app == "微信"
        assert result.target_object == "张三"


class TestFallbackLogic:
    """测试后备逻辑"""

    @patch('yuntai.agents.judgement_agent.get_judgement_model')
    def test_fallback_on_error(self, mock_get_model):
        """测试错误时的后备逻辑"""
        mock_model = MagicMock()
        mock_model.invoke.side_effect = Exception("API调用失败")
        mock_get_model.return_value = mock_model
        
        agent = JudgementAgent()
        result = agent.judge("打开微信")
        
        # 应该使用fallback逻辑
        assert result.task_type == TASK_TYPE_BASIC_OPERATION

    @patch('yuntai.agents.judgement_agent.get_judgement_model')
    def test_fallback_on_invalid_json(self, mock_get_model):
        """测试无效JSON时的后备逻辑"""
        mock_model = MagicMock()
        mock_model.invoke.return_value = MagicMock(
            content="这不是有效的JSON"
        )
        mock_get_model.return_value = mock_model
        
        agent = JudgementAgent()
        result = agent.judge("打开微信")
        
        # 应该使用fallback逻辑
        assert result.task_type == TASK_TYPE_BASIC_OPERATION


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_input(self):
        """测试空输入"""
        agent = JudgementAgent()
        result = agent.judge("")
        
        # 应该返回自由聊天
        assert result.task_type == TASK_TYPE_FREE_CHAT

    def test_whitespace_input(self):
        """测试空白字符输入"""
        agent = JudgementAgent()
        result = agent.judge("   \n\t  ")
        
        # 应该返回自由聊天
        assert result.task_type == TASK_TYPE_FREE_CHAT

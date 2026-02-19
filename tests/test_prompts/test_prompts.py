"""
提示词模块测试
测试 yuntai.prompts 模块
"""
import pytest


class TestChatPrompts:
    """测试聊天提示词"""
    
    def test_chat_system_prompt_exists(self, mock_env_vars):
        """测试聊天系统提示词存在"""
        from yuntai.prompts import CHAT_SYSTEM_PROMPT
        
        assert CHAT_SYSTEM_PROMPT is not None
        assert len(CHAT_SYSTEM_PROMPT) > 0
    
    def test_chat_system_prompt_contains_role(self, mock_env_vars):
        """测试系统提示词包含角色设定"""
        from yuntai.prompts import CHAT_SYSTEM_PROMPT
        
        assert "小芸" in CHAT_SYSTEM_PROMPT
        assert "助手" in CHAT_SYSTEM_PROMPT
    
    def test_chat_system_prompt_contains_rules(self, mock_env_vars):
        """测试系统提示词包含规则"""
        from yuntai.prompts import CHAT_SYSTEM_PROMPT
        
        assert "时间" in CHAT_SYSTEM_PROMPT
    
    def test_chat_with_context_prompt_format(self, mock_env_vars):
        """测试带上下文的提示词格式化"""
        from yuntai.prompts import CHAT_WITH_CONTEXT_PROMPT
        
        formatted = CHAT_WITH_CONTEXT_PROMPT.format(
            time_info="2026-01-15 10:00:00",
            forever_memory="测试记忆",
            chat_history="历史对话",
            user_input="你好"
        )
        
        assert "2026-01-15 10:00:00" in formatted
        assert "测试记忆" in formatted
        assert "历史对话" in formatted
        assert "你好" in formatted


class TestTaskJudgementPrompts:
    """测试任务判断提示词"""
    
    def test_task_judgement_prompt_exists(self, mock_env_vars):
        """测试任务判断提示词存在"""
        from yuntai.prompts import TASK_JUDGEMENT_PROMPT
        
        assert TASK_JUDGEMENT_PROMPT is not None
    
    def test_task_type_constants(self, mock_env_vars):
        """测试任务类型常量"""
        from yuntai.prompts import (
            TASK_TYPE_FREE_CHAT,
            TASK_TYPE_BASIC_OPERATION,
            TASK_TYPE_SINGLE_REPLY,
            TASK_TYPE_CONTINUOUS_REPLY,
            TASK_TYPE_COMPLEX_OPERATION,
        )
        
        assert TASK_TYPE_FREE_CHAT is not None
        assert TASK_TYPE_BASIC_OPERATION is not None
        assert TASK_TYPE_SINGLE_REPLY is not None
        assert TASK_TYPE_CONTINUOUS_REPLY is not None
        assert TASK_TYPE_COMPLEX_OPERATION is not None


class TestPhonePrompts:
    """测试手机操作提示词"""
    
    def test_phone_operation_prompt_exists(self, mock_env_vars):
        """测试手机操作提示词存在"""
        from yuntai.prompts import PHONE_OPERATION_PROMPT
        
        assert PHONE_OPERATION_PROMPT is not None
    
    def test_phone_extract_chat_prompt_exists(self, mock_env_vars):
        """测试提取聊天记录提示词存在"""
        from yuntai.prompts import PHONE_EXTRACT_CHAT_PROMPT
        
        assert PHONE_EXTRACT_CHAT_PROMPT is not None
    
    def test_phone_send_message_prompt_exists(self, mock_env_vars):
        """测试发送消息提示词存在"""
        from yuntai.prompts import PHONE_SEND_MESSAGE_PROMPT
        
        assert PHONE_SEND_MESSAGE_PROMPT is not None


class TestReplyPrompts:
    """测试回复生成提示词"""
    
    def test_reply_generation_prompt_exists(self, mock_env_vars):
        """测试回复生成提示词存在"""
        from yuntai.prompts import REPLY_GENERATION_PROMPT
        
        assert REPLY_GENERATION_PROMPT is not None
    
    def test_reply_judgement_prompt_exists(self, mock_env_vars):
        """测试回复判断提示词存在"""
        from yuntai.prompts import REPLY_JUDGEMENT_PROMPT
        
        assert REPLY_JUDGEMENT_PROMPT is not None


class TestPromptExports:
    """测试提示词导出"""
    
    def test_all_prompts_exported(self, mock_env_vars):
        """测试所有提示词都正确导出"""
        from yuntai.prompts import __all__
        
        expected_exports = [
            "TASK_JUDGEMENT_PROMPT",
            "TASK_TYPE_FREE_CHAT",
            "TASK_TYPE_BASIC_OPERATION",
            "TASK_TYPE_SINGLE_REPLY",
            "TASK_TYPE_CONTINUOUS_REPLY",
            "TASK_TYPE_COMPLEX_OPERATION",
            "CHAT_SYSTEM_PROMPT",
            "CHAT_WITH_CONTEXT_PROMPT",
            "PHONE_OPERATION_PROMPT",
            "PHONE_EXTRACT_CHAT_PROMPT",
            "PHONE_SEND_MESSAGE_PROMPT",
            "REPLY_GENERATION_PROMPT",
            "REPLY_JUDGEMENT_PROMPT",
        ]
        
        for export in expected_exports:
            assert export in __all__


class TestPromptContent:
    """测试提示词内容"""
    
    def test_chat_prompt_chinese(self, mock_env_vars):
        """测试聊天提示词是中文"""
        from yuntai.prompts import CHAT_SYSTEM_PROMPT
        
        assert "你" in CHAT_SYSTEM_PROMPT
        assert "的" in CHAT_SYSTEM_PROMPT or "是" in CHAT_SYSTEM_PROMPT
    
    def test_chat_prompt_character_setting(self, mock_env_vars):
        """测试角色设定完整"""
        from yuntai.prompts import CHAT_SYSTEM_PROMPT
        
        assert "友好" in CHAT_SYSTEM_PROMPT or "助手" in CHAT_SYSTEM_PROMPT
    
    def test_context_prompt_placeholders(self, mock_env_vars):
        """测试上下文提示词占位符"""
        from yuntai.prompts import CHAT_WITH_CONTEXT_PROMPT
        
        assert "{time_info}" in CHAT_WITH_CONTEXT_PROMPT
        assert "{forever_memory}" in CHAT_WITH_CONTEXT_PROMPT
        assert "{chat_history}" in CHAT_WITH_CONTEXT_PROMPT
        assert "{user_input}" in CHAT_WITH_CONTEXT_PROMPT

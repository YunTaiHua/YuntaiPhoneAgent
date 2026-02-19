"""
聊天工具模块测试
测试 yuntai.tools.chat_tools 模块
"""
from unittest.mock import MagicMock, patch

import pytest


class TestGetCurrentTimeInfo:
    """测试获取当前时间信息"""
    
    def test_returns_string(self):
        """测试返回字符串"""
        from yuntai.tools.chat_tools import get_current_time_info
        
        result = get_current_time_info()
        assert isinstance(result, str)
    
    def test_contains_time_info(self):
        """测试包含时间信息"""
        from yuntai.tools.chat_tools import get_current_time_info
        
        result = get_current_time_info()
        assert "当前时间信息" in result or "完整时间" in result


class TestGetHistoryContext:
    """测试获取历史上下文"""
    
    def test_empty_file_manager(self):
        """测试空文件管理器会抛出异常"""
        from yuntai.tools.chat_tools import get_history_context
        
        with pytest.raises(AttributeError):
            get_history_context(None)
    
    def test_with_target_app_and_object(self, mock_file_manager):
        """测试指定应用和对象"""
        from yuntai.tools.chat_tools import get_history_context
        
        mock_file_manager.get_recent_conversation_history.return_value = [
            {"content": "历史消息1"},
            {"content": "历史消息2"}
        ]
        
        result = get_history_context(
            mock_file_manager,
            target_app="微信",
            target_object="张三"
        )
        
        assert "最近聊天记录" in result
    
    def test_with_forever_memory(self, mock_file_manager):
        """测试包含永久记忆"""
        from yuntai.tools.chat_tools import get_history_context
        
        result = get_history_context(mock_file_manager)
        assert "永久记忆" in result
    
    def test_with_free_chat_history(self, mock_file_manager):
        """测试包含自由聊天历史"""
        from yuntai.tools.chat_tools import get_history_context
        
        result = get_history_context(mock_file_manager)
        assert "最近自由对话" in result or "永久记忆" in result


class TestBuildChatSystemPrompt:
    """测试构建聊天系统提示词"""
    
    def test_basic_prompt(self):
        """测试基本提示词"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        result = build_chat_system_prompt()
        
        assert "助手" in result
        assert "小芸" in result
    
    def test_prompt_with_time(self):
        """测试包含时间的提示词"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        result = build_chat_system_prompt(include_time=True)
        
        assert "时间" in result
    
    def test_prompt_without_time(self):
        """测试不包含时间的提示词"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        result = build_chat_system_prompt(include_time=False)
        
        assert "当前时间信息" not in result
    
    def test_prompt_with_memory(self):
        """测试包含记忆的提示词"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        memory_content = "用户喜欢音乐"
        result = build_chat_system_prompt(
            include_memory=True,
            forever_memory_content=memory_content
        )
        
        assert "永久记忆" in result
        assert memory_content in result
    
    def test_prompt_without_memory(self):
        """测试不包含记忆的提示词"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        result = build_chat_system_prompt(include_memory=False)
        
        assert "永久记忆" not in result
    
    def test_prompt_with_file_manager(self, mock_file_manager):
        """测试使用文件管理器"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        result = build_chat_system_prompt(
            include_memory=True,
            file_manager=mock_file_manager
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_prompt_character_setting(self):
        """测试角色设定"""
        from yuntai.tools.chat_tools import build_chat_system_prompt
        
        result = build_chat_system_prompt()
        
        assert "友好" in result
        assert "俏皮" in result or "可爱" in result

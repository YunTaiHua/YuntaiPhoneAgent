"""
测试 chat_tools.py - 聊天工具
"""
import pytest
import os
from unittest.mock import MagicMock, patch

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')

from yuntai.tools.chat_tools import (
    get_current_time_info,
    get_history_context,
    build_chat_system_prompt
)


class TestGetCurrentTimeInfo:
    """测试 get_current_time_info 函数"""

    def test_returns_string(self):
        """测试返回字符串"""
        result = get_current_time_info()
        
        assert isinstance(result, str)

    def test_contains_time_info(self):
        """测试包含时间信息"""
        result = get_current_time_info()
        
        assert "当前时间信息" in result
        assert "完整时间" in result
        assert "日期" in result
        assert "时间" in result
        assert "星期" in result

    def test_contains_valid_time(self):
        """测试包含有效时间"""
        result = get_current_time_info()
        
        import re
        # 验证包含时间格式
        assert re.search(r'\d{4}-\d{2}-\d{2}', result) is not None
        assert re.search(r'\d{2}:\d{2}:\d{2}', result) is not None


class TestGetHistoryContext:
    """测试 get_history_context 函数"""

    @pytest.fixture
    def mock_file_manager(self):
        """创建模拟文件管理器"""
        manager = MagicMock()
        manager.get_recent_conversation_history.return_value = [
            {"content": "这是历史消息1"},
            {"content": "这是历史消息2"},
        ]
        manager.get_recent_free_chats.return_value = [
            {"user_input": "用户问题1", "assistant_reply": "助手回复1"},
            {"user_input": "用户问题2", "assistant_reply": "助手回复2"},
        ]
        manager.read_forever_memory.return_value = "这是永久记忆内容"
        return manager

    def test_returns_string(self, mock_file_manager):
        """测试返回字符串"""
        result = get_history_context(mock_file_manager)
        
        assert isinstance(result, str)

    def test_empty_without_params(self, mock_file_manager):
        """测试无参数时返回空或基本内容"""
        result = get_history_context(mock_file_manager)
        
        # 应该包含永久记忆
        assert "永久记忆" in result

    def test_with_target_app_and_object(self, mock_file_manager):
        """测试带目标应用和对象"""
        result = get_history_context(
            mock_file_manager,
            target_app="微信",
            target_object="好友A"
        )
        
        assert "最近聊天记录" in result
        mock_file_manager.get_recent_conversation_history.assert_called_once()

    def test_includes_free_chat_history(self, mock_file_manager):
        """测试包含自由对话历史"""
        result = get_history_context(mock_file_manager)
        
        assert "最近自由对话" in result
        mock_file_manager.get_recent_free_chats.assert_called_once()

    def test_includes_forever_memory(self, mock_file_manager):
        """测试包含永久记忆"""
        result = get_history_context(mock_file_manager)
        
        assert "永久记忆" in result
        assert "这是永久记忆内容" in result
        mock_file_manager.read_forever_memory.assert_called_once()

    def test_custom_limit(self, mock_file_manager):
        """测试自定义限制"""
        result = get_history_context(
            mock_file_manager,
            target_app="微信",
            target_object="好友A",
            limit=10
        )
        
        mock_file_manager.get_recent_conversation_history.assert_called_with(
            "微信", "好友A", limit=10
        )
        mock_file_manager.get_recent_free_chats.assert_called_with(limit=10)

    def test_empty_history(self):
        """测试空历史"""
        manager = MagicMock()
        manager.get_recent_conversation_history.return_value = []
        manager.get_recent_free_chats.return_value = []
        manager.read_forever_memory.return_value = ""
        
        result = get_history_context(
            manager,
            target_app="微信",
            target_object="好友A"
        )
        
        # 应该不包含历史部分
        assert "最近聊天记录" not in result
        assert "最近自由对话" not in result
        assert "永久记忆" not in result


class TestBuildChatSystemPrompt:
    """测试 build_chat_system_prompt 函数"""

    def test_returns_string(self):
        """测试返回字符串"""
        result = build_chat_system_prompt()
        
        assert isinstance(result, str)

    def test_contains_basic_prompt(self):
        """测试包含基本提示"""
        result = build_chat_system_prompt()
        
        assert "小芸" in result
        assert "助手" in result

    def test_includes_time_by_default(self):
        """测试默认包含时间"""
        result = build_chat_system_prompt()
        
        assert "当前时间信息" in result

    def test_excludes_time(self):
        """测试排除时间"""
        result = build_chat_system_prompt(include_time=False)
        
        assert "当前时间信息" not in result

    def test_includes_memory(self):
        """测试包含记忆"""
        result = build_chat_system_prompt(
            include_memory=True,
            forever_memory_content="这是记忆内容"
        )
        
        assert "永久记忆" in result
        assert "这是记忆内容" in result

    def test_excludes_memory(self):
        """测试排除记忆"""
        result = build_chat_system_prompt(
            include_memory=False,
            forever_memory_content="这是记忆内容"
        )
        
        assert "永久记忆" not in result

    def test_empty_memory_not_included(self):
        """测试空记忆不包含"""
        result = build_chat_system_prompt(
            include_memory=True,
            forever_memory_content=""
        )
        
        assert "永久记忆" not in result

    def test_with_file_manager(self):
        """测试带文件管理器"""
        mock_manager = MagicMock()
        mock_manager.read_forever_memory.return_value = "文件管理器记忆"
        
        result = build_chat_system_prompt(
            include_memory=True,
            file_manager=mock_manager
        )
        
        # 结果取决于实现

    def test_time_instructions(self):
        """测试时间指令"""
        result = build_chat_system_prompt(include_time=True)
        
        assert "重要" in result
        assert "时间" in result


class TestChatToolsIntegration:
    """测试聊天工具集成"""

    def test_time_info_in_system_prompt(self):
        """测试时间信息在系统提示中"""
        time_info = get_current_time_info()
        prompt = build_chat_system_prompt(include_time=True)
        
        # 系统提示应该包含时间信息
        assert "当前时间信息" in prompt

    def test_full_workflow(self):
        """测试完整工作流"""
        # 创建模拟文件管理器
        mock_manager = MagicMock()
        mock_manager.get_recent_conversation_history.return_value = [
            {"content": "历史消息"}
        ]
        mock_manager.get_recent_free_chats.return_value = [
            {"user_input": "问题", "assistant_reply": "回复"}
        ]
        mock_manager.read_forever_memory.return_value = "记忆"
        
        # 获取历史上下文
        context = get_history_context(
            mock_manager,
            target_app="微信",
            target_object="好友"
        )
        
        # 构建系统提示
        prompt = build_chat_system_prompt(
            include_time=True,
            include_memory=True,
            forever_memory_content="记忆内容"
        )
        
        assert isinstance(context, str)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

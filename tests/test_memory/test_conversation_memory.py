"""
对话记忆管理模块测试
测试 yuntai.memory.conversation_memory 模块
"""
import os
import json
from unittest.mock import patch, MagicMock

import pytest


class TestConversationMemoryManager:
    """测试对话记忆管理器"""
    
    def test_init_without_files(self, mock_env_vars):
        """测试不带文件初始化"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        assert manager.history_file == ""
        assert manager.forever_memory_file == ""
    
    def test_init_with_history_file(self, temp_history_file, mock_env_vars):
        """测试带历史文件初始化"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager(history_file=temp_history_file)
        assert manager.history_file == temp_history_file
    
    def test_init_with_forever_memory_file(self, temp_forever_memory_file, mock_env_vars):
        """测试带永久记忆文件初始化"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager(forever_memory_file=temp_forever_memory_file)
        assert manager.get_forever_memory() != ""
    
    def test_get_memory(self, mock_env_vars):
        """测试获取记忆实例"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        memory = manager.get_memory()
        assert memory is not None
    
    def test_get_forever_memory_empty(self, mock_env_vars):
        """测试获取空的永久记忆"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        result = manager.get_forever_memory()
        assert result == ""
    
    def test_get_forever_memory_with_content(self, temp_forever_memory_file, mock_env_vars):
        """测试获取有内容的永久记忆"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager(forever_memory_file=temp_forever_memory_file)
        result = manager.get_forever_memory()
        assert "测试记忆内容" in result
    
    def test_add_user_message(self, mock_env_vars):
        """测试添加用户消息"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        manager.add_message("user", "你好")
        
        messages = manager.get_messages()
        assert len(messages) > 0
    
    def test_add_assistant_message(self, mock_env_vars):
        """测试添加助手消息"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        manager.add_message("assistant", "你好！有什么可以帮助你的？")
        
        messages = manager.get_messages()
        assert len(messages) > 0
    
    def test_get_messages_with_limit(self, mock_env_vars):
        """测试获取有限数量的消息"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        for i in range(15):
            manager.add_message("user", f"消息{i}")
        
        messages = manager.get_messages(limit=5)
        assert len(messages) == 5
    
    def test_get_history_context(self, mock_env_vars):
        """测试获取历史上下文"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        manager.add_message("user", "你好")
        manager.add_message("assistant", "你好！")
        
        context = manager.get_history_context()
        assert "用户" in context or "你好" in context
    
    def test_clear_memory(self, mock_env_vars):
        """测试清空记忆"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager
        
        manager = ConversationMemoryManager()
        manager.add_message("user", "测试消息")
        manager.clear()
        
        messages = manager.get_messages()
        assert len(messages) == 0


class TestFreeChatMemory:
    """测试自由聊天记忆"""
    
    def test_init_without_file_manager(self):
        """测试不带文件管理器初始化"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        
        memory = FreeChatMemory()
        assert memory.file_manager is None
    
    def test_get_recent_chats_without_file_manager(self):
        """测试不带文件管理器获取最近聊天"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        
        memory = FreeChatMemory()
        result = memory.get_recent_chats()
        assert result == []
    
    def test_get_recent_chats_with_file_manager(self, mock_file_manager):
        """测试带文件管理器获取最近聊天"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        
        memory = FreeChatMemory(file_manager=mock_file_manager)
        result = memory.get_recent_chats(limit=5)
        
        assert isinstance(result, list)
    
    def test_save_chat_without_file_manager(self):
        """测试不带文件管理器保存聊天"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        
        memory = FreeChatMemory()
        memory.save_chat("你好", "你好！")
    
    def test_save_chat_with_file_manager(self, mock_file_manager):
        """测试带文件管理器保存聊天"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        
        memory = FreeChatMemory(file_manager=mock_file_manager)
        memory.save_chat("你好", "你好！")
        
        mock_file_manager.save_conversation_history.assert_called_once()


class TestChatSessionMemory:
    """测试聊天会话记忆"""
    
    def test_init_without_file_manager(self):
        """测试不带文件管理器初始化"""
        from yuntai.memory.conversation_memory import ChatSessionMemory
        
        memory = ChatSessionMemory()
        assert memory.file_manager is None
    
    def test_get_recent_session_without_file_manager(self):
        """测试不带文件管理器获取最近会话"""
        from yuntai.memory.conversation_memory import ChatSessionMemory
        
        memory = ChatSessionMemory()
        result = memory.get_recent_session("微信", "张三")
        assert result == []
    
    def test_save_session_without_file_manager(self):
        """测试不带文件管理器保存会话"""
        from yuntai.memory.conversation_memory import ChatSessionMemory
        
        memory = ChatSessionMemory()
        memory.save_session("微信", "张三", "好的！", ["消息1", "消息2"])
    
    def test_save_session_with_file_manager(self, mock_file_manager):
        """测试带文件管理器保存会话"""
        from yuntai.memory.conversation_memory import ChatSessionMemory
        
        memory = ChatSessionMemory(file_manager=mock_file_manager)
        memory.save_session("微信", "张三", "好的！", ["消息1"])
        
        mock_file_manager.save_conversation_history.assert_called_once()

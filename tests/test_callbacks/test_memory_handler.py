"""
MemoryCallbackHandler 测试
测试记忆管理回调处理器的各种功能
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from yuntai.callbacks.memory_handler import (
    MemoryCallbackHandler,
    SessionMemoryCallbackHandler,
    FileBasedMemoryCallbackHandler
)
from langchain_core.outputs import LLMResult, ChatGeneration
from langchain_core.messages import AIMessage, HumanMessage


class TestMemoryCallbackHandlerInit:
    """测试 MemoryCallbackHandler 初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        handler = MemoryCallbackHandler()

        assert handler.memory_manager is None
        assert handler.auto_save is True
        assert handler.max_history == 50
        assert handler._current_user_input == ""
        assert handler._current_ai_response == ""
        assert handler._conversation_history == []

    def test_init_with_memory_manager(self):
        """测试带记忆管理器的初始化"""
        memory_manager = Mock()

        handler = MemoryCallbackHandler(
            memory_manager=memory_manager,
            auto_save=False,
            max_history=100
        )

        assert handler.memory_manager == memory_manager
        assert handler.auto_save is False
        assert handler.max_history == 100


class TestMemoryCallbackHandlerLLM:
    """测试 LLM 回调方法"""

    def test_on_llm_start(self):
        """测试 LLM 开始"""
        handler = MemoryCallbackHandler()

        handler.on_llm_start({}, ["prompt1", "prompt2"])

        assert handler._current_user_input == "prompt2"

    def test_on_llm_start_empty_prompts(self):
        """测试空提示词"""
        handler = MemoryCallbackHandler()

        handler.on_llm_start({}, [])

        assert handler._current_user_input == ""

    def test_on_llm_end(self):
        """测试 LLM 结束"""
        memory_manager = Mock()
        handler = MemoryCallbackHandler(
            memory_manager=memory_manager,
            auto_save=True
        )

        handler.on_llm_start({}, ["user input"])

        generation = ChatGeneration(message=AIMessage(content="AI response"))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        assert handler._current_user_input == ""
        assert handler._current_ai_response == ""
        memory_manager.add_message.assert_called()

    def test_on_llm_end_auto_save_disabled(self):
        """测试自动保存禁用"""
        memory_manager = Mock()
        handler = MemoryCallbackHandler(
            memory_manager=memory_manager,
            auto_save=False
        )

        handler.on_llm_start({}, ["user input"])

        generation = ChatGeneration(message=AIMessage(content="AI response"))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        memory_manager.add_message.assert_not_called()

    def test_on_llm_end_no_memory_manager(self):
        """测试无记忆管理器"""
        handler = MemoryCallbackHandler(
            auto_save=True
        )

        handler.on_llm_start({}, ["user input"])

        generation = ChatGeneration(message=AIMessage(content="AI response"))
        result = LLMResult(generations=[[generation]])
        # 不应该抛出异常
        handler.on_llm_end(result)

    def test_on_llm_end_save_exception(self):
        """测试保存异常"""
        memory_manager = Mock()
        memory_manager.add_message.side_effect = Exception("Save error")

        handler = MemoryCallbackHandler(
            memory_manager=memory_manager,
            auto_save=True
        )

        handler.on_llm_start({}, ["user input"])

        generation = ChatGeneration(message=AIMessage(content="AI response"))
        result = LLMResult(generations=[[generation]])
        # 不应该抛出异常
        handler.on_llm_end(result)


class TestMemoryCallbackHandlerMethods:
    """测试其他方法"""

    def test_get_conversation_history(self):
        """测试获取对话历史"""
        handler = MemoryCallbackHandler()

        # 添加一些历史
        handler._conversation_history = [
            {"user": "q1", "assistant": "a1"},
            {"user": "q2", "assistant": "a2"},
            {"user": "q3", "assistant": "a3"},
        ]

        history = handler.get_conversation_history(limit=2)

        assert len(history) == 2
        assert history[0]["user"] == "q2"

    def test_clear_history(self):
        """测试清空历史"""
        handler = MemoryCallbackHandler()

        handler._conversation_history = [
            {"user": "q1", "assistant": "a1"}
        ]

        handler.clear_history()

        assert handler._conversation_history == []

    def test_get_messages_for_langchain(self):
        """测试获取 LangChain 格式消息"""
        handler = MemoryCallbackHandler()

        handler._conversation_history = [
            {"user": "q1", "assistant": "a1"},
            {"user": "q2", "assistant": "a2"},
        ]

        messages = handler.get_messages_for_langchain(limit=2)

        assert len(messages) == 4
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)
        assert messages[0].content == "q1"
        assert messages[1].content == "a1"

    def test_max_history_limit(self):
        """测试历史记录限制"""
        handler = MemoryCallbackHandler(max_history=2)

        # 添加超过限制的历史
        for i in range(5):
            handler._current_user_input = f"q{i}"
            handler._current_ai_response = f"a{i}"
            handler._save_to_memory()

        assert len(handler._conversation_history) == 2


class TestSessionMemoryCallbackHandler:
    """测试会话记忆回调处理器"""

    def test_init(self):
        """测试初始化"""
        handler = SessionMemoryCallbackHandler()

        assert handler._sessions == {}
        assert handler._current_session_id is None

    def test_set_session(self):
        """测试设置会话"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")

        assert handler._current_session_id == "session1"
        assert "session1" in handler._sessions

    def test_get_current_session(self):
        """测试获取当前会话"""
        handler = SessionMemoryCallbackHandler()

        assert handler.get_current_session() is None

        handler.set_session("session1")
        assert handler.get_current_session() == "session1"

    def test_save_to_session(self):
        """测试保存到会话"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "user input"
        handler._current_ai_response = "AI response"
        handler._save_to_memory()

        assert len(handler._sessions["session1"]) == 1
        assert handler._sessions["session1"][0]["user"] == "user input"

    def test_get_session_history(self):
        """测试获取会话历史"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "q1"
        handler._current_ai_response = "a1"
        handler._save_to_memory()

        history = handler.get_session_history("session1")

        assert len(history) == 1
        assert history[0]["user"] == "q1"

    def test_get_session_history_current(self):
        """测试获取当前会话历史"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "q1"
        handler._current_ai_response = "a1"
        handler._save_to_memory()

        history = handler.get_session_history()

        assert len(history) == 1

    def test_get_session_history_nonexistent(self):
        """测试获取不存在的会话历史"""
        handler = SessionMemoryCallbackHandler()

        history = handler.get_session_history("nonexistent")

        assert history == []

    def test_get_all_sessions(self):
        """测试获取所有会话"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "q1"
        handler._current_ai_response = "a1"
        handler._save_to_memory()

        handler.set_session("session2")
        handler._current_user_input = "q2"
        handler._current_ai_response = "a2"
        handler._save_to_memory()

        sessions = handler.get_all_sessions()

        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions

    def test_clear_session(self):
        """测试清空会话"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "q1"
        handler._current_ai_response = "a1"
        handler._save_to_memory()

        handler.clear_session("session1")

        assert handler._sessions["session1"] == []

    def test_clear_current_session(self):
        """测试清空当前会话"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "q1"
        handler._current_ai_response = "a1"
        handler._save_to_memory()

        handler.clear_session()

        assert handler._sessions["session1"] == []

    def test_clear_all_sessions(self):
        """测试清空所有会话"""
        handler = SessionMemoryCallbackHandler()

        handler.set_session("session1")
        handler._current_user_input = "q1"
        handler._current_ai_response = "a1"
        handler._save_to_memory()

        handler.clear_all_sessions()

        assert handler._sessions == {}

    def test_session_max_history(self):
        """测试会话历史限制"""
        handler = SessionMemoryCallbackHandler(max_history=2)

        handler.set_session("session1")
        for i in range(5):
            handler._current_user_input = f"q{i}"
            handler._current_ai_response = f"a{i}"
            handler._save_to_memory()

        assert len(handler._sessions["session1"]) == 2


class TestFileBasedMemoryCallbackHandler:
    """测试基于文件的记忆回调处理器"""

    def test_init(self):
        """测试初始化"""
        file_manager = Mock()
        handler = FileBasedMemoryCallbackHandler(
            file_manager=file_manager
        )

        assert handler.file_manager == file_manager

    def test_save_to_file(self):
        """测试保存到文件"""
        file_manager = Mock()
        handler = FileBasedMemoryCallbackHandler(
            file_manager=file_manager,
            auto_save=True
        )

        handler._current_user_input = "user input"
        handler._current_ai_response = "AI response"
        handler._save_to_memory()

        file_manager.save_conversation_history.assert_called_once()

    def test_save_to_file_no_file_manager(self):
        """测试无文件管理器"""
        handler = FileBasedMemoryCallbackHandler(
            auto_save=True
        )

        handler._current_user_input = "user input"
        handler._current_ai_response = "AI response"
        # 不应该抛出异常
        handler._save_to_memory()

    def test_save_to_file_exception(self):
        """测试保存到文件异常"""
        file_manager = Mock()
        file_manager.save_conversation_history.side_effect = Exception("File error")

        handler = FileBasedMemoryCallbackHandler(
            file_manager=file_manager,
            auto_save=True
        )

        handler._current_user_input = "user input"
        handler._current_ai_response = "AI response"
        # 不应该抛出异常
        handler._save_to_memory()

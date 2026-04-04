"""
针对第二轮覆盖率缺口补充测试
================================

覆盖模块:
    - callbacks/streaming_handler: exception paths, reset()
    - callbacks/memory_handler: save paths, get_messages_for_langchain
    - core/agent_executor: set_device_type, user_confirm, cleanup
    - core/utils: check_hdc, check_system_requirements exception paths
    - agents/phone_agent: wrapper methods, send_message, open_app
    - agents/chat_agent: callbacks, history, memory loading
    - agents/judgement_agent: _extract_app fallback, _extract_content colon
    - chains/reply_chain: set_device_id, _get_graph, is_running, single_reply
    - graphs/nodes/extract: cache update, remove, module-level functions
    - views/dashboard: adaptive height edge cases
"""

import os
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ==============================================================
# callbacks/streaming_handler 未覆盖行
# ==============================================================

class TestStreamingHandlerCoverageGaps:
    """覆盖 streaming_handler.py 未覆盖行"""

    def test_output_callback_exception(self):
        """覆盖 lines 153-156: output_callback 异常"""
        from yuntai.callbacks.streaming_handler import StreamingCallbackHandler

        handler = StreamingCallbackHandler()
        handler._is_streaming = True
        handler.output_callback = lambda t: (_ for _ in ()).throw(RuntimeError("cb boom"))

        handler.on_llm_new_token("test", run=MagicMock())

    def test_complete_callback_exception(self):
        """覆盖 lines 176-179: complete_callback 异常"""
        from yuntai.callbacks.streaming_handler import StreamingCallbackHandler

        handler = StreamingCallbackHandler()
        handler._is_streaming = True
        handler._current_response = "some response"
        handler.complete_callback = lambda t: (_ for _ in ()).throw(RuntimeError("cb boom"))
        handler.on_llm_end(MagicMock(), run=MagicMock())

    def test_reset_method(self):
        """覆盖 lines 211-213: reset() 方法"""
        from yuntai.callbacks.streaming_handler import StreamingCallbackHandler

        handler = StreamingCallbackHandler()
        handler._current_response = "old"
        handler._is_streaming = True
        handler.reset()
        assert handler._current_response == ""
        assert handler._is_streaming is False

    def test_qt_handler_not_streaming_early_return(self):
        """覆盖 line 271: _is_streaming=False 早期返回"""
        from yuntai.callbacks.streaming_handler import QtStreamingCallbackHandler

        handler = QtStreamingCallbackHandler()
        handler._is_streaming = False
        handler.on_llm_new_token("test", run=MagicMock())

    def test_qt_handler_signal_exception(self):
        """覆盖 lines 280-283: Qt 信号发送异常"""
        from yuntai.callbacks.streaming_handler import QtStreamingCallbackHandler

        handler = QtStreamingCallbackHandler()
        handler._is_streaming = True
        handler.append_signal = SimpleNamespace(emit=lambda t: (_ for _ in ()).throw(RuntimeError("signal boom")))
        handler.on_llm_new_token("test", run=MagicMock())

    def test_qt_handler_complete_signal_exception(self):
        """覆盖 lines 301-304: Qt 完成信号异常"""
        from yuntai.callbacks.streaming_handler import QtStreamingCallbackHandler

        handler = QtStreamingCallbackHandler()
        handler._is_streaming = True
        handler._current_response = "resp"
        handler.complete_signal = SimpleNamespace(emit=lambda t: (_ for _ in ()).throw(RuntimeError("signal boom")))
        handler.on_llm_end(MagicMock(), run=MagicMock())

    def test_async_handler_not_streaming_early_return(self):
        """覆盖 line 360: 异步 handler _is_streaming=False"""
        from yuntai.callbacks.streaming_handler import AsyncStreamingCallbackHandler

        handler = AsyncStreamingCallbackHandler()
        handler._is_streaming = False
        import asyncio
        asyncio.get_event_loop().run_until_complete(handler.on_llm_new_token_async("test", run=MagicMock()))

    def test_async_handler_callback_exception(self, monkeypatch):
        """覆盖 lines 378-381: 异步回调异常"""
        from yuntai.callbacks.streaming_handler import AsyncStreamingCallbackHandler
        import builtins

        handler = AsyncStreamingCallbackHandler()
        handler._is_streaming = True
        handler.output_callback = lambda t: (_ for _ in ()).throw(RuntimeError("async boom"))

        # 防止 Windows GBK 编码错误
        real_print = builtins.print
        monkeypatch.setattr(builtins, "print", lambda *a, **k: None)
        import asyncio
        asyncio.get_event_loop().run_until_complete(handler.on_llm_new_token_async("test", run=MagicMock()))


# ==============================================================
# callbacks/memory_handler 未覆盖行
# ==============================================================

class TestMemoryHandlerCoverageGaps:
    """覆盖 memory_handler.py 未覆盖行"""

    def test_save_to_memory_empty_input_returns(self):
        """覆盖 line 133: 空输入直接返回"""
        from yuntai.callbacks.memory_handler import MemoryCallbackHandler

        handler = MemoryCallbackHandler()
        handler._current_user_input = ""
        handler._current_ai_response = "resp"
        handler._save_to_memory()

    def test_save_to_memory_exception(self):
        """覆盖 lines 157-159: 保存异常"""
        from yuntai.callbacks.memory_handler import MemoryCallbackHandler

        handler = MemoryCallbackHandler()
        handler._current_user_input = "user"
        handler._current_ai_response = "ai"
        handler._memory = SimpleNamespace(
            append=lambda item: (_ for _ in ()).throw(RuntimeError("mem boom"))
        )
        handler._save_to_memory()

    def test_get_messages_for_langchain(self):
        """覆盖 lines 194-202: get_messages_for_langchain"""
        from yuntai.callbacks.memory_handler import MemoryCallbackHandler

        handler = MemoryCallbackHandler()
        handler._conversation_history = [
            {"user": "hello", "assistant": "hi"},
            {"user": "bye", "assistant": "bye"},
        ]
        messages = handler.get_messages_for_langchain(limit=10)
        assert len(messages) == 4
        assert messages[0].content == "hello"
        assert messages[1].content == "hi"

    def test_session_handler_empty_input_returns(self):
        """覆盖 line 278: SessionMemory 空输入返回"""
        from yuntai.callbacks.memory_handler import SessionMemoryCallbackHandler

        handler = SessionMemoryCallbackHandler()
        handler._current_user_input = ""
        handler._current_ai_response = "resp"
        handler._save_to_memory()

    def test_session_handler_new_session_init(self):
        """覆盖 line 291: 新 session 初始化"""
        from yuntai.callbacks.memory_handler import SessionMemoryCallbackHandler

        handler = SessionMemoryCallbackHandler()
        handler._current_session_id = "sess1"
        handler._current_user_input = "user"
        handler._current_ai_response = "ai"
        handler._save_to_memory()
        assert "sess1" in handler._sessions
        assert len(handler._sessions["sess1"]) == 1

    def test_session_handler_get_current_session(self):
        """覆盖 line 268: get_current_session"""
        from yuntai.callbacks.memory_handler import SessionMemoryCallbackHandler

        handler = SessionMemoryCallbackHandler()
        handler._current_session_id = "sess1"
        assert handler.get_current_session() == "sess1"

    def test_session_handler_get_session_history_empty(self):
        """覆盖 line 324: 空 session 返回空列表"""
        from yuntai.callbacks.memory_handler import SessionMemoryCallbackHandler

        handler = SessionMemoryCallbackHandler()
        assert handler.get_session_history("") == []
        assert handler.get_session_history("nonexistent") == []

    def test_file_handler_empty_input_returns(self):
        """覆盖 line 407: FileBased 空输入返回"""
        from yuntai.callbacks.memory_handler import FileBasedMemoryCallbackHandler

        handler = FileBasedMemoryCallbackHandler(file_manager=SimpleNamespace(
            save_conversation_history=lambda x: None
        ))
        handler._current_user_input = ""
        handler._current_ai_response = "resp"
        handler._save_to_memory()

    def test_file_handler_save_exception(self):
        """覆盖 lines 428-430: 文件保存异常"""
        from yuntai.callbacks.memory_handler import FileBasedMemoryCallbackHandler

        handler = FileBasedMemoryCallbackHandler(file_manager=SimpleNamespace(
            save_conversation_history=lambda x: (_ for _ in ()).throw(RuntimeError("file boom"))
        ))
        handler._current_user_input = "user"
        handler._current_ai_response = "ai"
        handler._save_to_memory()


# ==============================================================
# core/agent_executor 未覆盖行
# ==============================================================

class TestAgentExecutorCoverageGaps:
    """覆盖 agent_executor.py 未覆盖行"""

    def test_set_device_type(self):
        """覆盖 lines 101-102: set_device_type"""
        from yuntai.core.agent_executor import AgentExecutor

        executor = AgentExecutor()
        executor.set_device_type("harmony")
        assert executor.device_type == "harmony"

    def test_cleanup_stdin_pipe_oserror(self, monkeypatch):
        """覆盖 lines 141-142, 149-150: stdin pipe 关闭异常"""
        from yuntai.core import agent_executor as mod

        mod.AgentExecutor._stdin_write = 99
        mod.AgentExecutor._stdin_read = 98

        monkeypatch.setattr(os, "close", lambda fd: (_ for _ in ()).throw(OSError("bad fd")))
        mod.AgentExecutor._cleanup_stdin_pipe()

        assert mod.AgentExecutor._stdin_write is None
        assert mod.AgentExecutor._stdin_read is None

    def test_user_confirm_with_pipe(self, monkeypatch):
        """覆盖 lines 176-187: user_confirm 通过管道"""
        from yuntai.core import agent_executor as mod

        write_fd = []
        monkeypatch.setattr(os, "write", lambda fd, data: write_fd.append(fd))

        mod.AgentExecutor._stdin_write = 42
        mod.AgentExecutor._user_confirmation_event = threading.Event()
        mod.AgentExecutor._is_waiting_for_confirmation = threading.Event()

        result = mod.AgentExecutor.user_confirm()
        assert result is True
        assert write_fd == [42]

        mod.AgentExecutor._stdin_write = None

    def test_user_confirm_write_oserror(self, monkeypatch):
        """覆盖 lines 185-186: user_confirm 写入失败"""
        from yuntai.core import agent_executor as mod

        monkeypatch.setattr(os, "write", lambda fd, data: (_ for _ in ()).throw(OSError("pipe closed")))

        mod.AgentExecutor._stdin_write = 42
        mod.AgentExecutor._user_confirmation_event = threading.Event()
        mod.AgentExecutor._is_waiting_for_confirmation = threading.Event()

        result = mod.AgentExecutor.user_confirm()
        assert result is False

        mod.AgentExecutor._stdin_write = None

    def test_user_confirm_no_pipe(self, monkeypatch):
        """覆盖 lines 190-192: user_confirm 无管道"""
        from yuntai.core import agent_executor as mod

        mod.AgentExecutor._stdin_write = None
        mod.AgentExecutor._user_confirmation_event = threading.Event()
        mod.AgentExecutor._is_waiting_for_confirmation = threading.Event()

        result = mod.AgentExecutor.user_confirm()
        assert result is False  # 无管道返回 False


# ==============================================================
# core/utils 未覆盖行
# ==============================================================

class TestUtilsCoverageGaps:
    """覆盖 utils.py 未覆盖行"""

    def test_enable_windows_color_oserror(self, monkeypatch):
        """覆盖 lines 93-95: Windows 控制台颜色设置失败"""
        from yuntai.core.utils import Utils

        utils = Utils()
        monkeypatch.setattr(sys, "platform", "win32")

        # ctypes 在 enable_windows_color 内部局部导入，需 mock sys.modules
        mock_ctypes = SimpleNamespace(
            windll=SimpleNamespace(
                kernel32=SimpleNamespace(
                    GetStdHandle=lambda x: (_ for _ in ()).throw(OSError("no handle"))
                )
            )
        )
        monkeypatch.setitem(sys.modules, "ctypes", mock_ctypes)
        utils.enable_windows_color()

    def test_check_system_requirements_adb_not_found(self, monkeypatch):
        """覆盖 lines 140-145: ADB 未找到"""
        from yuntai.core.utils import Utils

        utils = Utils()
        monkeypatch.setattr("yuntai.core.utils.subprocess.run",
                            lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("adb not found")))
        result = utils.check_system_requirements()
        assert result is False

    def test_check_system_requirements_adb_exception(self, monkeypatch):
        """覆盖 lines 144-145: ADB 检查异常"""
        from yuntai.core.utils import Utils

        utils = Utils()
        monkeypatch.setattr("yuntai.core.utils.subprocess.run",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("adb crash")))
        result = utils.check_system_requirements()
        assert result is False

    def test_check_hdc_not_installed(self, monkeypatch):
        """覆盖 lines 165-166: HDC 未安装"""
        from yuntai.core.utils import Utils

        utils = Utils()
        monkeypatch.setattr("yuntai.core.utils.shutil.which", lambda cmd: None)
        result = utils.check_hdc()
        assert result is False

    def test_check_hdc_version_check_exception(self, monkeypatch):
        """覆盖 lines 190-192: HDC 检查异常"""
        from yuntai.core.utils import Utils

        utils = Utils()
        monkeypatch.setattr("yuntai.core.utils.shutil.which", lambda cmd: "/usr/bin/hdc")
        monkeypatch.setattr("yuntai.core.utils.subprocess.run",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("hdc crash")))
        result = utils.check_hdc()
        assert result is False

    def test_tts_state_manager_page_synthesizing_property(self):
        """覆盖 line 328: tts_page_synthesizing 属性"""
        from yuntai.core.utils import TTSStateManager

        mgr = TTSStateManager()
        assert mgr.tts_page_synthesizing is False
        mgr._tts_page_synthesizing = True
        assert mgr.tts_page_synthesizing is True
        mgr._tts_page_synthesizing = False


# ==============================================================
# agents/phone_agent 未覆盖行
# ==============================================================

class TestPhoneAgentCoverageGaps:
    """覆盖 phone_agent.py 未覆盖行"""

    def _make_wrapper(self, monkeypatch):
        """创建 PhoneAgentWrapper"""
        import yuntai.agents.phone_agent as mod

        monkeypatch.setattr(mod, "ModelConfig", lambda **kw: SimpleNamespace(**kw))
        monkeypatch.setattr(mod, "AgentConfig", lambda **kw: SimpleNamespace(**kw))
        monkeypatch.setattr(mod, "ExternalPhoneAgent", MagicMock())

        wrapper = mod.PhoneAgentWrapper(device_id="test_dev", max_steps=10)
        return wrapper

    def test_create_agent(self, monkeypatch):
        """覆盖 lines 102-121: _create_agent"""
        wrapper = self._make_wrapper(monkeypatch)
        agent = wrapper._create_agent()
        assert agent is not None

    def test_get_agent_lazy_creation(self, monkeypatch):
        """覆盖 lines 132-134: _get_agent 懒加载"""
        wrapper = self._make_wrapper(monkeypatch)
        agent = wrapper._get_agent()
        assert agent is not None
        agent2 = wrapper._get_agent()
        assert agent2 is agent

    def test_reset_agent(self, monkeypatch):
        """覆盖 lines 143-146: _reset_agent"""
        wrapper = self._make_wrapper(monkeypatch)
        wrapper._get_agent()
        wrapper._reset_agent()
        assert wrapper._agent is None

    def test_setup_pipe(self, monkeypatch):
        """覆盖 lines 154-155: _setup_pipe"""
        import yuntai.agents.phone_agent as mod
        called = []
        monkeypatch.setattr(mod.AgentExecutor, "_setup_stdin_pipe", lambda: called.append(True))
        wrapper = self._make_wrapper(monkeypatch)
        wrapper._setup_pipe()
        assert called == [True]

    def test_cleanup_pipe(self, monkeypatch):
        """覆盖 lines 163-164: _cleanup_pipe"""
        import yuntai.agents.phone_agent as mod
        called = []
        monkeypatch.setattr(mod.AgentExecutor, "_cleanup_stdin_pipe", lambda: called.append(True))
        wrapper = self._make_wrapper(monkeypatch)
        wrapper._cleanup_pipe()
        assert called == [True]

    def test_open_app(self, monkeypatch):
        """覆盖 lines 223-224: open_app"""
        wrapper = self._make_wrapper(monkeypatch)
        wrapper.execute = MagicMock(return_value=True)
        result = wrapper.open_app("微信")
        assert result is True
        wrapper.execute.assert_called_once_with("打开微信")

    def test_send_message_default_template(self, monkeypatch):
        """覆盖 line 313: 默认消息模板"""
        wrapper = self._make_wrapper(monkeypatch)

        mock_agent = MagicMock()
        mock_agent.run.return_value = "消息已成功发送"
        wrapper._setup_pipe = MagicMock()
        wrapper._get_agent = MagicMock(return_value=mock_agent)
        wrapper._reset_agent = MagicMock()

        ok, result = wrapper.send_message("微博", "friend", "hello")
        assert ok is True

    def test_send_message_exception(self, monkeypatch):
        """覆盖 lines 333-336: 发送消息异常"""
        wrapper = self._make_wrapper(monkeypatch)

        mock_agent = MagicMock()
        mock_agent.run.side_effect = RuntimeError("exec boom")
        wrapper._setup_pipe = MagicMock()
        wrapper._get_agent = MagicMock(return_value=mock_agent)
        wrapper._reset_agent = MagicMock()

        ok, msg = wrapper.send_message("微信", "friend", "hello")
        assert ok is False
        assert "发送失败" in msg


# ==============================================================
# agents/chat_agent 未覆盖行
# ==============================================================

class TestChatAgentCoverageGaps:
    """覆盖 chat_agent.py 未覆盖行"""

    def test_set_streaming_callback(self):
        """覆盖 lines 135-136: set_streaming_callback"""
        from yuntai.agents.chat_agent import ChatAgent
        agent = ChatAgent(model=MagicMock())
        cb = lambda t: None
        agent.set_streaming_callback(cb)
        assert agent._streaming_callback is cb

    def test_set_complete_callback(self):
        """覆盖 lines 152-153: set_complete_callback"""
        from yuntai.agents.chat_agent import ChatAgent
        agent = ChatAgent(model=MagicMock())
        cb = lambda t: None
        agent.set_complete_callback(cb)
        assert agent._complete_callback is cb

    def test_chat_with_history_assistant_role(self, monkeypatch):
        """覆盖 lines 311-313: 历史消息中 assistant 角色"""
        from yuntai.agents.chat_agent import ChatAgent

        mock_model = MagicMock()
        mock_model.invoke.return_value = SimpleNamespace(content="response")
        agent = ChatAgent(model=mock_model)
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = agent.chat_with_history("test", history)
        assert result == "response"

    def test_chat_with_history_exception(self, monkeypatch):
        """覆盖 lines 336-339: 带历史聊天异常"""
        from yuntai.agents.chat_agent import ChatAgent

        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("model boom")
        agent = ChatAgent(model=mock_model)
        result = agent.chat_with_history("test", [])
        assert "聊天失败" in result

    def test_chat_stream_with_memory(self, monkeypatch):
        """覆盖 lines 374-384: chat_stream 带记忆"""
        from yuntai.agents.chat_agent import ChatAgent

        mock_model = MagicMock()
        mock_chunks = [SimpleNamespace(content="hel"), SimpleNamespace(content="lo")]
        mock_model.stream.return_value = iter(mock_chunks)

        fm = SimpleNamespace(
            read_forever_memory=lambda: "永久记忆内容",
            get_recent_free_chats=lambda limit: [
                {"user_input": "hi", "assistant_reply": "hello"},
            ],
        )

        agent = ChatAgent(model=mock_model, file_manager=fm)
        chunks = list(agent.chat_stream("test", include_memory=True))
        assert len(chunks) > 0


# ==============================================================
# agents/judgement_agent 未覆盖行
# ==============================================================

class TestJudgementAgentCoverageGaps:
    """覆盖 judgement_agent.py 未覆盖行"""

    def test_extract_app_no_match(self):
        """覆盖 line 334: 未提取到目标 APP"""
        from yuntai.agents.judgement_agent import JudgementAgent

        agent = JudgementAgent(model=MagicMock())
        result = agent._extract_app("打开一个不存在的应用")
        assert result == ""

    def test_extract_content_colon(self):
        """覆盖 lines 387-393: 冒号内容提取"""
        from yuntai.agents.judgement_agent import JudgementAgent

        agent = JudgementAgent(model=MagicMock())
        result = agent._extract_content("请帮我发送消息：你好世界")
        assert result == "你好世界"

    def test_extract_content_colon_with_time_format(self):
        """覆盖 lines 387-393: 冒号后是时间格式（排除）"""
        from yuntai.agents.judgement_agent import JudgementAgent

        agent = JudgementAgent(model=MagicMock())
        result = agent._extract_content("时间：12:30")
        assert result == "" or "12" not in result


# ==============================================================
# chains/reply_chain 未覆盖行
# ==============================================================

class TestReplyChainCoverageGaps:
    """覆盖 reply_chain.py 未覆盖行"""

    def test_set_device_id(self):
        """覆盖 lines 121-124: set_device_id"""
        from yuntai.chains.reply_chain import ReplyChain

        chain = ReplyChain(device_id="old_id")
        chain.set_device_id("new_id")
        assert chain.device_id == "new_id"
        assert chain._reply_graph is None

    def test_get_graph_lazy_creation(self, monkeypatch):
        """覆盖 lines 136-137: _get_graph 懒加载"""
        import yuntai.chains.reply_chain as mod

        mock_graph = MagicMock()
        monkeypatch.setattr(mod, "ReplyGraph", lambda **kw: mock_graph)
        chain = mod.ReplyChain()
        graph = chain._get_graph()
        assert graph is mock_graph

    def test_is_running_no_graph(self):
        """覆盖 line 361: is_running 无 graph"""
        from yuntai.chains.reply_chain import ReplyChain

        chain = ReplyChain()
        assert chain.is_running() is False

    def test_single_reply_no_messages(self, monkeypatch):
        """覆盖 lines 195-196: single_reply 消息解析为空"""
        import yuntai.chains.reply_chain as mod

        # Mock PhoneAgent to return success with records
        mock_phone = MagicMock()
        mock_phone.extract_chat_records.return_value = (True, "some records")
        monkeypatch.setattr(mod, "PhoneAgent", lambda device_id: mock_phone)

        # Mock parse_messages to return empty list
        monkeypatch.setattr(mod, "parse_messages", lambda *a, **k: [])
        monkeypatch.setattr(mod, "get_zhipu_client", lambda: MagicMock())

        chain = mod.ReplyChain()
        chain.file_manager = None
        ok, msg = chain.single_reply("wx", "test")
        assert ok is False
        assert "未能解析" in msg


# ==============================================================
# graphs/nodes/extract 未覆盖行
# ==============================================================

class TestExtractCoverageGaps:
    """覆盖 extract.py 未覆盖行"""

    def _make_cache(self):
        """创建 PhoneAgentCache"""
        from yuntai.graphs.nodes.extract import PhoneAgentCache
        cache = PhoneAgentCache(max_size=3, expire_seconds=3600)
        return cache

    def test_cache_put_update_existing(self):
        """覆盖 lines 161-167: 更新已有缓存条目"""
        cache = self._make_cache()
        agent1 = SimpleNamespace(name="agent1")
        agent2 = SimpleNamespace(name="agent2")
        cache.put("dev1", agent1)
        cache.put("dev1", agent2)
        assert cache.get("dev1") is agent2

    def test_cache_remove_existing(self):
        """覆盖 lines 196-198: 移除存在的缓存条目"""
        cache = self._make_cache()
        cache.put("dev1", SimpleNamespace())
        result = cache.remove("dev1")
        assert result is True
        assert cache.get("dev1") is None

    def test_cache_remove_nonexistent(self):
        """覆盖 lines 196-198: 移除不存在的缓存条目"""
        cache = self._make_cache()
        result = cache.remove("nonexistent")
        assert result is False

    def test_clear_cache_specific_device(self):
        """覆盖 lines 306-308: 清理特定设备缓存"""
        from yuntai.graphs.nodes import extract as mod
        mod._cache = self._make_cache()
        mod._cache.put("dev1", SimpleNamespace())
        mod._cache.put("dev2", SimpleNamespace())
        mod.clear_cache("dev1")
        assert mod._cache.get("dev1") is None
        assert mod._cache.get("dev2") is not None

    def test_clear_cache_all(self):
        """覆盖 lines 309-311: 清理全部缓存"""
        from yuntai.graphs.nodes import extract as mod
        mod._cache = self._make_cache()
        mod._cache.put("dev1", SimpleNamespace())
        mod._cache.put("dev2", SimpleNamespace())
        mod.clear_cache()
        assert mod._cache.size() == 0

    def test_get_cache_size(self):
        """覆盖 line 321: get_cache_size"""
        from yuntai.graphs.nodes import extract as mod
        mod._cache = self._make_cache()
        mod._cache.put("dev1", SimpleNamespace())
        mod._cache.put("dev2", SimpleNamespace())
        assert mod.get_cache_size() == 2

    def test_get_cache_stats(self):
        """覆盖 line 331: get_cache_stats"""
        from yuntai.graphs.nodes import extract as mod
        mod._cache = self._make_cache()
        stats = mod.get_cache_stats()
        assert isinstance(stats, dict)

    def test_cleanup_expired_cache(self):
        """覆盖 line 341: cleanup_expired_cache"""
        from yuntai.graphs.nodes import extract as mod
        mod._cache = self._make_cache()
        result = mod.cleanup_expired_cache()
        assert isinstance(result, int)


# ==============================================================
# views/dashboard 未覆盖行
# ==============================================================

class TestDashboardCoverageGaps:
    """覆盖 dashboard.py 未覆盖行"""

    def test_input_text_changed_no_widget(self):
        """覆盖 line 513: command_input 组件缺失"""
        from yuntai.views.dashboard import DashboardBuilder

        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder.components = {}
        builder._on_input_text_changed()

    def test_input_text_changed_same_line_count(self):
        """覆盖 line 527: 行数未变化"""
        from yuntai.views.dashboard import DashboardBuilder

        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 3
        widget = SimpleNamespace(toPlainText=lambda: "line1\nline2\nline3")
        builder.components = {"command_input": widget}
        builder._on_input_text_changed()

    def test_input_text_changed_attribute_error(self):
        """覆盖 line 538: AttributeError"""
        from yuntai.views.dashboard import DashboardBuilder

        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 1

        class BadWidget:
            def toPlainText(self):
                raise AttributeError("no such method")

        builder.components = {"command_input": BadWidget()}
        builder._on_input_text_changed()

    def test_input_text_changed_runtime_error(self):
        """覆盖 lines 541-543: RuntimeError"""
        from yuntai.views.dashboard import DashboardBuilder

        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 1

        class BadWidget:
            def toPlainText(self):
                raise RuntimeError("C++ object deleted")

        builder.components = {"command_input": BadWidget()}
        builder._on_input_text_changed()

    def test_input_text_changed_generic_exception(self):
        """覆盖 line 544-545: 通用异常"""
        from yuntai.views.dashboard import DashboardBuilder

        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 1

        class BadWidget:
            def toPlainText(self):
                raise ValueError("unexpected")

        builder.components = {"command_input": BadWidget()}
        builder._on_input_text_changed()

    def test_input_text_changed_height_below_minimum(self):
        """覆盖 line 535: 高度低于最小值"""
        from yuntai.views.dashboard import DashboardBuilder

        builder = DashboardBuilder.__new__(DashboardBuilder)
        builder._last_line_count = 3

        heights = []
        widget = SimpleNamespace(
            toPlainText=lambda: "x",
            setFixedHeight=lambda h: heights.append(h),
        )
        builder.components = {"command_input": widget}
        builder._on_input_text_changed()
        assert 42 in heights

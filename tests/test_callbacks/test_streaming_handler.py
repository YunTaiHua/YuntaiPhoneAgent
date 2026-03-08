"""
StreamingCallbackHandler 测试
测试流式输出处理器的各种功能
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from yuntai.callbacks.streaming_handler import (
    StreamingCallbackHandler,
    QtStreamingCallbackHandler,
    AsyncStreamingCallbackHandler
)
from langchain_core.outputs import LLMResult, ChatGeneration
from langchain_core.messages import AIMessage


class TestStreamingCallbackHandlerInit:
    """测试 StreamingCallbackHandler 初始化"""

    def test_init_default(self):
        """测试默认初始化"""
        handler = StreamingCallbackHandler()

        assert handler.output_callback is None
        assert handler.complete_callback is None
        assert handler.enable_typewriter is True
        assert handler._current_response == ""
        assert handler._is_streaming is False

    def test_init_with_callbacks(self):
        """测试带回调的初始化"""
        output_cb = Mock()
        complete_cb = Mock()

        handler = StreamingCallbackHandler(
            output_callback=output_cb,
            complete_callback=complete_cb,
            enable_typewriter=False
        )

        assert handler.output_callback == output_cb
        assert handler.complete_callback == complete_cb
        assert handler.enable_typewriter is False


class TestStreamingCallbackHandlerLLM:
    """测试 LLM 回调方法"""

    def test_on_llm_start(self):
        """测试 LLM 开始"""
        handler = StreamingCallbackHandler()

        handler.on_llm_start({}, ["test prompt"])

        assert handler._current_response == ""
        assert handler._is_streaming is True

    def test_on_llm_new_token(self):
        """测试新 token 生成"""
        tokens = []
        handler = StreamingCallbackHandler(
            output_callback=lambda t: tokens.append(t)
        )

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("Hello")
        handler.on_llm_new_token(" ")
        handler.on_llm_new_token("World")

        assert handler._current_response == "Hello World"
        assert tokens == ["Hello", " ", "World"]

    def test_on_llm_new_token_not_streaming(self):
        """测试非流式状态下的 token"""
        tokens = []
        handler = StreamingCallbackHandler(
            output_callback=lambda t: tokens.append(t)
        )

        # 不调用 on_llm_start
        handler.on_llm_new_token("test")

        assert handler._current_response == ""
        assert tokens == []

    def test_on_llm_new_token_callback_exception(self):
        """测试输出回调异常"""
        handler = StreamingCallbackHandler(
            output_callback=lambda t: 1/0  # 故意抛出异常
        )

        handler.on_llm_start({}, ["test"])
        # 不应该抛出异常
        handler.on_llm_new_token("test")

        assert handler._current_response == "test"

    def test_on_llm_end(self):
        """测试 LLM 结束"""
        complete_response = []
        handler = StreamingCallbackHandler(
            complete_callback=lambda r: complete_response.append(r)
        )

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("Hello")
        handler.on_llm_new_token(" World")

        generation = ChatGeneration(message=AIMessage(content="Hello World"))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        assert handler._is_streaming is False
        assert complete_response == ["Hello World"]

    def test_on_llm_end_no_response(self):
        """测试 LLM 结束无响应"""
        complete_response = []
        handler = StreamingCallbackHandler(
            complete_callback=lambda r: complete_response.append(r)
        )

        handler.on_llm_start({}, ["test"])
        # 不添加 token

        generation = ChatGeneration(message=AIMessage(content=""))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        # 没有响应时不调用完成回调
        assert complete_response == []

    def test_on_llm_end_callback_exception(self):
        """测试完成回调异常"""
        handler = StreamingCallbackHandler(
            complete_callback=lambda r: 1/0  # 故意抛出异常
        )

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("test")

        generation = ChatGeneration(message=AIMessage(content="test"))
        result = LLMResult(generations=[[generation]])
        # 不应该抛出异常
        handler.on_llm_end(result)

        assert handler._is_streaming is False

    def test_on_llm_error(self):
        """测试 LLM 错误"""
        handler = StreamingCallbackHandler()

        handler.on_llm_start({}, ["test"])
        handler.on_llm_error(Exception("Test error"))

        assert handler._is_streaming is False


class TestStreamingCallbackHandlerMethods:
    """测试其他方法"""

    def test_get_current_response(self):
        """测试获取当前响应"""
        handler = StreamingCallbackHandler()

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("Hello")

        assert handler.get_current_response() == "Hello"

    def test_reset(self):
        """测试重置"""
        handler = StreamingCallbackHandler()

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("Hello")
        handler.reset()

        assert handler._current_response == ""
        assert handler._is_streaming is False


class TestQtStreamingCallbackHandler:
    """测试 Qt 流式输出处理器"""

    def test_init(self):
        """测试初始化"""
        append_signal = Mock()
        complete_signal = Mock()

        handler = QtStreamingCallbackHandler(
            append_signal=append_signal,
            complete_signal=complete_signal,
            enable_typewriter=True
        )

        assert handler.append_signal == append_signal
        assert handler.complete_signal == complete_signal
        assert handler.enable_typewriter is True

    def test_on_llm_new_token_with_signal(self):
        """测试带信号的 token 生成"""
        append_signal = Mock()
        handler = QtStreamingCallbackHandler(
            append_signal=append_signal
        )

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("test")

        append_signal.emit.assert_called_once_with("test")

    def test_on_llm_new_token_signal_exception(self):
        """测试信号发送异常"""
        append_signal = Mock()
        append_signal.emit.side_effect = Exception("Signal error")

        handler = QtStreamingCallbackHandler(
            append_signal=append_signal
        )

        handler.on_llm_start({}, ["test"])
        # 不应该抛出异常
        handler.on_llm_new_token("test")

        assert handler._current_response == "test"

    def test_on_llm_end_with_signal(self):
        """测试带信号的 LLM 结束"""
        complete_signal = Mock()
        handler = QtStreamingCallbackHandler(
            complete_signal=complete_signal
        )

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("Hello")

        generation = ChatGeneration(message=AIMessage(content="Hello"))
        result = LLMResult(generations=[[generation]])
        handler.on_llm_end(result)

        complete_signal.emit.assert_called_once_with("Hello")

    def test_on_llm_end_signal_exception(self):
        """测试完成信号发送异常"""
        complete_signal = Mock()
        complete_signal.emit.side_effect = Exception("Signal error")

        handler = QtStreamingCallbackHandler(
            complete_signal=complete_signal
        )

        handler.on_llm_start({}, ["test"])
        handler.on_llm_new_token("test")

        generation = ChatGeneration(message=AIMessage(content="test"))
        result = LLMResult(generations=[[generation]])
        # 不应该抛出异常
        handler.on_llm_end(result)


class TestAsyncStreamingCallbackHandler:
    """测试异步流式输出处理器"""

    def test_init(self):
        """测试初始化"""
        handler = AsyncStreamingCallbackHandler()

        assert handler._async_queue == []

    def test_on_llm_new_token_async(self):
        """测试异步 token 生成"""
        tokens = []
        handler = AsyncStreamingCallbackHandler(
            output_callback=lambda t: tokens.append(t)
        )

        handler.on_llm_start({}, ["test"])
        # 使用同步方法测试，因为异步方法需要 await
        handler.on_llm_new_token("test")

        assert handler._current_response == "test"
        assert "test" in tokens

    @pytest.mark.asyncio
    async def test_on_llm_new_token_async_with_async_callback(self):
        """测试异步回调"""
        tokens = []

        async def async_callback(token):
            tokens.append(token)

        handler = AsyncStreamingCallbackHandler(
            output_callback=async_callback
        )

        handler.on_llm_start({}, ["test"])
        await handler.on_llm_new_token_async("test")

        assert "test" in tokens

    @pytest.mark.asyncio
    async def test_on_llm_new_token_async_not_streaming(self):
        """测试非流式状态下的异步 token"""
        tokens = []
        handler = AsyncStreamingCallbackHandler(
            output_callback=lambda t: tokens.append(t)
        )

        # 不调用 on_llm_start
        await handler.on_llm_new_token_async("test")

        assert tokens == []

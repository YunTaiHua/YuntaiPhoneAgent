"""
流式输出回调处理器模块
======================

本模块实现流式输出回调处理器，用于实时捕获 LLM 生成的 token 并输出到 GUI。

主要功能：
    - 实时捕获 LLM 生成的每个 token
    - 支持打字机效果（逐字显示）
    - 提供 Qt 信号机制支持
    - 支持异步流式输出

类说明：
    - StreamingCallbackHandler: 基础流式输出处理器
    - QtStreamingCallbackHandler: PyQt GUI 专用流式输出处理器
    - AsyncStreamingCallbackHandler: 异步流式输出处理器

使用示例：
    >>> from yuntai.callbacks import StreamingCallbackHandler
    >>> 
    >>> # 创建处理器
    >>> handler = StreamingCallbackHandler(
    ...     output_callback=lambda token: print(token, end=''),
    ...     enable_typewriter=True
    ... )
    >>> 
    >>> # 在模型调用时使用
    >>> response = model.invoke(messages, config={"callbacks": [handler]})
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


@runtime_checkable
class SignalProtocol(Protocol):
    """
    Qt 信号协议
    
    定义 Qt 信号需要实现的接口，用于类型注解。
    避免直接依赖 PyQt6 类型，提高代码可移植性。
    
    使用示例：
        >>> def setup_handler(signal: SignalProtocol):
        ...     signal.emit("message")
    """
    def emit(self, value: str) -> None:
        """发送信号"""
        ...


class StreamingCallbackHandler(BaseCallbackHandler):
    """
    流式输出回调处理器
    
    用于实时捕获 LLM 生成的 token 并输出到 GUI。
    支持打字机效果，可以设置输出回调和完成回调。
    
    Attributes:
        output_callback: token 输出回调函数
        complete_callback: 完成回调函数
        enable_typewriter: 是否启用打字机效果
        _current_response: 当前收集的响应内容
        _is_streaming: 是否正在流式输出
    
    使用示例：
        >>> def on_token(token):
        ...     print(token, end='', flush=True)
        >>> handler = StreamingCallbackHandler(output_callback=on_token)
    """

    def __init__(
        self,
        output_callback: Callable[[str], None] | None = None,
        complete_callback: Callable[[str], None] | None = None,
        enable_typewriter: bool = True
    ) -> None:
        """
        初始化流式输出处理器
        
        Args:
            output_callback: token 输出回调函数，接收每个 token
            complete_callback: 完成回调函数，接收完整响应
            enable_typewriter: 是否启用打字机效果（逐字显示），默认为 True
        """
        super().__init__()
        # token 输出回调函数
        self.output_callback = output_callback
        # 完成回调函数
        self.complete_callback = complete_callback
        # 是否启用打字机效果
        self.enable_typewriter = enable_typewriter
        
        # 用于收集完整响应
        self._current_response = ""
        # 是否正在流式输出
        self._is_streaming = False
        
        logger.debug("StreamingCallbackHandler 初始化完成")
        
    def on_llm_start(
        self,
        serialized: dict[str, object],
        prompts: list[str],
        **kwargs: object
    ) -> None:
        """
        LLM 开始调用时触发
        
        重置响应收集器和流式输出状态。
        
        Args:
            serialized: 序列化的模型信息
            prompts: 提示词列表
            **kwargs: 其他参数
        """
        logger.debug("LLM 开始调用，重置响应收集器")
        # 重置响应收集器
        self._current_response = ""
        # 设置流式输出状态
        self._is_streaming = True
        
    def on_llm_new_token(self, token: str, **kwargs: object) -> None:
        """
        新 token 生成时触发
        
        这是实现流式输出的关键方法。收集每个 token 并调用输出回调。
        
        Args:
            token: 新生成的 token
            **kwargs: 其他参数
        """
        # 检查是否正在流式输出
        if not self._is_streaming:
            return
            
        # 收集 token
        self._current_response += token
        
        # 调用输出回调
        if self.output_callback:
            try:
                self.output_callback(token)
            except Exception as e:
                # 回调失败时记录日志并打印警告
                logger.warning("流式输出回调失败: %s", str(e))
                print(f"⚠️ 流式输出回调失败: {e}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        """
        LLM 调用结束时触发
        
        调用完成回调函数，传递完整的响应内容。
        
        Args:
            response: LLM 响应结果
            **kwargs: 其他参数
        """
        logger.debug("LLM 调用结束，响应长度: %d", len(self._current_response))
        # 重置流式输出状态
        self._is_streaming = False

        # 调用完成回调
        if self.complete_callback and self._current_response:
            try:
                self.complete_callback(self._current_response)
            except Exception as e:
                # 回调失败时记录日志并打印警告
                logger.warning("完成回调失败: %s", str(e))
                print(f"⚠️ 完成回调失败: {e}")
    
    def on_llm_error(self, error: Exception, **kwargs: object) -> None:
        """
        LLM 调用出错时触发
        
        记录错误信息并重置流式输出状态。
        
        Args:
            error: 异常对象
            **kwargs: 其他参数
        """
        logger.error("LLM 调用错误: %s", str(error))
        # 重置流式输出状态
        self._is_streaming = False
        print(f"❌ LLM 调用错误: {error}")
        
    def get_current_response(self) -> str:
        """
        获取当前收集的响应
        
        Returns:
            当前收集的完整响应内容
        """
        return self._current_response
    
    def reset(self) -> None:
        """
        重置状态
        
        清空响应收集器并重置流式输出状态。
        """
        logger.debug("重置 StreamingCallbackHandler 状态")
        self._current_response = ""
        self._is_streaming = False


class QtStreamingCallbackHandler(StreamingCallbackHandler):
    """
    Qt 流式输出回调处理器
    
    专为 PyQt GUI 设计的流式输出处理器，使用 Qt 信号机制实现线程安全的 GUI 更新。
    继承自 StreamingCallbackHandler，重写 token 输出和完成方法以使用 Qt 信号。
    
    Attributes:
        append_signal: PyQt Signal 用于追加文本
        complete_signal: PyQt Signal 用于完成通知
    
    使用示例：
        >>> from PyQt5.QtCore import pyqtSignal
        >>> 
        >>> class MyWidget(QWidget):
        ...     append_signal = pyqtSignal(str)
        ...     
        ...     def setup_handler(self):
        ...         handler = QtStreamingCallbackHandler(
        ...             append_signal=self.append_signal
        ...         )
    """

    def __init__(
        self,
        append_signal: SignalProtocol | None = None,
        complete_signal: SignalProtocol | None = None,
        enable_typewriter: bool = True
    ) -> None:
        """
        初始化 Qt 流式输出处理器
        
        Args:
            append_signal: PyQt Signal 用于追加文本，需要是 str 类型的信号
            complete_signal: PyQt Signal 用于完成通知，需要是 str 类型的信号
            enable_typewriter: 是否启用打字机效果
        """
        super().__init__(enable_typewriter=enable_typewriter)
        # PyQt 追加文本信号
        self.append_signal: SignalProtocol | None = append_signal
        # PyQt 完成信号
        self.complete_signal: SignalProtocol | None = complete_signal
        
        logger.debug("QtStreamingCallbackHandler 初始化完成")
        
    def on_llm_new_token(self, token: str, **kwargs: object) -> None:
        """
        新 token 生成时触发，使用 Qt 信号更新 GUI
        
        Args:
            token: 新生成的 token
            **kwargs: 其他参数
        """
        # 检查是否正在流式输出
        if not self._is_streaming:
            return
            
        # 收集 token
        self._current_response += token
        
        # 使用 Qt 信号更新 GUI
        if self.append_signal:
            try:
                self.append_signal.emit(token)
            except Exception as e:
                # 信号发送失败时记录日志并打印警告
                logger.warning("Qt 信号发送失败: %s", str(e))
                print(f"⚠️ Qt 信号发送失败: {e}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        """
        LLM 调用结束时触发，使用 Qt 信号通知完成
        
        Args:
            response: LLM 响应结果
            **kwargs: 其他参数
        """
        logger.debug("LLM 调用结束（Qt），响应长度: %d", len(self._current_response))
        # 重置流式输出状态
        self._is_streaming = False
        
        # 使用 Qt 信号通知完成
        if self.complete_signal and self._current_response:
            try:
                self.complete_signal.emit(self._current_response)
            except Exception as e:
                # 信号发送失败时记录日志并打印警告
                logger.warning("Qt 完成信号发送失败: %s", str(e))
                print(f"⚠️ Qt 完成信号发送失败: {e}")


class AsyncStreamingCallbackHandler(StreamingCallbackHandler):
    """
    异步流式输出回调处理器
    
    用于异步场景下的流式输出，支持异步回调函数。
    继承自 StreamingCallbackHandler，提供异步 token 处理能力。
    
    Attributes:
        _async_queue: 异步 token 队列
    
    使用示例：
        >>> import asyncio
        >>> 
        >>> async def on_token_async(token):
        ...     await some_async_operation(token)
        >>> 
        >>> handler = AsyncStreamingCallbackHandler(
        ...     output_callback=on_token_async
        ... )
    """

    def __init__(
        self,
        output_callback: Callable[[str], None] | None = None,
        complete_callback: Callable[[str], None] | None = None,
        enable_typewriter: bool = True
    ) -> None:
        """
        初始化异步流式输出处理器
        
        Args:
            output_callback: token 输出回调函数，可以是异步函数
            complete_callback: 完成回调函数
            enable_typewriter: 是否启用打字机效果
        """
        super().__init__(output_callback, complete_callback, enable_typewriter)
        # 异步 token 队列
        self._async_queue = []
        
        logger.debug("AsyncStreamingCallbackHandler 初始化完成")
        
    async def on_llm_new_token_async(self, token: str, **kwargs: object) -> None:
        """
        异步处理新 token
        
        异步版本的 token 处理方法，支持异步回调函数。
        
        Args:
            token: 新生成的 token
            **kwargs: 其他参数
        """
        # 检查是否正在流式输出
        if not self._is_streaming:
            return
            
        # 收集 token
        self._current_response += token
        # 添加到异步队列
        self._async_queue.append(token)
        
        # 调用输出回调
        if self.output_callback:
            try:
                if callable(self.output_callback):
                    # 检查是否是异步回调
                    if asyncio.iscoroutinefunction(self.output_callback):
                        # 异步调用
                        await self.output_callback(token)
                    else:
                        # 同步调用
                        self.output_callback(token)
            except Exception as e:
                # 回调失败时记录日志并打印警告
                logger.warning("异步流式输出回调失败: %s", str(e))
                print(f"⚠️ 异步流式输出回调失败: {e}")

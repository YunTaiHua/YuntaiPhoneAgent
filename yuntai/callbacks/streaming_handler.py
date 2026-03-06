"""
流式输出回调处理器
实现真正的流式输出到 GUI，支持打字机效果
"""
from typing import Any, Dict, List, Optional, Callable
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class StreamingCallbackHandler(BaseCallbackHandler):
    """
    流式输出回调处理器
    
    用于实时捕获 LLM 生成的 token 并输出到 GUI
    实现真正的流式输出效果
    """
    
    def __init__(
        self,
        output_callback: Optional[Callable[[str], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        enable_typewriter: bool = True
    ):
        """
        初始化流式输出处理器
        
        Args:
            output_callback: token 输出回调函数，接收每个 token
            complete_callback: 完成回调函数，接收完整响应
            enable_typewriter: 是否启用打字机效果（逐字显示）
        """
        super().__init__()
        self.output_callback = output_callback
        self.complete_callback = complete_callback
        self.enable_typewriter = enable_typewriter
        
        # 用于收集完整响应
        self._current_response = ""
        self._is_streaming = False
        
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """LLM 开始调用时触发"""
        self._current_response = ""
        self._is_streaming = True
        
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """
        新 token 生成时触发
        
        这是实现流式输出的关键方法
        """
        if not self._is_streaming:
            return
            
        # 收集 token
        self._current_response += token
        
        # 调用输出回调
        if self.output_callback:
            try:
                self.output_callback(token)
            except Exception as e:
                print(f"⚠️ 流式输出回调失败: {e}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束时触发"""
        self._is_streaming = False
        
        # 调用完成回调
        if self.complete_callback and self._current_response:
            try:
                self.complete_callback(self._current_response)
            except Exception as e:
                print(f"⚠️ 完成回调失败: {e}")
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """LLM 调用出错时触发"""
        self._is_streaming = False
        print(f"❌ LLM 调用错误: {error}")
        
    def get_current_response(self) -> str:
        """获取当前收集的响应"""
        return self._current_response
    
    def reset(self):
        """重置状态"""
        self._current_response = ""
        self._is_streaming = False


class QtStreamingCallbackHandler(StreamingCallbackHandler):
    """
    专为 PyQt GUI 设计的流式输出处理器
    
    使用 Qt 信号机制实现线程安全的 GUI 更新
    """
    
    def __init__(
        self,
        append_signal=None,
        complete_signal=None,
        enable_typewriter: bool = True
    ):
        """
        初始化 Qt 流式输出处理器
        
        Args:
            append_signal: PyQt Signal 用于追加文本
            complete_signal: PyQt Signal 用于完成通知
            enable_typewriter: 是否启用打字机效果
        """
        super().__init__(enable_typewriter=enable_typewriter)
        self.append_signal = append_signal
        self.complete_signal = complete_signal
        
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """新 token 生成时触发，使用 Qt 信号更新 GUI"""
        if not self._is_streaming:
            return
            
        self._current_response += token
        
        # 使用 Qt 信号更新 GUI
        if self.append_signal:
            try:
                self.append_signal.emit(token)
            except Exception as e:
                print(f"⚠️ Qt 信号发送失败: {e}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束时触发"""
        self._is_streaming = False
        
        # 使用 Qt 信号通知完成
        if self.complete_signal and self._current_response:
            try:
                self.complete_signal.emit(self._current_response)
            except Exception as e:
                print(f"⚠️ Qt 完成信号发送失败: {e}")


class AsyncStreamingCallbackHandler(StreamingCallbackHandler):
    """
    异步流式输出处理器
    
    用于异步场景下的流式输出
    """
    
    def __init__(
        self,
        output_callback: Optional[Callable[[str], None]] = None,
        complete_callback: Optional[Callable[[str], None]] = None,
        enable_typewriter: bool = True
    ):
        super().__init__(output_callback, complete_callback, enable_typewriter)
        self._async_queue = []
        
    async def on_llm_new_token_async(self, token: str, **kwargs: Any) -> None:
        """异步处理新 token"""
        if not self._is_streaming:
            return
            
        self._current_response += token
        self._async_queue.append(token)
        
        if self.output_callback:
            try:
                if callable(self.output_callback):
                    # 如果是异步回调
                    import asyncio
                    if asyncio.iscoroutinefunction(self.output_callback):
                        await self.output_callback(token)
                    else:
                        self.output_callback(token)
            except Exception as e:
                print(f"⚠️ 异步流式输出回调失败: {e}")

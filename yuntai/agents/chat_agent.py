"""聊天 Agent，使用 ZHIPU_CHAT_MODEL 进行自由聊天，支持 LangChain Callbacks 实现流式输出"""
from collections.abc import Callable

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler

from yuntai.models import get_chat_model, get_zhipu_client
from yuntai.prompts import CHAT_SYSTEM_PROMPT, CHAT_WITH_CONTEXT_PROMPT
from yuntai.tools import get_current_time_info
from yuntai.callbacks import StreamingCallbackHandler, get_callback_manager


class ChatAgent:
    """聊天 Agent - 支持 Callbacks 流式输出"""
    
    def __init__(
        self,
        model: BaseChatModel | None = None,
        file_manager: object = None,
        tts_manager: object = None,
        enable_streaming: bool = True
    ) -> None:
        self.model = model or get_chat_model()
        self.zhipu_client = get_zhipu_client()
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        self.system_prompt = CHAT_SYSTEM_PROMPT
        self.enable_streaming = enable_streaming
        
        # 回调管理器
        self.callback_manager = get_callback_manager()
        
        # 流式输出回调（可外部设置）
        self._streaming_callback: Callable[[str], None] | None = None
        self._complete_callback: Callable[[str], None] | None = None

    def set_streaming_callback(self, callback: Callable[[str], None]) -> None:
        """设置流式输出回调函数"""
        self._streaming_callback = callback

    def set_complete_callback(self, callback: Callable[[str], None]) -> None:
        """设置完成回调函数"""
        self._complete_callback = callback
    
    def chat(
        self,
        user_input: str,
        include_memory: bool = True,
        callbacks: list[BaseCallbackHandler] | None = None,
        enable_streaming: bool | None = None
    ) -> str:
        """
        进行自由聊天（支持流式输出）
        
        Args:
            user_input: 用户输入
            include_memory: 是否包含记忆
            callbacks: 自定义回调处理器列表
            enable_streaming: 是否启用流式输出（None 则使用实例设置）
        
        Returns:
            回复内容
        """
        # 确定是否启用流式输出
        use_streaming = enable_streaming if enable_streaming is not None else self.enable_streaming
        
        time_info = get_current_time_info()
        
        context_parts = []
        
        if include_memory and self.file_manager:
            forever_memory = self.file_manager.read_forever_memory()
            if forever_memory:
                context_parts.append(f"=== 永久记忆 ===\n{forever_memory}")
            
            chat_history = self.file_manager.get_recent_free_chats(limit=5)
            if chat_history:
                history_text = "=== 最近对话 ===\n"
                for i, chat in enumerate(chat_history):
                    history_text += f"{i+1}. 用户: {chat.get('user_input', '')}\n"
                    history_text += f"   助手: {chat.get('assistant_reply', '')}\n"
                context_parts.append(history_text)
        
        context = "\n".join(context_parts)
        
        prompt = CHAT_WITH_CONTEXT_PROMPT.format(
            time_info=time_info,
            forever_memory=context,
            chat_history="",
            user_input=user_input
        )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        try:
            # 准备回调处理器
            all_callbacks = self._prepare_callbacks(callbacks, use_streaming)
            
            # 使用回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 调用模型
            response = self.model.invoke(messages, config=config)
            
            reply = response.content.strip()
            
            # 保存对话历史
            if self.file_manager:
                import datetime
                session_data = {
                    "type": "free_chat",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_input": user_input,
                    "assistant_reply": reply,
                }
                self.file_manager.save_conversation_history(session_data)
            
            # TTS 播报
            if self.tts_manager and self.tts_manager.tts_enabled and len(reply) > 5:
                import threading
                threading.Timer(0.5, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
            
            return reply
            
        except Exception as e:
            return f"聊天失败: {str(e)}"
    
    def _prepare_callbacks(
        self,
        callbacks: list[BaseCallbackHandler] | None = None,
        enable_streaming: bool = True
    ) -> list[BaseCallbackHandler]:
        """
        准备回调处理器列表
        
        Args:
            callbacks: 用户提供的回调列表
            enable_streaming: 是否启用流式输出
        
        Returns:
            合并后的回调处理器列表
        """
        all_callbacks = []
        
        # 添加全局回调
        global_callbacks = self.callback_manager.get_callbacks(include_global=True)
        all_callbacks.extend(global_callbacks)
        
        # 添加流式输出回调
        if enable_streaming and (self._streaming_callback or self._complete_callback):
            streaming_handler = StreamingCallbackHandler(
                output_callback=self._streaming_callback,
                complete_callback=self._complete_callback
            )
            all_callbacks.append(streaming_handler)
        
        # 添加用户提供的回调
        if callbacks:
            all_callbacks.extend(callbacks)
        
        return all_callbacks
    
    def chat_with_history(
        self,
        user_input: str,
        history: list[dict[str, str]],
        callbacks: list[BaseCallbackHandler] | None = None,
        enable_streaming: bool | None = None
    ) -> str:
        """
        带历史记录的聊天（支持流式输出）
        
        Args:
            user_input: 用户输入
            history: 历史记录列表
            callbacks: 自定义回调处理器列表
            enable_streaming: 是否启用流式输出
        
        Returns:
            回复内容
        """
        # 确定是否启用流式输出
        use_streaming = enable_streaming if enable_streaming is not None else self.enable_streaming
        
        messages = [SystemMessage(content=self.system_prompt)]
        
        for msg in history[-10:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg.get("content", "")))
        
        messages.append(HumanMessage(content=user_input))
        
        try:
            # 准备回调处理器
            all_callbacks = self._prepare_callbacks(callbacks, use_streaming)
            
            # 使用回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 调用模型
            response = self.model.invoke(messages, config=config)
            
            return response.content.strip()
        except Exception as e:
            return f"聊天失败: {str(e)}"
    
    def chat_stream(
        self,
        user_input: str,
        include_memory: bool = True,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> None:
        """
        流式聊天（返回生成器）
        
        Args:
            user_input: 用户输入
            include_memory: 是否包含记忆
            callbacks: 自定义回调处理器列表
        
        Yields:
            str: 每个 token
        """
        time_info = get_current_time_info()
        
        context_parts = []
        
        if include_memory and self.file_manager:
            forever_memory = self.file_manager.read_forever_memory()
            if forever_memory:
                context_parts.append(f"=== 永久记忆 ===\n{forever_memory}")
            
            chat_history = self.file_manager.get_recent_free_chats(limit=5)
            if chat_history:
                history_text = "=== 最近对话 ===\n"
                for i, chat in enumerate(chat_history):
                    history_text += f"{i+1}. 用户: {chat.get('user_input', '')}\n"
                    history_text += f"   助手: {chat.get('assistant_reply', '')}\n"
                context_parts.append(history_text)
        
        context = "\n".join(context_parts)
        
        prompt = CHAT_WITH_CONTEXT_PROMPT.format(
            time_info=time_info,
            forever_memory=context,
            chat_history="",
            user_input=user_input
        )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        try:
            # 准备回调处理器
            all_callbacks = self._prepare_callbacks(callbacks, enable_streaming=True)
            
            # 使用回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 使用流式输出
            for chunk in self.model.stream(messages, config=config):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            yield f"聊天失败: {str(e)}"

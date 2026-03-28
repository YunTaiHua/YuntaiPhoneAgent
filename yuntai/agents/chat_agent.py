"""
聊天 Agent 模块
===============

本模块实现聊天 Agent，使用 ZHIPU_CHAT_MODEL 进行自由聊天，支持 LangChain Callbacks 实现流式输出。

主要功能：
    - 自由对话：支持与用户进行自然语言对话
    - 记忆集成：可集成永久记忆和对话历史
    - 流式输出：支持实时流式输出响应内容
    - TTS 集成：支持将回复转换为语音播报

类说明：
    - ChatAgent: 聊天 Agent 类，提供多种聊天方法

使用示例：
    >>> from yuntai.agents import ChatAgent
    >>> 
    >>> # 创建聊天 Agent
    >>> agent = ChatAgent()
    >>> 
    >>> # 进行对话
    >>> reply = agent.chat("你好，今天天气怎么样？")
    >>> print(reply)
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler

from yuntai.models import get_chat_model, get_zhipu_client
from yuntai.prompts import CHAT_SYSTEM_PROMPT, CHAT_WITH_CONTEXT_PROMPT
from yuntai.tools import get_current_time_info
from yuntai.tools.callback_utils import prepare_callbacks_with_manager
from yuntai.callbacks import get_callback_manager
from yuntai.core.config import (
    RECENT_CHATS_LIMIT,
    TTS_MIN_REPLY_LENGTH,
    TTS_SPEAK_DELAY_REPLY,
    HISTORY_CONTEXT_LIMIT,
)

# 类型检查时导入，避免运行时循环导入
if TYPE_CHECKING:
    from yuntai.services.file_manager import FileManager
    from yuntai.services.task_manager import TTSManager

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class ChatAgent:
    """
    聊天 Agent 类
    
    支持 Callbacks 流式输出，可集成文件管理和 TTS 功能。
    提供多种聊天方法，支持带记忆和不带记忆的对话模式。
    
    Attributes:
        model: LangChain 聊天模型实例
        zhipu_client: 智谱 AI 客户端实例
        file_manager: 文件管理器实例，用于读写记忆
        tts_manager: TTS 管理器实例，用于语音播报
        system_prompt: 系统提示词
        enable_streaming: 是否启用流式输出
        callback_manager: 回调管理器实例
    
    使用示例：
        >>> agent = ChatAgent(enable_streaming=True)
        >>> agent.set_streaming_callback(lambda token: print(token, end=''))
        >>> reply = agent.chat("你好")
    """
    
    def __init__(
        self,
        model: BaseChatModel | None = None,
        file_manager: FileManager | None = None,
        tts_manager: TTSManager | None = None,
        enable_streaming: bool = True
    ) -> None:
        """
        初始化聊天 Agent
        
        Args:
            model: LangChain 聊天模型实例，如果为 None 则使用默认模型
            file_manager: 文件管理器实例，用于读写记忆和对话历史
            tts_manager: TTS 管理器实例，用于语音播报回复
            enable_streaming: 是否启用流式输出，默认为 True
        """
        # 初始化模型，使用默认模型或传入的模型
        self.model = model or get_chat_model()
        # 获取智谱 AI 客户端
        self.zhipu_client = get_zhipu_client()
        # 文件管理器，用于读写记忆
        self.file_manager = file_manager
        # TTS 管理器，用于语音播报
        self.tts_manager = tts_manager
        # 系统提示词
        self.system_prompt = CHAT_SYSTEM_PROMPT
        # 是否启用流式输出
        self.enable_streaming = enable_streaming
        
        # 获取回调管理器单例
        self.callback_manager = get_callback_manager()
        
        # 流式输出回调函数（可外部设置）
        self._streaming_callback: Callable[[str], None] | None = None
        # 完成回调函数（可外部设置）
        self._complete_callback: Callable[[str], None] | None = None
        
        logger.debug("ChatAgent 初始化完成，流式输出: %s", enable_streaming)

    def set_streaming_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置流式输出回调函数
        
        当启用流式输出时，每生成一个 token 就会调用此回调函数。
        
        Args:
            callback: 回调函数，接收每个 token 作为参数
        
        使用示例：
            >>> def on_token(token):
            ...     print(token, end='', flush=True)
            >>> agent.set_streaming_callback(on_token)
        """
        self._streaming_callback = callback
        logger.debug("已设置流式输出回调函数")

    def set_complete_callback(self, callback: Callable[[str], None]) -> None:
        """
        设置完成回调函数
        
        当响应生成完成时调用此回调函数。
        
        Args:
            callback: 回调函数，接收完整响应作为参数
        
        使用示例：
            >>> def on_complete(response):
            ...     print(f"\\n完成: {len(response)} 字符")
            >>> agent.set_complete_callback(on_complete)
        """
        self._complete_callback = callback
        logger.debug("已设置完成回调函数")
    
    def chat(
        self,
        user_input: str,
        include_memory: bool = True,
        callbacks: list[BaseCallbackHandler] | None = None,
        enable_streaming: bool | None = None
    ) -> str:
        """
        进行自由聊天（支持流式输出）
        
        主要的聊天入口方法，支持记忆集成和流式输出。
        
        Args:
            user_input: 用户输入的文本
            include_memory: 是否包含记忆上下文，默认为 True
            callbacks: 自定义回调处理器列表，可选
            enable_streaming: 是否启用流式输出，None 则使用实例设置
        
        Returns:
            生成的回复内容，失败时返回错误信息字符串
        
        使用示例：
            >>> reply = agent.chat("你好", include_memory=True)
            >>> print(reply)
        """
        # 确定是否启用流式输出
        use_streaming = enable_streaming if enable_streaming is not None else self.enable_streaming
        
        logger.info("开始聊天，用户输入: %s...", user_input[:50] if len(user_input) > 50 else user_input)
        
        # 获取当前时间信息
        time_info = get_current_time_info()
        
        # 构建上下文部分
        context_parts = []
        
        # 如果启用记忆且存在文件管理器，加载记忆上下文
        if include_memory and self.file_manager:
            # 加载永久记忆
            forever_memory = self.file_manager.read_forever_memory()
            if forever_memory:
                context_parts.append(f"=== 永久记忆 ===\n{forever_memory}")
                logger.debug("已加载永久记忆: %d 字符", len(forever_memory))
            
            # 加载最近的自由对话历史
            chat_history = self.file_manager.get_recent_free_chats(limit=RECENT_CHATS_LIMIT)
            if chat_history:
                history_text = "=== 最近对话 ===\n"
                for i, chat in enumerate(chat_history):
                    history_text += f"{i+1}. 用户: {chat.get('user_input', '')}\n"
                    history_text += f"   助手: {chat.get('assistant_reply', '')}\n"
                context_parts.append(history_text)
                logger.debug("已加载 %d 条历史对话", len(chat_history))
        
        # 合并上下文
        context = "\n".join(context_parts)
        
        # 构建提示词
        prompt = CHAT_WITH_CONTEXT_PROMPT.format(
            time_info=time_info,
            forever_memory=context,
            chat_history="",
            user_input=user_input
        )
        
        # 构建消息列表
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        try:
            # 准备回调处理器
            all_callbacks = prepare_callbacks_with_manager(
                self.callback_manager,
                callbacks=callbacks,
                streaming_callback=self._streaming_callback,
                complete_callback=self._complete_callback,
                enable_streaming=use_streaming
            )
            
            # 构建回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 调用模型生成回复
            response = self.model.invoke(messages, config=config)
            
            # 提取并清理回复内容
            reply = response.content.strip()
            
            # 保存对话历史到文件
            if self.file_manager:
                import datetime
                session_data = {
                    "type": "free_chat",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_input": user_input,
                    "assistant_reply": reply,
                }
                self.file_manager.save_conversation_history(session_data)
                logger.debug("已保存对话历史")
            
            # TTS 语音播报（如果启用且回复足够长）
            if self.tts_manager and self.tts_manager.tts_enabled and len(reply) > TTS_MIN_REPLY_LENGTH:
                import threading
                # 延迟播报，避免与流式输出冲突
                threading.Timer(TTS_SPEAK_DELAY_REPLY, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
                logger.debug("已安排 TTS 播报")
            
            logger.info("聊天完成，回复长度: %d 字符", len(reply))
            return reply
            
        except Exception as e:
            # 记录错误日志
            logger.error("聊天失败: %s", str(e), exc_info=True)
            return f"聊天失败: {str(e)}"
    
    def chat_with_history(
        self,
        user_input: str,
        history: list[dict[str, str]],
        callbacks: list[BaseCallbackHandler] | None = None,
        enable_streaming: bool | None = None
    ) -> str:
        """
        带历史记录的聊天（支持流式输出）
        
        与 chat 方法类似，但直接传入历史记录而不是从文件管理器加载。
        适用于需要自定义历史记录的场景。
        
        Args:
            user_input: 用户输入的文本
            history: 历史记录列表，每条记录包含 role 和 content 字段
            callbacks: 自定义回调处理器列表，可选
            enable_streaming: 是否启用流式输出，None 则使用实例设置
        
        Returns:
            生成的回复内容，失败时返回错误信息字符串
        
        使用示例：
            >>> history = [
            ...     {"role": "user", "content": "你好"},
            ...     {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
            ... ]
            >>> reply = agent.chat_with_history("今天天气怎么样？", history)
        """
        # 确定是否启用流式输出
        use_streaming = enable_streaming if enable_streaming is not None else self.enable_streaming
        
        logger.info("开始带历史的聊天，历史记录数: %d", len(history))
        
        # 构建消息列表，以系统提示词开始
        messages = [SystemMessage(content=self.system_prompt)]
        
        # 添加历史消息（限制数量）
        for msg in history[-HISTORY_CONTEXT_LIMIT:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg.get("content", "")))
        
        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))
        
        try:
            # 准备回调处理器
            all_callbacks = prepare_callbacks_with_manager(
                self.callback_manager,
                callbacks=callbacks,
                streaming_callback=self._streaming_callback,
                complete_callback=self._complete_callback,
                enable_streaming=use_streaming
            )
            
            # 构建回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 调用模型生成回复
            response = self.model.invoke(messages, config=config)
            
            logger.info("带历史的聊天完成")
            return response.content.strip()
        except Exception as e:
            # 记录错误日志
            logger.error("带历史的聊天失败: %s", str(e), exc_info=True)
            return f"聊天失败: {str(e)}"
    
    def chat_stream(
        self,
        user_input: str,
        include_memory: bool = True,
        callbacks: list[BaseCallbackHandler] | None = None
    ):
        """
        流式聊天（返回生成器）
        
        以生成器形式返回响应，适用于需要逐 token 处理的场景。
        
        Args:
            user_input: 用户输入的文本
            include_memory: 是否包含记忆上下文，默认为 True
            callbacks: 自定义回调处理器列表，可选
        
        Yields:
            str: 每次生成的一个 token
        
        使用示例：
            >>> for token in agent.chat_stream("你好"):
            ...     print(token, end='', flush=True)
        """
        logger.info("开始流式聊天")
        
        # 获取当前时间信息
        time_info = get_current_time_info()
        
        # 构建上下文部分
        context_parts = []
        
        # 如果启用记忆且存在文件管理器，加载记忆上下文
        if include_memory and self.file_manager:
            forever_memory = self.file_manager.read_forever_memory()
            if forever_memory:
                context_parts.append(f"=== 永久记忆 ===\n{forever_memory}")
            
            chat_history = self.file_manager.get_recent_free_chats(limit=RECENT_CHATS_LIMIT)
            if chat_history:
                history_text = "=== 最近对话 ===\n"
                for i, chat in enumerate(chat_history):
                    history_text += f"{i+1}. 用户: {chat.get('user_input', '')}\n"
                    history_text += f"   助手: {chat.get('assistant_reply', '')}\n"
                context_parts.append(history_text)
        
        # 合并上下文
        context = "\n".join(context_parts)
        
        # 构建提示词
        prompt = CHAT_WITH_CONTEXT_PROMPT.format(
            time_info=time_info,
            forever_memory=context,
            chat_history="",
            user_input=user_input
        )
        
        # 构建消息列表
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        try:
            # 准备回调处理器
            all_callbacks = prepare_callbacks_with_manager(
                self.callback_manager,
                callbacks=callbacks,
                streaming_callback=self._streaming_callback,
                complete_callback=self._complete_callback,
                enable_streaming=True
            )
            
            # 构建回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 使用流式输出
            for chunk in self.model.stream(messages, config=config):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            # 记录错误日志
            logger.error("流式聊天失败: %s", str(e), exc_info=True)
            yield f"聊天失败: {str(e)}"

"""
对话记忆管理模块
================

使用 LangChain 记忆管理机制，支持 LangChain Callbacks 自动记录对话历史。

主要组件:
    - ConversationMemoryManager: 对话记忆管理器
    - FreeChatMemory: 自由聊天记忆
    - ChatSessionMemory: 聊天会话记忆

使用示例:
    >>> from yuntai.memory import ConversationMemoryManager
    >>> manager = ConversationMemoryManager(
    ...     history_file="history.json",
    ...     forever_memory_file="forever.txt"
    ... )
    >>> manager.add_message("user", "你好")
    >>> manager.add_message("assistant", "你好！有什么可以帮助你的？")
"""
import json
import logging
from datetime import datetime
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import FileChatMessageHistory

from yuntai.callbacks import get_callback_manager

logger = logging.getLogger(__name__)


class ConversationMemoryManager:
    """
    对话记忆管理器
    
    支持 Callbacks 自动记录对话历史，集成 LangChain 记忆机制。
    
    Attributes:
        history_file: 历史记录文件路径
        forever_memory_file: 永久记忆文件路径
        max_history_length: 最大历史记录长度
        callback_manager: 回调管理器实例
        
    Args:
        history_file: 历史记录文件路径
        forever_memory_file: 永久记忆文件路径
        max_history_length: 最大历史记录长度，默认为 50
    """
    
    def __init__(
        self,
        history_file: str = "",
        forever_memory_file: str = "",
        max_history_length: int = 50
    ):
        self.history_file = history_file
        self.forever_memory_file = forever_memory_file
        self.max_history_length = max_history_length
        
        self.callback_manager = get_callback_manager()
        
        self._memory: ConversationBufferMemory | None = None
        self._forever_memory: str = ""
        
        if history_file and Path(history_file).exists():
            self._load_memory()
        
        if forever_memory_file and Path(forever_memory_file).exists():
            self._load_forever_memory()
        
        self._setup_memory_callback()
        logger.debug(f"ConversationMemoryManager 初始化完成, history_file={history_file}")
    
    def _load_memory(self) -> None:
        """加载记忆"""
        try:
            self._memory = ConversationBufferMemory(
                chat_memory=FileChatMessageHistory(self.history_file),
                return_messages=True
            )
            logger.debug(f"加载记忆成功: {self.history_file}")
        except Exception as e:
            logger.warning(f"加载记忆失败: {e}")
            self._memory = ConversationBufferMemory(return_messages=True)
    
    def _load_forever_memory(self) -> None:
        """加载永久记忆"""
        try:
            self._forever_memory = Path(self.forever_memory_file).read_text(encoding='utf-8').strip()
            logger.debug(f"加载永久记忆成功: {self.forever_memory_file}")
        except Exception as e:
            logger.warning(f"加载永久记忆失败: {e}")
            self._forever_memory = ""
    
    def get_memory(self) -> ConversationBufferMemory:
        """
        获取记忆实例
        
        Returns:
            ConversationBufferMemory 实例
        """
        if self._memory is None:
            self._memory = ConversationBufferMemory(return_messages=True)
        return self._memory
    
    def get_forever_memory(self) -> str:
        """
        获取永久记忆
        
        Returns:
            永久记忆字符串
        """
        return self._forever_memory
    
    def add_message(self, role: str, content: str) -> None:
        """
        添加消息
        
        Args:
            role: 消息角色，"user" 或 "assistant"
            content: 消息内容
        """
        memory = self.get_memory()
        if role == "user":
            memory.chat_memory.add_user_message(content)
            logger.debug(f"添加用户消息: {content[:50]}...")
        elif role == "assistant":
            memory.chat_memory.add_ai_message(content)
            logger.debug(f"添加助手消息: {content[:50]}...")
    
    def get_messages(self, limit: int = 10) -> list[BaseMessage]:
        """
        获取消息列表
        
        Args:
            limit: 返回消息数量限制
            
        Returns:
            消息列表
        """
        memory = self.get_memory()
        messages = memory.chat_memory.messages
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_history_context(self, limit: int = 5) -> str:
        """
        获取历史上下文
        
        Args:
            limit: 返回消息数量限制
            
        Returns:
            格式化的历史上下文字符串
        """
        messages = self.get_messages(limit)
        context_parts = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                context_parts.append(f"用户: {msg.content}")
            elif isinstance(msg, AIMessage):
                context_parts.append(f"助手: {msg.content}")
        return "\n".join(context_parts)
    
    def clear(self) -> None:
        """清空记忆"""
        if self._memory:
            self._memory.clear()
            logger.debug("记忆已清空")
    
    def save_to_file(self, data: dict[str, object], filepath: str) -> None:
        """
        保存到文件
        
        Args:
            data: 要保存的数据字典
            filepath: 目标文件路径
        """
        try:
            existing_data = []
            file_path = Path(filepath)
            if file_path.exists():
                existing_data = json.loads(file_path.read_text(encoding='utf-8'))
            
            if not isinstance(existing_data, list):
                existing_data = []
            
            existing_data.append(data)
            
            if len(existing_data) > self.max_history_length:
                existing_data = existing_data[-self.max_history_length:]
            
            file_path.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2), encoding='utf-8')
            logger.debug(f"保存数据到文件: {filepath}")
                
        except Exception as e:
            logger.error(f"保存失败: {e}")
    
    def _setup_memory_callback(self) -> None:
        """设置记忆回调处理器"""
        from yuntai.callbacks import MemoryCallbackHandler
        
        memory_handler = MemoryCallbackHandler(
            memory_manager=self,
            auto_save=True,
            max_history=self.max_history_length
        )
        
        self.callback_manager.register_handler(
            name="conversation_memory",
            handler=memory_handler,
            is_global=True
        )
        logger.debug("记忆回调处理器已注册")
    
    def get_callbacks(self) -> list[BaseCallbackHandler]:
        """
        获取记忆相关的回调处理器
        
        Returns:
            回调处理器列表
        """
        return self.callback_manager.get_callbacks(
            include_global=True,
            handler_names=["conversation_memory"]
        )


class FreeChatMemory:
    """
    自由聊天记忆
    
    管理自由聊天模式的对话记录。
    
    Attributes:
        file_manager: 文件管理器实例
    """
    
    def __init__(self, file_manager=None):
        """
        初始化自由聊天记忆
        
        Args:
            file_manager: 文件管理器实例
        """
        self.file_manager = file_manager
    
    def get_recent_chats(self, limit: int = 5) -> list[dict[str, object]]:
        """
        获取最近的聊天记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            聊天记录列表
        """
        if not self.file_manager:
            return []
        return self.file_manager.get_recent_free_chats(limit=limit)
    
    def save_chat(self, user_input: str, assistant_reply: str) -> None:
        """
        保存聊天记录
        
        Args:
            user_input: 用户输入
            assistant_reply: 助手回复
        """
        if not self.file_manager:
            return
        
        session_data = {
            "type": "free_chat",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_input,
            "assistant_reply": assistant_reply,
        }
        self.file_manager.save_conversation_history(session_data)
        logger.debug(f"保存自由聊天记录: user_input={user_input[:30]}...")


class ChatSessionMemory:
    """
    聊天会话记忆
    
    管理特定应用的聊天会话记录。
    
    Attributes:
        file_manager: 文件管理器实例
    """
    
    def __init__(self, file_manager=None):
        """
        初始化聊天会话记忆
        
        Args:
            file_manager: 文件管理器实例
        """
        self.file_manager = file_manager
    
    def get_recent_session(self, app_name: str, chat_object: str, limit: int = 5) -> list[dict[str, object]]:
        """
        获取最近的会话记录
        
        Args:
            app_name: 应用名称
            chat_object: 聊天对象
            limit: 返回记录数量限制
            
        Returns:
            会话记录列表
        """
        if not self.file_manager:
            return []
        return self.file_manager.get_recent_conversation_history(app_name, chat_object, limit=limit)
    
    def save_session(
        self,
        app_name: str,
        chat_object: str,
        reply: str,
        other_messages: list[str],
        cycle: int = 1
    ) -> None:
        """
        保存会话记录
        
        Args:
            app_name: 应用名称
            chat_object: 聊天对象
            reply: 生成的回复
            other_messages: 其他消息列表
            cycle: 循环次数
        """
        if not self.file_manager:
            return
        
        session_data = {
            "type": "chat_session",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_app": app_name,
            "target_object": chat_object,
            "cycle": cycle,
            "reply_generated": reply,
            "other_messages": other_messages,
            "sent_success": True
        }
        self.file_manager.save_conversation_history(session_data)
        logger.debug(f"保存会话记录: app={app_name}, object={chat_object}")

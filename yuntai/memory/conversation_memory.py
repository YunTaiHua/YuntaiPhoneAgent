"""
对话记忆管理模块
使用 LangChain 记忆管理机制
支持 LangChain Callbacks 自动记录对话历史
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import FileChatMessageHistory

from yuntai.callbacks import get_callback_manager


class ConversationMemoryManager:
    """对话记忆管理器 - 支持 Callbacks 自动记录"""
    
    def __init__(
        self,
        history_file: str = "",
        forever_memory_file: str = "",
        max_history_length: int = 50
    ):
        self.history_file = history_file
        self.forever_memory_file = forever_memory_file
        self.max_history_length = max_history_length
        
        # 回调管理器
        self.callback_manager = get_callback_manager()
        
        self._memory: ConversationBufferMemory | None = None
        self._forever_memory: str = ""
        
        if history_file and Path(history_file).exists():
            self._load_memory()
        
        if forever_memory_file and Path(forever_memory_file).exists():
            self._load_forever_memory()
        
        # 注册记忆回调处理器
        self._setup_memory_callback()
    
    def _load_memory(self):
        """加载记忆"""
        try:
            self._memory = ConversationBufferMemory(
                chat_memory=FileChatMessageHistory(self.history_file),
                return_messages=True
            )
        except Exception as e:
            print(f"加载记忆失败: {e}")
            self._memory = ConversationBufferMemory(return_messages=True)
    
    def _load_forever_memory(self):
        """加载永久记忆"""
        try:
            self._forever_memory = Path(self.forever_memory_file).read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"加载永久记忆失败: {e}")
            self._forever_memory = ""
    
    def get_memory(self) -> ConversationBufferMemory:
        """获取记忆实例"""
        if self._memory is None:
            self._memory = ConversationBufferMemory(return_messages=True)
        return self._memory
    
    def get_forever_memory(self) -> str:
        """获取永久记忆"""
        return self._forever_memory
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        memory = self.get_memory()
        if role == "user":
            memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            memory.chat_memory.add_ai_message(content)
    
    def get_messages(self, limit: int = 10) -> list[BaseMessage]:
        """获取消息列表"""
        memory = self.get_memory()
        messages = memory.chat_memory.messages
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_history_context(self, limit: int = 5) -> str:
        """获取历史上下文"""
        messages = self.get_messages(limit)
        context_parts = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                context_parts.append(f"用户: {msg.content}")
            elif isinstance(msg, AIMessage):
                context_parts.append(f"助手: {msg.content}")
        return "\n".join(context_parts)
    
    def clear(self):
        """清空记忆"""
        if self._memory:
            self._memory.clear()
    
    def save_to_file(self, data: dict[str, Any], filepath: str) -> None:
        """保存到文件"""
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
                
        except Exception as e:
            print(f"保存失败: {e}")
    
    def _setup_memory_callback(self):
        """设置记忆回调处理器"""
        from yuntai.callbacks import MemoryCallbackHandler
        
        # 创建记忆回调处理器
        memory_handler = MemoryCallbackHandler(
            memory_manager=self,
            auto_save=True,
            max_history=self.max_history_length
        )
        
        # 注册为全局回调
        self.callback_manager.register_handler(
            name="conversation_memory",
            handler=memory_handler,
            is_global=True
        )
    
    def get_callbacks(self) -> list[BaseCallbackHandler]:
        """获取记忆相关的回调处理器"""
        return self.callback_manager.get_callbacks(
            include_global=True,
            handler_names=["conversation_memory"]
        )


class FreeChatMemory:
    """自由聊天记忆"""
    
    def __init__(self, file_manager=None):
        self.file_manager = file_manager
    
    def get_recent_chats(self, limit: int = 5) -> list[dict[str, Any]]:
        """获取最近的聊天记录"""
        if not self.file_manager:
            return []
        return self.file_manager.get_recent_free_chats(limit=limit)
    
    def save_chat(self, user_input: str, assistant_reply: str):
        """保存聊天记录"""
        if not self.file_manager:
            return
        
        session_data = {
            "type": "free_chat",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_input,
            "assistant_reply": assistant_reply,
        }
        self.file_manager.save_conversation_history(session_data)


class ChatSessionMemory:
    """聊天会话记忆"""
    
    def __init__(self, file_manager=None):
        self.file_manager = file_manager
    
    def get_recent_session(self, app_name: str, chat_object: str, limit: int = 5) -> list[dict[str, Any]]:
        """获取最近的会话记录"""
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
        """保存会话记录"""
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

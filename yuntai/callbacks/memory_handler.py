"""
记忆管理回调处理器
用于自动记录对话历史到记忆系统
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import HumanMessage, AIMessage


class MemoryCallbackHandler(BaseCallbackHandler):
    """
    记忆管理回调处理器
    
    自动捕获 LLM 的输入输出并记录到记忆系统
    """
    
    def __init__(
        self,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50
    ):
        """
        初始化记忆管理处理器
        
        Args:
            memory_manager: 记忆管理器实例
            auto_save: 是否自动保存到记忆
            max_history: 最大历史记录数
        """
        super().__init__()
        self.memory_manager = memory_manager
        self.auto_save = auto_save
        self.max_history = max_history
        
        # 临时存储当前对话
        self._current_user_input = ""
        self._current_ai_response = ""
        self._conversation_history = []
        
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """LLM 开始调用时，记录用户输入"""
        if prompts:
            # 提取用户输入（通常是最后一个提示词）
            self._current_user_input = prompts[-1] if prompts else ""
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束时，记录 AI 响应"""
        if response.generations and response.generations[0]:
            # 提取 AI 响应
            self._current_ai_response = response.generations[0][0].text
            
            # 自动保存到记忆
            if self.auto_save and self.memory_manager:
                self._save_to_memory()
    
    def _save_to_memory(self):
        """保存对话到记忆"""
        if not self._current_user_input or not self._current_ai_response:
            return
        
        try:
            # 添加到记忆管理器
            if hasattr(self.memory_manager, 'add_message'):
                self.memory_manager.add_message("user", self._current_user_input)
                self.memory_manager.add_message("assistant", self._current_ai_response)
            
            # 添加到历史记录
            self._conversation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user": self._current_user_input,
                "assistant": self._current_ai_response
            })
            
            # 限制历史记录长度
            if len(self._conversation_history) > self.max_history:
                self._conversation_history = self._conversation_history[-self.max_history:]
            
            # 清空当前对话
            self._current_user_input = ""
            self._current_ai_response = ""
            
        except Exception as e:
            print(f"⚠️ 保存到记忆失败: {e}")
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self._conversation_history[-limit:]
    
    def clear_history(self):
        """清空历史记录"""
        self._conversation_history = []
    
    def get_messages_for_langchain(self, limit: int = 10) -> List:
        """
        获取 LangChain 格式的消息列表
        
        Returns:
            List[HumanMessage | AIMessage]: LangChain 消息列表
        """
        messages = []
        history = self.get_conversation_history(limit)
        
        for conv in history:
            messages.append(HumanMessage(content=conv["user"]))
            messages.append(AIMessage(content=conv["assistant"]))
        
        return messages


class SessionMemoryCallbackHandler(MemoryCallbackHandler):
    """
    会话记忆回调处理器
    
    支持按会话（如按APP、按聊天对象）分类记录
    """
    
    def __init__(
        self,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50
    ):
        super().__init__(memory_manager, auto_save, max_history)
        
        # 会话存储：{session_id: [conversations]}
        self._sessions: Dict[str, List[Dict]] = {}
        self._current_session_id: Optional[str] = None
    
    def set_session(self, session_id: str):
        """设置当前会话 ID"""
        self._current_session_id = session_id
        
        # 初始化会话
        if session_id not in self._sessions:
            self._sessions[session_id] = []
    
    def get_current_session(self) -> Optional[str]:
        """获取当前会话 ID"""
        return self._current_session_id
    
    def _save_to_memory(self):
        """保存对话到当前会话"""
        if not self._current_user_input or not self._current_ai_response:
            return
        
        conversation = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": self._current_user_input,
            "assistant": self._current_ai_response
        }
        
        # 保存到当前会话
        if self._current_session_id:
            if self._current_session_id not in self._sessions:
                self._sessions[self._current_session_id] = []
            
            self._sessions[self._current_session_id].append(conversation)
            
            # 限制会话历史长度
            if len(self._sessions[self._current_session_id]) > self.max_history:
                self._sessions[self._current_session_id] = \
                    self._sessions[self._current_session_id][-self.max_history:]
        
        # 同时保存到全局历史
        super()._save_to_memory()
    
    def get_session_history(
        self, 
        session_id: Optional[str] = None, 
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        获取指定会话的历史记录
        
        Args:
            session_id: 会话 ID，如果为 None 则使用当前会话
            limit: 返回的记录数量限制
        
        Returns:
            会话历史记录列表
        """
        sid = session_id or self._current_session_id
        if not sid or sid not in self._sessions:
            return []
        
        return self._sessions[sid][-limit:]
    
    def get_all_sessions(self) -> Dict[str, List[Dict]]:
        """获取所有会话"""
        return self._sessions
    
    def clear_session(self, session_id: Optional[str] = None):
        """清空指定会话"""
        sid = session_id or self._current_session_id
        if sid and sid in self._sessions:
            self._sessions[sid] = []
    
    def clear_all_sessions(self):
        """清空所有会话"""
        self._sessions = {}


class FileBasedMemoryCallbackHandler(MemoryCallbackHandler):
    """
    基于文件的记忆回调处理器
    
    自动将对话历史保存到文件
    """
    
    def __init__(
        self,
        file_manager=None,
        memory_manager=None,
        auto_save: bool = True,
        max_history: int = 50
    ):
        super().__init__(memory_manager, auto_save, max_history)
        self.file_manager = file_manager
    
    def _save_to_memory(self):
        """保存对话到文件"""
        if not self._current_user_input or not self._current_ai_response:
            return
        
        # 先调用父类方法保存到内存
        super()._save_to_memory()
        
        # 保存到文件
        if self.file_manager:
            try:
                session_data = {
                    "type": "free_chat",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_input": self._current_user_input,
                    "assistant_reply": self._current_ai_response,
                }
                
                if hasattr(self.file_manager, 'save_conversation_history'):
                    self.file_manager.save_conversation_history(session_data)
                    
            except Exception as e:
                print(f"⚠️ 保存到文件失败: {e}")

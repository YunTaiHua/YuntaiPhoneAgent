"""
聊天 Agent
使用 ZHIPU_CHAT_MODEL 进行自由聊天
"""
from typing import Dict, Any, Optional, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from yuntai.models import get_chat_model, get_zhipu_client
from yuntai.prompts import CHAT_SYSTEM_PROMPT, CHAT_WITH_CONTEXT_PROMPT
from yuntai.tools import get_current_time_info


class ChatAgent:
    """聊天 Agent"""
    
    def __init__(
        self, 
        model: Optional[BaseChatModel] = None,
        file_manager=None,
        tts_manager=None
    ):
        self.model = model or get_chat_model()
        self.zhipu_client = get_zhipu_client()
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        self.system_prompt = CHAT_SYSTEM_PROMPT
    
    def chat(self, user_input: str, include_memory: bool = True) -> str:
        """
        进行自由聊天
        
        Args:
            user_input: 用户输入
            include_memory: 是否包含记忆
        
        Returns:
            回复内容
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
            response = self.model.invoke(messages)
            reply = response.content.strip()
            
            if self.file_manager:
                import datetime
                session_data = {
                    "type": "free_chat",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_input": user_input,
                    "assistant_reply": reply,
                }
                self.file_manager.save_conversation_history(session_data)
            
            if self.tts_manager and self.tts_manager.tts_enabled and len(reply) > 5:
                import threading
                threading.Timer(0.5, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
            
            return reply
            
        except Exception as e:
            return f"聊天失败: {str(e)}"
    
    def chat_with_history(
        self, 
        user_input: str, 
        history: List[Dict[str, str]]
    ) -> str:
        """
        带历史记录的聊天
        
        Args:
            user_input: 用户输入
            history: 历史记录列表
        
        Returns:
            回复内容
        """
        messages = [SystemMessage(content=self.system_prompt)]
        
        for msg in history[-10:]:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg.get("content", "")))
        
        messages.append(HumanMessage(content=user_input))
        
        try:
            response = self.model.invoke(messages)
            return response.content.strip()
        except Exception as e:
            return f"聊天失败: {str(e)}"

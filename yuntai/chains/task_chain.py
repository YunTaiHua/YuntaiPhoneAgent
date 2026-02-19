"""
任务处理链
整合判断 → 分发 → 执行流程
"""
import threading
from typing import Dict, Any, Optional, Tuple

from yuntai.agents import JudgementAgent, ChatAgent, PhoneAgent, ReplyAgent
from yuntai.prompts import (
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)
from yuntai.config import SHORTCUTS


class TaskChain:
    """任务处理链"""
    
    def __init__(
        self,
        device_id: str = "",
        file_manager=None,
        tts_manager=None
    ):
        self.device_id = device_id
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        
        self.judgement_agent = JudgementAgent()
        self.chat_agent = ChatAgent(file_manager=file_manager, tts_manager=tts_manager)
        self.phone_agent = PhoneAgent(device_id=device_id)
        self.reply_agent = ReplyAgent(
            device_id=device_id,
            file_manager=file_manager,
            tts_manager=tts_manager
        )
        
        self._continuous_reply_thread: Optional[threading.Thread] = None
    
    def set_device_id(self, device_id: str):
        """设置设备 ID"""
        self.device_id = device_id
        self.phone_agent.set_device_id(device_id)
        self.reply_agent.set_device_id(device_id)
    
    def set_tts_manager(self, tts_manager):
        """设置 TTS 管理器"""
        self.tts_manager = tts_manager
        self.chat_agent.tts_manager = tts_manager
        self.reply_agent.tts_manager = tts_manager
    
    def process(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """
        处理用户输入
        
        流程：
        1. JudgementAgent 判断任务类型
        2. 根据任务类型分发到对应的处理逻辑
        
        Args:
            user_input: 用户输入
        
        Returns:
            (处理结果, 任务信息)
        """
        if not user_input or not user_input.strip():
            return "输入为空", {}
        
        if len(user_input.strip()) == 1:
            letter = user_input.strip().lower()
            if letter in SHORTCUTS:
                task = SHORTCUTS[letter]
                return self._handle_basic_operation(task)
        
        judgement_result = self.judgement_agent.judge(user_input)
        task_info = judgement_result.to_dict()
        
        print(f"📋 任务类型: {judgement_result.task_type}")
        #print(f"\n📋 目标 APP: {judgement_result.target_app}")
        #print(f"\n📋 目标对象: {judgement_result.target_object}")
        
        if judgement_result.task_type == TASK_TYPE_FREE_CHAT:
            result = self._handle_free_chat(user_input)
        
        elif judgement_result.task_type == TASK_TYPE_BASIC_OPERATION:
            result = self._handle_basic_operation(
                f"打开{judgement_result.target_app}"
            )
        
        elif judgement_result.task_type == TASK_TYPE_SINGLE_REPLY:
            if not judgement_result.target_app or not judgement_result.target_object:
                result = "无法识别 APP 或聊天对象"
            else:
                result = self._handle_single_reply(
                    judgement_result.target_app,
                    judgement_result.target_object
                )
        
        elif judgement_result.task_type == TASK_TYPE_CONTINUOUS_REPLY:
            if not judgement_result.target_app or not judgement_result.target_object:
                result = "无法识别 APP 或聊天对象"
            else:
                result = self._handle_continuous_reply(
                    judgement_result.target_app,
                    judgement_result.target_object
                )
        
        elif judgement_result.task_type == TASK_TYPE_COMPLEX_OPERATION:
            result = self._handle_complex_operation(user_input)
        
        else:
            result = self._handle_free_chat(user_input)
        
        return result, task_info
    
    def _handle_free_chat(self, user_input: str) -> str:
        """处理自由聊天"""
        return self.chat_agent.chat(user_input)
    
    def _handle_basic_operation(self, task: str) -> str:
        """处理基础操作"""
        print(f"\n📱 执行：{task}")
        success, result = self.phone_agent.execute_operation(task)
        
        if success:
            if self.tts_manager and self.tts_manager.tts_enabled and result:
                threading.Timer(0.3, lambda: self.tts_manager.speak_text_intelligently(result)).start()
            return f"✅ 操作完成"
        else:
            return f"❌ 操作失败: {result}"
    
    def _handle_single_reply(self, app_name: str, chat_object: str) -> str:
        """处理单次回复"""
        success, result = self.reply_agent.single_reply(app_name, chat_object)
        return result
    
    def _handle_continuous_reply(self, app_name: str, chat_object: str) -> str:
        """处理持续回复 - 只返回标记，由 gui_controller 统一启动线程"""
        if not self.device_id:
            return "❌ 设备未连接"
        return f"🔄CONTINUOUS_REPLY:{app_name}:{chat_object}"
    
    def _handle_complex_operation(self, task: str) -> str:
        """处理复杂操作"""
        print(f"\n⚙️ 执行复杂操作：{task}")
        success, result = self.phone_agent.execute_operation(task)
        
        if success:
            if self.tts_manager and self.tts_manager.tts_enabled and result:
                threading.Timer(0.3, lambda: self.tts_manager.speak_text_intelligently(result)).start()
            return f"✅ 操作完成"
        else:
            return f"❌ 操作失败: {result}"
    
    def stop_continuous_reply(self):
        """停止持续回复"""
        if self.reply_agent:
            self.reply_agent.set_terminate_flag()

"""
任务判断 Agent
使用 ZHIPU_JUDGEMENT_MODEL 判断任务类型
"""
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from yuntai.models import get_judgement_model
from yuntai.prompts import (
    TASK_JUDGEMENT_PROMPT,
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)


@dataclass
class TaskJudgementResult:
    """任务判断结果"""
    task_type: str
    target_app: str
    target_object: str
    is_auto: bool
    specific_content: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "target_app": self.target_app,
            "target_object": self.target_object,
            "is_auto": self.is_auto,
            "specific_content": self.specific_content,
        }


class JudgementAgent:
    """任务判断 Agent"""
    
    def __init__(self, model: Optional[BaseChatModel] = None):
        self.model = model or get_judgement_model()
        self.system_prompt = TASK_JUDGEMENT_PROMPT
    
    def judge(self, user_input: str) -> TaskJudgementResult:
        """
        判断任务类型
        
        Args:
            user_input: 用户输入
        
        Returns:
            TaskJudgementResult: 任务判断结果
        """
        if not user_input or not user_input.strip():
            return TaskJudgementResult(
                task_type=TASK_TYPE_FREE_CHAT,
                target_app="",
                target_object="",
                is_auto=False,
                specific_content=""
            )
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"请分析以下用户指令并返回JSON格式的任务识别结果：\n\n用户指令：{user_input}")
        ]
        
        try:
            response = self.model.invoke(messages)
            result_text = response.content.strip()
            
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                task_info = json.loads(json_str)
                
                return TaskJudgementResult(
                    task_type=task_info.get("task_type", TASK_TYPE_FREE_CHAT),
                    target_app=task_info.get("target_app", ""),
                    target_object=task_info.get("target_object", ""),
                    is_auto=task_info.get("is_auto", False),
                    specific_content=task_info.get("specific_content", "")
                )
        except Exception as e:
            print(f"任务判断失败: {e}")
        
        return self._fallback_judge(user_input)
    
    def _fallback_judge(self, user_input: str) -> TaskJudgementResult:
        """后备判断逻辑"""
        user_input_lower = user_input.lower()
        
        if "auto" in user_input_lower or "持续" in user_input_lower:
            if "打开" in user_input and "发消息" in user_input:
                target_app = self._extract_app(user_input)
                target_object = self._extract_object(user_input)
                return TaskJudgementResult(
                    task_type=TASK_TYPE_CONTINUOUS_REPLY,
                    target_app=target_app,
                    target_object=target_object,
                    is_auto=True,
                    specific_content=""
                )
        
        if "打开" in user_input and "发消息" in user_input:
            target_app = self._extract_app(user_input)
            target_object = self._extract_object(user_input)
            specific_content = self._extract_content(user_input)
            
            if specific_content:
                return TaskJudgementResult(
                    task_type=TASK_TYPE_COMPLEX_OPERATION,
                    target_app=target_app,
                    target_object=target_object,
                    is_auto=False,
                    specific_content=specific_content
                )
            else:
                return TaskJudgementResult(
                    task_type=TASK_TYPE_SINGLE_REPLY,
                    target_app=target_app,
                    target_object=target_object,
                    is_auto=False,
                    specific_content=""
                )
        
        if "打开" in user_input:
            target_app = self._extract_app(user_input)
            return TaskJudgementResult(
                task_type=TASK_TYPE_BASIC_OPERATION,
                target_app=target_app,
                target_object="",
                is_auto=False,
                specific_content=""
            )
        
        return TaskJudgementResult(
            task_type=TASK_TYPE_FREE_CHAT,
            target_app="",
            target_object="",
            is_auto=False,
            specific_content=""
        )
    
    def _extract_app(self, user_input: str) -> str:
        """提取目标 APP"""
        supported_apps = ["qq", "微信", "抖音", "淘宝", "快手", "qq音乐", "支付宝", "微博", "小红书", "bilibili"]
        user_input_lower = user_input.lower()
        for app in supported_apps:
            if app in user_input_lower:
                return app
        return ""
    
    def _extract_object(self, user_input: str) -> str:
        """提取聊天对象"""
        import re
        patterns = [
            r"给([^\s]+?)发消息",
            r"和([^\s]+?)聊天",
            r"向([^\s]+?)发送",
        ]
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match and match.group(1):
                return match.group(1).strip()
        return ""
    
    def _extract_content(self, user_input: str) -> str:
        """提取具体消息内容"""
        import re
        quote_patterns = [r'["\']([^"\']+)["\']']
        for pattern in quote_patterns:
            match = re.search(pattern, user_input)
            if match:
                return match.group(1).strip()
        
        if "：" in user_input:
            parts = user_input.split("：")
            if len(parts) > 1:
                last_part = parts[-1].strip()
                if not re.match(r'\d{1,2}:\d{2}', last_part) and len(last_part) > 0:
                    return last_part
        
        return ""

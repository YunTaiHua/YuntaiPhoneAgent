"""
手机操作工具模块
封装 PhoneAgent 的核心功能
"""
import json
from typing import Optional, Tuple, List, Dict, Any, Callable
from langchain.tools import tool

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

from yuntai.config import (
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_MODEL,
)


def _create_phone_agent(device_id: str, max_steps: int = 100, lang: str = "cn") -> PhoneAgent:
    """创建 PhoneAgent 实例"""
    model_config = ModelConfig(
        base_url=ZHIPU_API_BASE_URL,
        model_name=ZHIPU_MODEL,
        api_key=ZHIPU_API_KEY,
        lang=lang,
    )
    agent_config = AgentConfig(
        max_steps=max_steps,
        device_id=device_id,
        verbose=False,
        lang=lang,
    )
    return PhoneAgent(model_config=model_config, agent_config=agent_config)


class PhoneToolManager:
    """手机操作工具管理器"""
    
    def __init__(self, device_id: str, max_steps: int = 100):
        self.device_id = device_id
        self.max_steps = max_steps
        self._agent: Optional[PhoneAgent] = None
    
    def _get_agent(self) -> PhoneAgent:
        if self._agent is None:
            self._agent = _create_phone_agent(self.device_id, self.max_steps)
        return self._agent
    
    def _reset_agent(self):
        if self._agent:
            self._agent.reset()
            self._agent = None
    
    def open_app(self, app_name: str) -> Tuple[bool, str]:
        """打开指定APP"""
        try:
            agent = self._get_agent()
            task = f"打开{app_name}"
            result = agent.run(task)
            self._reset_agent()
            
            success = "失败" not in result and "错误" not in result
            return success, result
        except Exception as e:
            return False, f"打开APP失败: {str(e)}"
    
    def execute_operation(self, task: str) -> Tuple[bool, str]:
        """执行复杂手机操作"""
        try:
            agent = self._get_agent()
            result = agent.run(task)
            self._reset_agent()
            
            success = "失败" not in result and "错误" not in result
            return success, result
        except Exception as e:
            return False, f"操作执行失败: {str(e)}"
    
    def extract_chat_records(
        self, 
        app_name: str, 
        chat_object: str,
        extra_prompt: str = ""
    ) -> Tuple[bool, str]:
        """提取聊天记录"""
        try:
            agent = self._get_agent()
            task = f"""在{app_name}中进入{chat_object}的聊天窗口，向下滑动1次，提取当前屏幕可见的聊天记录

重要说明：
1. 键盘已经关闭，不需要点击聊天区空白处关闭键盘
2. 直接向下滑动1次即可
3. 准确描述每条消息的气泡颜色（如白色、红色、蓝色、绿色等）
4. 准确描述每条消息的头像位置（左侧有头像/右侧有头像）
5. 不要判断发送方，只需描述客观信息
6. 不要简化描述，必须明确说明头像位置
7. 不要向上滑动
{extra_prompt}
"""
            result = agent.run(task)
            self._reset_agent()
            return True, result
        except Exception as e:
            return False, f"提取聊天记录失败: {str(e)}"
    
    def send_message(
        self, 
        app_name: str, 
        chat_object: str, 
        message: str
    ) -> Tuple[bool, str]:
        """发送消息"""
        try:
            agent = self._get_agent()
            
            if app_name == "QQ":
                task = f"在{app_name}中给{chat_object}发送消息：{message}，点击右下角的发送按钮，然后使用Back按钮关闭键盘"
            elif app_name == "微信":
                task = f"在{app_name}中给{chat_object}发送消息：{message}，点击右侧的发送按钮，然后使用Back按钮关闭键盘"
            else:
                task = f"在{app_name}中给{chat_object}发送消息：{message}，然后点击发送按钮，然后使用Back按钮关闭键盘"
            
            result = agent.run(task)
            self._reset_agent()
            
            success_keywords = ["已成功发送消息", "消息已成功发送", "发送了消息", "发送成功", "发送了", "已发送", "点击了发送", "发送按钮", "点击发送按钮"]
            success = any(keyword in result for keyword in success_keywords)
            return success, result
        except Exception as e:
            return False, f"发送消息失败: {str(e)}"


def open_app_tool(device_id: str, app_name: str) -> Tuple[bool, str]:
    """打开APP工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.open_app(app_name)


def execute_phone_operation(device_id: str, task: str) -> Tuple[bool, str]:
    """执行手机操作工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.execute_operation(task)


def extract_chat_records_tool(
    device_id: str, 
    app_name: str, 
    chat_object: str,
    extra_prompt: str = ""
) -> Tuple[bool, str]:
    """提取聊天记录工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.extract_chat_records(app_name, chat_object, extra_prompt)


def send_message_tool(
    device_id: str, 
    app_name: str, 
    chat_object: str, 
    message: str
) -> Tuple[bool, str]:
    """发送消息工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.send_message(app_name, chat_object, message)

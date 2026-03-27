"""
手机操作工具模块
封装 PhoneAgent 的核心功能
"""
from __future__ import annotations

import json
from collections.abc import Callable
from langchain.tools import tool

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

from yuntai.core.config import (
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_MODEL,
    PHONE_AGENT_MAX_STEPS,
    PHONE_AGENT_LANG,
    PHONE_SUCCESS_KEYWORDS,
)
from yuntai.prompts import (
    PHONE_EXTRACT_TASK_PROMPT,
    PHONE_SEND_TASK_QQ,
    PHONE_SEND_TASK_WECHAT,
    PHONE_SEND_TASK_DEFAULT,
)


def _create_phone_agent(device_id: str, max_steps: int = PHONE_AGENT_MAX_STEPS, lang: str = PHONE_AGENT_LANG) -> PhoneAgent:
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
    
    def __init__(self, device_id: str, max_steps: int = PHONE_AGENT_MAX_STEPS) -> None:
        self.device_id = device_id
        self.max_steps = max_steps
        self._agent: PhoneAgent | None = None
    
    def _get_agent(self) -> PhoneAgent:
        if self._agent is None:
            self._agent = _create_phone_agent(self.device_id, self.max_steps)
        return self._agent
    
    def _reset_agent(self) -> None:
        if self._agent:
            self._agent.reset()
            self._agent = None
    
    def open_app(self, app_name: str) -> tuple[bool, str]:
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
    
    def execute_operation(self, task: str) -> tuple[bool, str]:
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
    ) -> tuple[bool, str]:
        """
        提取聊天记录
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            extra_prompt: 额外提示词
        
        Returns:
            (是否成功, 聊天记录)
        """
        try:
            agent = self._get_agent()
            task = PHONE_EXTRACT_TASK_PROMPT.format(
                app_name=app_name,
                chat_object=chat_object,
                extra_prompt=extra_prompt
            )
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
    ) -> tuple[bool, str]:
        """
        发送消息
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            message: 消息内容
        
        Returns:
            (是否成功, 执行结果)
        """
        try:
            agent = self._get_agent()
            
            if app_name == "QQ":
                task = PHONE_SEND_TASK_QQ.format(
                    app_name=app_name,
                    chat_object=chat_object,
                    message=message
                )
            elif app_name == "微信":
                task = PHONE_SEND_TASK_WECHAT.format(
                    app_name=app_name,
                    chat_object=chat_object,
                    message=message
                )
            else:
                task = PHONE_SEND_TASK_DEFAULT.format(
                    app_name=app_name,
                    chat_object=chat_object,
                    message=message
                )
            
            result = agent.run(task)
            self._reset_agent()
            
            success_keywords = PHONE_SUCCESS_KEYWORDS
            success = any(keyword in result for keyword in success_keywords)
            return success, result
        except Exception as e:
            return False, f"发送消息失败: {str(e)}"


def open_app_tool(device_id: str, app_name: str) -> tuple[bool, str]:
    """打开APP工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.open_app(app_name)


def execute_phone_operation(device_id: str, task: str) -> tuple[bool, str]:
    """执行手机操作工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.execute_operation(task)


def extract_chat_records_tool(
    device_id: str,
    app_name: str,
    chat_object: str,
    extra_prompt: str = ""
) -> tuple[bool, str]:
    """提取聊天记录工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.extract_chat_records(app_name, chat_object, extra_prompt)


def send_message_tool(
    device_id: str,
    app_name: str,
    chat_object: str,
    message: str
) -> tuple[bool, str]:
    """发送消息工具函数"""
    manager = PhoneToolManager(device_id)
    return manager.send_message(app_name, chat_object, message)

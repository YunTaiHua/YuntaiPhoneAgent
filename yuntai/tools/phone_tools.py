"""
手机操作工具模块
封装 PhoneAgent 的核心功能
"""
from __future__ import annotations

from yuntai.agents.phone_agent import PhoneAgent


def open_app_tool(device_id: str, app_name: str) -> tuple[bool, str]:
    """打开APP工具函数"""
    agent = PhoneAgent(device_id)
    return agent.open_app(app_name)


def execute_phone_operation(device_id: str, task: str) -> tuple[bool, str]:
    """执行手机操作工具函数"""
    agent = PhoneAgent(device_id)
    return agent.execute_operation(task)


def extract_chat_records_tool(
    device_id: str,
    app_name: str,
    chat_object: str,
    extra_prompt: str = ""
) -> tuple[bool, str]:
    """提取聊天记录工具函数"""
    agent = PhoneAgent(device_id)
    return agent.extract_chat_records(app_name, chat_object)


def send_message_tool(
    device_id: str,
    app_name: str,
    chat_object: str,
    message: str
) -> tuple[bool, str]:
    """发送消息工具函数"""
    agent = PhoneAgent(device_id)
    return agent.send_message(app_name, chat_object, message)

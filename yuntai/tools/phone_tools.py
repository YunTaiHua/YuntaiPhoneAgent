"""
手机操作工具模块
================

封装 PhoneAgent 的核心功能，提供简洁的工具函数接口。

主要功能:
    - open_app_tool: 打开 APP 工具函数
    - execute_phone_operation: 执行手机操作工具函数
    - extract_chat_records_tool: 提取聊天记录工具函数
    - send_message_tool: 发送消息工具函数

使用示例:
    >>> from yuntai.tools import open_app_tool, send_message_tool
    >>> success, msg = open_app_tool(device_id, "微信")
    >>> success, msg = send_message_tool(device_id, "微信", "张三", "你好")
"""
from __future__ import annotations

import logging

from yuntai.agents.phone_agent import PhoneAgent

logger = logging.getLogger(__name__)


def open_app_tool(device_id: str, app_name: str) -> tuple[bool, str]:
    """
    打开 APP 工具函数
    
    在指定设备上打开指定的应用程序。
    
    Args:
        device_id: 设备 ID
        app_name: 应用程序名称
        
    Returns:
        元组 (是否成功, 消息)
    """
    logger.debug(f"打开 APP: {app_name}, device_id={device_id}")
    agent = PhoneAgent(device_id)
    return agent.open_app(app_name)


def execute_phone_operation(device_id: str, task: str) -> tuple[bool, str]:
    """
    执行手机操作工具函数
    
    在指定设备上执行指定的操作任务。
    
    Args:
        device_id: 设备 ID
        task: 操作任务描述
        
    Returns:
        元组 (是否成功, 消息)
    """
    logger.debug(f"执行手机操作: {task}, device_id={device_id}")
    agent = PhoneAgent(device_id)
    return agent.execute_operation(task)


def extract_chat_records_tool(
    device_id: str,
    app_name: str,
    chat_object: str,
    extra_prompt: str = ""
) -> tuple[bool, str]:
    """
    提取聊天记录工具函数
    
    在指定设备上从指定 APP 提取与指定对象的聊天记录。
    
    Args:
        device_id: 设备 ID
        app_name: 应用程序名称
        chat_object: 聊天对象名称
        extra_prompt: 额外的提示词，可选
        
    Returns:
        元组 (是否成功, 聊天记录或错误消息)
    """
    logger.debug(f"提取聊天记录: app={app_name}, object={chat_object}")
    agent = PhoneAgent(device_id)
    return agent.extract_chat_records(app_name, chat_object)


def send_message_tool(
    device_id: str,
    app_name: str,
    chat_object: str,
    message: str
) -> tuple[bool, str]:
    """
    发送消息工具函数
    
    在指定设备上通过指定 APP 向指定对象发送消息。
    
    Args:
        device_id: 设备 ID
        app_name: 应用程序名称
        chat_object: 聊天对象名称
        message: 要发送的消息内容
        
    Returns:
        元组 (是否成功, 消息)
    """
    logger.debug(f"发送消息: app={app_name}, object={chat_object}, message={message[:20]}...")
    agent = PhoneAgent(device_id)
    return agent.send_message(app_name, chat_object, message)

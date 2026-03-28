"""
Chain 模块
==========

本模块提供任务链和回复链的实现，用于编排复杂的工作流。

模块包含以下链类：
    - TaskChain: 任务处理链，整合判断、分发、执行流程
    - ReplyChain: 回复处理链，使用 LangGraph 工作流处理回复

使用示例：
    >>> from yuntai.chains import TaskChain, ReplyChain
    >>> 
    >>> # 创建任务链
    >>> task_chain = TaskChain(device_id="your_device")
    >>> result, info = task_chain.process("打开微信")
    >>> 
    >>> # 创建回复链
    >>> reply_chain = ReplyChain(device_id="your_device")
    >>> success, result = reply_chain.single_reply("微信", "张三")
"""

from .task_chain import TaskChain
from .reply_chain import ReplyChain

# 模块公开接口
__all__ = [
    "TaskChain",
    "ReplyChain",
]

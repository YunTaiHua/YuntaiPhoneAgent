"""
LangGraph 工作流模块
====================

本模块提供基于 LangGraph 的工作流实现，用于处理持续回复等复杂任务。

模块包含以下组件：
    - ReplyState: 回复工作流状态定义
    - ReplyStateBuilder: 状态构建器
    - ReplyGraph: 持续回复工作流图

使用示例：
    >>> from yuntai.graphs import ReplyGraph, ReplyStateBuilder
    >>> 
    >>> # 创建工作流
    >>> graph = ReplyGraph(file_manager=file_manager)
    >>> 
    >>> # 运行工作流
    >>> success, result = graph.run("微信", "张三", device_id="device_123")
"""
from .state import ReplyState, ReplyStateBuilder
from .reply_graph import ReplyGraph

# 模块公开接口
__all__ = [
    "ReplyState",
    "ReplyStateBuilder", 
    "ReplyGraph",
]

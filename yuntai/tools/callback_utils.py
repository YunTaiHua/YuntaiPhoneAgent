"""
回调处理器工具模块
==================

提供 LangChain Callbacks 的统一准备和管理功能，用于简化回调处理器的配置和合并操作。

主要功能:
    - prepare_callbacks: 准备回调处理器列表
    - prepare_callbacks_with_manager: 使用指定回调管理器准备回调
    - get_global_callbacks: 获取全局回调处理器列表

使用示例:
    >>> from yuntai.tools import prepare_callbacks
    >>> def on_token(text: str): print(text, end='')
    >>> callbacks = prepare_callbacks(streaming_callback=on_token)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain_core.callbacks import BaseCallbackHandler

from yuntai.callbacks import get_callback_manager, StreamingCallbackHandler

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def prepare_callbacks(
    callbacks: list[BaseCallbackHandler] | None = None,
    streaming_callback: Callable[[str], None] | None = None,
    complete_callback: Callable[[str], None] | None = None,
    enable_streaming: bool = True
) -> list[BaseCallbackHandler]:
    """
    准备回调处理器列表
    
    合并全局回调、流式输出回调和用户自定义回调，
    返回统一的回调处理器列表供 LangChain 调用使用。
    
    Args:
        callbacks: 用户提供的自定义回调处理器列表
        streaming_callback: 流式输出回调函数，每个 token 调用一次
        complete_callback: 完成回调函数，输出完成时调用
        enable_streaming: 是否启用流式输出回调，默认 True
    
    Returns:
        合并后的回调处理器列表
    
    Example:
        >>> def on_token(text: str): print(text, end='')
        >>> callbacks = prepare_callbacks(
        ...     streaming_callback=on_token,
        ...     enable_streaming=True
        ... )
    """
    all_callbacks: list[BaseCallbackHandler] = []
    
    callback_manager = get_callback_manager()
    global_callbacks = callback_manager.get_callbacks(include_global=True)
    all_callbacks.extend(global_callbacks)
    
    if enable_streaming and (streaming_callback or complete_callback):
        streaming_handler = StreamingCallbackHandler(
            output_callback=streaming_callback,
            complete_callback=complete_callback
        )
        all_callbacks.append(streaming_handler)
    
    if callbacks:
        all_callbacks.extend(callbacks)
    
    logger.debug("准备回调处理器: 共 %d 个", len(all_callbacks))
    return all_callbacks


def prepare_callbacks_with_manager(
    callback_manager,
    callbacks: list[BaseCallbackHandler] | None = None,
    streaming_callback: Callable[[str], None] | None = None,
    complete_callback: Callable[[str], None] | None = None,
    enable_streaming: bool = True
) -> list[BaseCallbackHandler]:
    """
    使用指定回调管理器准备回调处理器列表
    
    与 prepare_callbacks 功能相同，但允许指定自定义的回调管理器实例。
    
    Args:
        callback_manager: 回调管理器实例
        callbacks: 用户提供的自定义回调处理器列表
        streaming_callback: 流式输出回调函数
        complete_callback: 完成回调函数
        enable_streaming: 是否启用流式输出回调
    
    Returns:
        合并后的回调处理器列表
    """
    all_callbacks: list[BaseCallbackHandler] = []
    
    global_callbacks = callback_manager.get_callbacks(include_global=True)
    all_callbacks.extend(global_callbacks)
    
    if enable_streaming and (streaming_callback or complete_callback):
        streaming_handler = StreamingCallbackHandler(
            output_callback=streaming_callback,
            complete_callback=complete_callback
        )
        all_callbacks.append(streaming_handler)
    
    if callbacks:
        all_callbacks.extend(callbacks)
    
    logger.debug("使用自定义管理器准备回调处理器: 共 %d 个", len(all_callbacks))
    return all_callbacks


def get_global_callbacks() -> list[BaseCallbackHandler]:
    """
    获取全局回调处理器列表
    
    仅返回已注册的全局回调处理器，不包含流式输出回调。
    适用于不需要流式输出的简单场景。
    
    Returns:
        全局回调处理器列表
    """
    callback_manager = get_callback_manager()
    callbacks = callback_manager.get_callbacks(include_global=True)
    logger.debug("获取全局回调处理器: 共 %d 个", len(callbacks))
    return callbacks

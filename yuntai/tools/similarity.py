"""
文本相似度工具模块

提供文本相似度比较功能，用于消息去重和相似性判断。
支持多种相似度计算策略，包括精确匹配、包含匹配和模糊匹配。
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Final


DEFAULT_SIMILARITY_THRESHOLD: Final[float] = 0.6


def clean_text(text: str) -> str:
    """
    清理文本，移除标点符号和空白字符
    
    保留中文字符、英文字母和数字，转换为小写形式。
    
    Args:
        text: 待清理的原始文本
    
    Returns:
        清理后的文本字符串
    
    Example:
        >>> clean_text("你好，世界！")
        '你好世界'
        >>> clean_text("Hello, World!")
        'helloworld'
    """
    return re.sub(r'[^\w\u4e00-\u9fff]', '', text).lower()


def is_similar(
    msg1: str, 
    msg2: str, 
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> bool:
    """
    判断两条消息是否相似
    
    使用多级匹配策略判断消息相似性：
    1. 精确匹配：清理后的文本完全相同
    2. 包含匹配：一条消息包含另一条消息
    3. 模糊匹配：使用 SequenceMatcher 计算相似度比率
    
    Args:
        msg1: 第一条消息文本
        msg2: 第二条消息文本
        threshold: 相似度阈值，范围 [0.0, 1.0]，默认 0.6
    
    Returns:
        如果消息相似返回 True，否则返回 False
    
    Example:
        >>> is_similar("你好", "你好！", 0.6)
        True
        >>> is_similar("今天天气不错", "明天天气不错", 0.7)
        False
    """
    if not msg1 or not msg2:
        return False
    
    c1, c2 = clean_text(msg1), clean_text(msg2)
    
    if not c1 or not c2:
        return msg1 == msg2
    
    if c1 == c2:
        return True
    
    if c1 in c2 or c2 in c1:
        return True
    
    return SequenceMatcher(None, c1, c2).ratio() >= threshold


def calculate_similarity(msg1: str, msg2: str) -> float:
    """
    计算两条消息的相似度比率
    
    返回 [0.0, 1.0] 范围内的相似度分数，
    可用于需要精确相似度值的场景。
    
    Args:
        msg1: 第一条消息文本
        msg2: 第二条消息文本
    
    Returns:
        相似度比率，范围 [0.0, 1.0]
    
    Example:
        >>> calculate_similarity("你好世界", "你好")
        0.666...
    """
    if not msg1 or not msg2:
        return 0.0
    
    c1, c2 = clean_text(msg1), clean_text(msg2)
    
    if not c1 or not c2:
        return 1.0 if msg1 == msg2 else 0.0
    
    if c1 == c2:
        return 1.0
    
    return SequenceMatcher(None, c1, c2).ratio()

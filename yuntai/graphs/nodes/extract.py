"""
提取聊天记录节点模块
====================

本模块负责从手机应用中提取聊天记录，使用 LRU 缓存机制优化性能。

主要功能：
    - 从手机应用提取聊天记录
    - PhoneAgent 实例 LRU 缓存管理
    - 缓存过期清理功能防止内存泄漏
    - 缓存统计和监控功能

函数说明：
    - extract_records: 提取聊天记录节点函数
    - clear_cache: 清理 PhoneAgent 缓存
    - get_cache_size: 获取当前缓存大小
    - get_cache_stats: 获取缓存统计信息

使用示例：
    >>> from yuntai.graphs.nodes import extract_records
    >>> 
    >>> # 在 LangGraph 中使用
    >>> result = extract_records(state)
"""
from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from yuntai.graphs.state import ReplyState
from yuntai.agents.phone_agent import PhoneAgent
from yuntai.core.config import PHONE_AGENT_CACHE_MAX_SIZE

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# 缓存过期时间（秒）- 默认 30 分钟
CACHE_EXPIRE_SECONDS: int = 1800


@dataclass
class CacheEntry:
    """
    缓存条目数据类
    
    存储缓存项及其元数据，包括创建时间和最后访问时间。
    
    Attributes:
        agent: PhoneAgent 实例
        created_at: 创建时间戳
        last_accessed: 最后访问时间戳
        access_count: 访问次数
    """
    agent: PhoneAgent
    created_at: float
    last_accessed: float
    access_count: int = 0


class PhoneAgentCache:
    """
    PhoneAgent LRU 缓存管理器
    
    使用 LRU（最近最少使用）策略管理 PhoneAgent 实例缓存，
    支持过期清理和容量限制。
    
    Attributes:
        max_size: 最大缓存容量
        expire_seconds: 缓存过期时间（秒）
        _cache: 有序字典，按访问顺序排列
        _lock: 线程锁，保证线程安全
        _hits: 缓存命中次数
        _misses: 缓存未命中次数
    
    使用示例：
        >>> cache = PhoneAgentCache(max_size=10, expire_seconds=1800)
        >>> agent = cache.get("device_123")
        >>> cache.put("device_123", agent)
    """
    
    def __init__(
        self, 
        max_size: int = PHONE_AGENT_CACHE_MAX_SIZE,
        expire_seconds: int = CACHE_EXPIRE_SECONDS
    ) -> None:
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存容量，默认使用配置值
            expire_seconds: 缓存过期时间（秒），默认 30 分钟
        """
        self.max_size = max_size
        self.expire_seconds = expire_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        
        logger.debug(
            "PhoneAgentCache 初始化完成, max_size=%d, expire_seconds=%d",
            max_size, expire_seconds
        )
    
    def get(self, device_id: str) -> PhoneAgent | None:
        """
        获取缓存中的 PhoneAgent 实例
        
        使用 LRU 策略，访问后更新条目位置到队列末尾。
        自动检查并清理过期条目。
        
        Args:
            device_id: 设备 ID
        
        Returns:
            PhoneAgent 实例，如果不存在或已过期则返回 None
        """
        with self._lock:
            if device_id not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[device_id]
            
            # 检查是否过期
            if time.time() - entry.last_accessed > self.expire_seconds:
                logger.info("缓存条目已过期: %s", device_id)
                del self._cache[device_id]
                self._misses += 1
                return None
            
            # LRU: 移动到队列末尾（最近使用）
            self._cache.move_to_end(device_id)
            entry.last_accessed = time.time()
            entry.access_count += 1
            self._hits += 1
            
            logger.debug("缓存命中: %s, 访问次数: %d", device_id, entry.access_count)
            return entry.agent
    
    def put(self, device_id: str, agent: PhoneAgent) -> None:
        """
        将 PhoneAgent 实例放入缓存
        
        如果缓存已满，移除最久未使用的条目（LRU 策略）。
        
        Args:
            device_id: 设备 ID
            agent: PhoneAgent 实例
        """
        with self._lock:
            current_time = time.time()
            
            # 如果已存在，更新并移动到末尾
            if device_id in self._cache:
                entry = self._cache[device_id]
                entry.agent = agent
                entry.last_accessed = current_time
                entry.access_count += 1
                self._cache.move_to_end(device_id)
                logger.debug("更新缓存条目: %s", device_id)
                return
            
            # 检查容量，移除最久未使用的条目
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.info("LRU 清理最旧缓存: %s", oldest_key)
                print(f"🧹 LRU 清理最旧缓存: {oldest_key}")
            
            # 添加新条目
            self._cache[device_id] = CacheEntry(
                agent=agent,
                created_at=current_time,
                last_accessed=current_time,
                access_count=1
            )
            logger.debug("添加缓存条目: %s", device_id)
    
    def remove(self, device_id: str) -> bool:
        """
        移除指定缓存条目
        
        Args:
            device_id: 设备 ID
        
        Returns:
            是否成功移除
        """
        with self._lock:
            if device_id in self._cache:
                del self._cache[device_id]
                logger.info("已移除缓存条目: %s", device_id)
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("已清空所有缓存，共 %d 个条目", count)
    
    def cleanup_expired(self) -> int:
        """
        清理所有过期条目
        
        Returns:
            清理的条目数量
        """
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if current_time - entry.last_accessed > self.expire_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.info("清理过期缓存: %d 个条目", len(expired_keys))
            print(f"🧹 清理过期缓存: {len(expired_keys)} 个条目")
        
        return len(expired_keys)
    
    def size(self) -> int:
        """获取当前缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计数据的字典
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2%}",
                "expire_seconds": self.expire_seconds,
            }


# 全局缓存实例
_cache: PhoneAgentCache = PhoneAgentCache()


def _get_phone_agent(device_id: str) -> PhoneAgent:
    """
    获取或创建 PhoneAgent 实例
    
    使用 LRU 缓存机制避免重复创建实例，提高性能。
    当缓存超过最大限制时，自动清理最久未使用的条目。
    
    Args:
        device_id: 设备 ID
    
    Returns:
        PhoneAgent: PhoneAgent 实例
    
    使用示例：
        >>> agent = _get_phone_agent("device_123")
    """
    # 尝试从缓存获取
    agent = _cache.get(device_id)
    if agent is not None:
        logger.debug("从缓存获取 PhoneAgent: %s", device_id)
        return agent
    
    # 创建新的 PhoneAgent 实例
    agent = PhoneAgent(device_id)
    _cache.put(device_id, agent)
    logger.debug("创建并缓存 PhoneAgent: %s", device_id)
    return agent


def clear_cache(device_id: str | None = None) -> None:
    """
    清理 PhoneAgent 缓存
    
    清理指定设备的缓存，如果未指定则清理全部缓存。
    建议在设备断开连接或应用退出时调用。
    
    Args:
        device_id: 设备 ID，为 None 时清理全部缓存
    
    使用示例：
        >>> clear_cache("device_123")  # 清理指定设备缓存
        >>> clear_cache()  # 清理全部缓存
    """
    if device_id is not None:
        if _cache.remove(device_id):
            print(f"🧹 已清理设备缓存: {device_id}")
    else:
        _cache.clear()
        print("🧹 已清理全部 PhoneAgent 缓存")


def get_cache_size() -> int:
    """
    获取当前缓存大小
    
    Returns:
        int: 缓存中的 PhoneAgent 实例数量
    """
    return _cache.size()


def get_cache_stats() -> dict[str, Any]:
    """
    获取缓存统计信息
    
    Returns:
        dict[str, Any]: 包含缓存统计数据的字典
    """
    return _cache.get_stats()


def cleanup_expired_cache() -> int:
    """
    清理过期缓存
    
    Returns:
        int: 清理的条目数量
    """
    return _cache.cleanup_expired()


def extract_records(state: ReplyState) -> dict[str, Any]:
    """
    提取聊天记录节点
    
    从指定应用的聊天界面提取聊天记录。
    
    输入状态字段:
        - app_name: 应用名称
        - chat_object: 聊天对象
        - device_id: 设备 ID
        - cycle_count: 当前循环次数
        - max_cycles: 最大循环次数
        - terminate_flag: 终止标志
    
    输出状态字段:
        - cycle_count: 更新后的循环次数
        - extracted_records: 提取的聊天记录
        - error: 错误信息（如有）
        - should_continue: 是否继续（如有终止信号）
        - terminate_flag: 终止标志
    
    Args:
        state: 回复状态字典
    
    Returns:
        dict[str, Any]: 包含提取结果的字典
    
    使用示例：
        >>> result = extract_records(state)
        >>> records = result.get("extracted_records", "")
    """
    # 导入终止检查函数
    from yuntai.graphs.nodes.control import check_terminate
    
    # 获取状态参数
    app_name = state["app_name"]
    chat_object = state["chat_object"]
    device_id = state["device_id"]
    cycle_count = state["cycle_count"] + 1
    
    # 打印循环信息
    print(f"\n{'='*60}")
    print(f"📊 循环轮次 {cycle_count}/{state['max_cycles']}")
    print(f"{'='*60}")
    
    logger.debug("提取聊天记录: APP=%s, 对象=%s, 循环=%d", app_name, chat_object, cycle_count)
    
    # 检查终止信号
    if check_terminate() or state.get("terminate_flag"):
        logger.info("检测到终止信号，停止提取")
        print("🛑 检测到终止信号")
        return {
            "cycle_count": cycle_count,
            "should_continue": False,
            "terminate_flag": True,
            "extracted_records": "",
        }
    
    # 获取 PhoneAgent 实例
    agent = _get_phone_agent(device_id)
    
    # 提取聊天记录
    success, records = agent.extract_chat_records(app_name, chat_object)
    
    if not success:
        # 提取失败
        logger.error("提取聊天记录失败: %s", records)
        print(f"❌ 提取聊天记录失败: {records}")
        return {
            "cycle_count": cycle_count,
            "extracted_records": "",
            "error": records,
        }
    
    # 提取成功
    logger.debug("提取聊天记录成功，长度: %d", len(records))
    return {
        "cycle_count": cycle_count,
        "extracted_records": records,
        "error": None,
    }

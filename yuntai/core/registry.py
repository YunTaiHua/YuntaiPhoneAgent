# yuntai/core/registry.py
"""
服务注册表模块
==============

提供轻量级依赖注入容器，管理应用级单例和工厂函数。
仅在应用启动时用于组装依赖，不用于业务逻辑中。

使用示例:
    >>> from yuntai.core.registry import get_registry
    >>> registry = get_registry()
    >>> registry.register("config", my_config)
    >>> config = registry.get("config")
"""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """轻量级服务定位器，管理应用级单例和工厂函数"""

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, instance: Any) -> None:
        """注册单例服务"""
        self._services[name] = instance
        logger.debug("注册服务: %s", name)

    def register_factory(self, name: str, factory: Callable[..., Any]) -> None:
        """注册工厂函数（按需创建）"""
        self._factories[name] = factory
        logger.debug("注册工厂: %s", name)

    def get(self, name: str) -> Any:
        """获取服务实例，未注册抛出 KeyError"""
        if name not in self._services:
            raise KeyError(f"服务 '{name}' 未注册")
        return self._services[name]

    def create(self, name: str, **kwargs: Any) -> Any:
        """通过工厂创建新实例"""
        if name not in self._factories:
            raise KeyError(f"工厂 '{name}' 未注册")
        instance = self._factories[name](**kwargs)
        logger.debug("通过工厂创建: %s", name)
        return instance

    def has(self, name: str) -> bool:
        """检查服务是否已注册（包括单例和工厂）"""
        return name in self._services or name in self._factories


# 全局注册表单例
_registry: ServiceRegistry | None = None


def get_registry() -> ServiceRegistry:
    """获取全局注册表单例"""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
        logger.debug("创建全局注册表")
    return _registry

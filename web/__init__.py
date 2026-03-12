"""
Web模块初始化
提供Web界面功能
"""

from .core import WebController, setup_routes, ConnectionManager

__all__ = [
    'WebController',
    'setup_routes',
    'ConnectionManager',
]

"""
core - Web核心模块
包含控制器、路由、WebSocket管理器等核心组件
"""

from .controller import WebController
from .routes import setup_routes
from .ws_manager import ConnectionManager
from .output_capture import WebOutputCapture

__all__ = [
    'WebController',
    'setup_routes',
    'ConnectionManager',
    'WebOutputCapture',
]

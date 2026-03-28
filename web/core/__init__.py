"""
Web 核心模块
============

提供 Web 界面的核心功能，包括控制器、路由、WebSocket 管理器等。

主要组件:
    - WebController: Web 控制器，处理所有 Web 请求和业务逻辑
    - setup_routes: FastAPI 路由设置函数
    - ConnectionManager: WebSocket 连接管理器
    - WebOutputCapture: Web 端输出捕获类

功能特点:
    - FastAPI 异步路由
    - WebSocket 实时通信
    - 终端输出同步到前端
    - TTS 语音合成集成
"""
import logging

logger = logging.getLogger(__name__)

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

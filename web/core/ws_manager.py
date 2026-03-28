"""
WebSocket 连接管理器模块
========================

管理 WebSocket 连接的建立、断开和消息广播。

主要组件:
    - ConnectionManager: WebSocket 连接管理器

功能特点:
    - 支持多客户端同时连接
    - 线程安全的连接管理
    - 支持个人消息和广播消息
    - 首次连接状态跟踪
"""
import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket 连接管理器
    
    管理所有 WebSocket 连接，支持消息广播和个人消息发送。
    
    Attributes:
        active_connections: 当前活跃的 WebSocket 连接列表
        _lock: 异步锁，保证线程安全
        _first_connection_occurred: 是否已有首次连接
    
    使用示例:
        >>> manager = ConnectionManager()
        >>> await manager.connect(websocket)
        >>> await manager.broadcast({"type": "message", "data": "hello"})
    """
    
    def __init__(self) -> None:
        """初始化连接管理器"""
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
        self._first_connection_occurred = False
        logger.debug("ConnectionManager 初始化完成")
    
    async def connect(self, websocket: WebSocket) -> None:
        """
        接受新的 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接实例
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        print(f"✅ WebSocket连接建立，当前连接数: {len(self.active_connections)}")
        logger.info(f"WebSocket 连接建立，当前连接数: {len(self.active_connections)}")

    def is_first_connection(self) -> bool:
        """
        检查是否是首次连接
        
        用于判断是否需要显示欢迎遮罩。
        
        Returns:
            如果是后端启动后的第一个连接返回 True
        """
        return not self._first_connection_occurred

    def mark_first_connection_done(self) -> None:
        """标记首次连接已完成"""
        self._first_connection_occurred = True
        logger.debug("首次连接标记完成")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        断开 WebSocket 连接
        
        Args:
            websocket: 要断开的 WebSocket 连接实例
        """
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        print(f"❌ WebSocket连接断开，当前连接数: {len(self.active_connections)}")
        logger.info(f"WebSocket 连接断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        发送个人消息
        
        向指定的 WebSocket 连接发送消息。
        
        Args:
            message: 要发送的消息字典
            websocket: 目标 WebSocket 连接实例
        """
        try:
            await websocket.send_json(message)
            logger.debug(f"发送个人消息: {message.get('type', 'unknown')}")
        except Exception as e:
            logger.warning(f"发送消息失败: {e}")
            print(f"发送消息失败: {e}")
    
    async def broadcast(self, message: dict) -> None:
        """
        广播消息到所有连接
        
        向所有活跃的 WebSocket 连接发送消息。
        
        Args:
            message: 要广播的消息字典
        """
        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)
        
        if len(disconnected) > 0:
            logger.debug(f"广播消息完成，清理 {len(disconnected)} 个断开的连接")

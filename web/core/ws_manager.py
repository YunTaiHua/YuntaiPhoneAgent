"""
ws_manager.py - WebSocket连接管理器
"""

import asyncio
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
        # 首次连接状态：后端启动后第一个连接需要显示欢迎遮罩
        self._first_connection_occurred = False
    
    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        print(f"✅ WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def is_first_connection(self) -> bool:
        """检查是否是首次连接（后端启动后的第一个连接）"""
        return not self._first_connection_occurred

    def mark_first_connection_done(self):
        """标记首次连接已完成"""
        self._first_connection_occurred = True
    
    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        print(f"❌ WebSocket连接断开，当前连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"发送消息失败: {e}")
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

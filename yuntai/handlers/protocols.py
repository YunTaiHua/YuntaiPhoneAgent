# yuntai/handlers/protocols.py
"""
Handler 回调协议定义
====================

定义 Handler 层与 GUI 层通信的回调接口，
替代直接 GUIView 依赖，消除反向依赖。
"""
from __future__ import annotations

from typing import Protocol, Any


class ViewCallbacks(Protocol):
    """GUI 视图回调协议

    定义 Handler 需要从视图层获取的操作接口。
    Handler 只依赖这些回调，不直接依赖 GUIView。
    """

    def get_component(self, name: str) -> Any:
        """获取 UI 组件"""
        ...

    def show_toast(self, message: str, toast_type: str = "info") -> None:
        """显示 Toast 通知"""
        ...

    def create_connection_page(self) -> None:
        """创建连接页面"""
        ...

    def show_page(self, index: int) -> None:
        """切换页面"""
        ...

    def create_dynamic_page(self) -> None:
        """创建动态功能页面"""
        ...

    def create_history_page(self) -> None:
        """创建历史记录页面"""
        ...

    def create_settings_page(self) -> None:
        """创建设置页面"""
        ...


class ControllerCallbacks(Protocol):
    """GUI 控制器回调协议

    定义 Handler 需要从控制器层获取的操作接口。
    """

    def show_toast(self, message: str, toast_type: str = "info") -> None:
        """显示 Toast 通知"""
        ...

    def update_tts_indicator(self, enabled: bool) -> None:
        """更新 TTS 状态指示器"""
        ...

    @property
    def message_queue(self) -> Any:
        """消息队列"""
        ...

    @property
    def task_manager(self) -> Any:
        """任务管理器"""
        ...

    @property
    def scrcpy_path(self) -> Any:
        """Scrcpy 路径"""
        ...

    @property
    def active_subprocesses(self) -> list:
        """活跃子进程列表"""
        ...

    @property
    def media_generator(self) -> Any:
        """媒体生成器"""
        ...

    @media_generator.setter
    def media_generator(self, value: Any) -> None:
        ...

    @property
    def latest_image_path(self) -> str:
        ...

    @latest_image_path.setter
    def latest_image_path(self, value: str) -> None:
        ...

    @property
    def latest_video_path(self) -> str:
        ...

    @latest_video_path.setter
    def latest_video_path(self, value: str) -> None:
        ...

    @property
    def latest_video_cover_path(self) -> str:
        ...

    @latest_video_cover_path.setter
    def latest_video_cover_path(self, value: str) -> None:
        ...

    @property
    def current_video_task_id(self) -> str:
        ...

    @current_video_task_id.setter
    def current_video_task_id(self, value: str) -> None:
        ...

    def _sync_device_to_task_chain(self) -> None:
        """同步设备到任务链"""
        ...

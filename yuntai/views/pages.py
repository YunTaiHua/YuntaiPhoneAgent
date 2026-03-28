"""
PageBuilder - 页面构建聚合器（PyQt6 重构版）
============================================

负责聚合各个具体页面的构建器，统一管理页面创建流程。

主要组件:
    - PageBuilder: 页面构建聚合器

页面构建器:
    - DashboardBuilder: 控制中心页面
    - ConnectionBuilder: 设备管理页面
    - TTSBuilder: TTS语音合成页面
    - HistoryBuilder: 历史记录页面
    - SettingsBuilder: 系统设置页面
    - DynamicBuilder: 动态功能页面

使用示例:
    >>> builder = PageBuilder(view)
    >>> builder.create_dashboard_page()  # 创建控制中心页面
    >>> builder.create_connection_page()  # 创建设备管理页面
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from yuntai.gui.styles import ThemeColors, DarkThemeColors, ThemeFonts, ThemeCorner
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

# 初始化模块日志记录器
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from yuntai.gui.gui_view import GUIView
    from yuntai.services.task_manager import TTSManager


class PageBuilder:
    """
    页面构建聚合器 - 负责调用各个具体页面的构建器
    
    统一管理所有页面的创建流程，确保每个页面只初始化一次。
    通过延迟导入避免循环依赖。
    
    Attributes:
        view: GUIView实例
        components: UI组件字典
        dashboard: 控制中心页面构建器
        connection: 设备管理页面构建器
        tts: TTS语音合成页面构建器
        history: 历史记录页面构建器
        settings: 系统设置页面构建器
        dynamic: 动态功能页面构建器
        page_initialized: 页面初始化标志列表
        tts_manager: TTS管理器实例
    """

    def __init__(self, view_instance: GUIView) -> None:
        """
        初始化页面构建聚合器
        
        Args:
            view_instance: GUIView实例
        """
        self.view: GUIView = view_instance
        self.components: dict[str, Any] = view_instance.components

        # 延迟导入避免循环依赖
        from .dashboard import DashboardBuilder
        from .connection import ConnectionBuilder
        from .tts import TTSBuilder
        from .history import HistoryBuilder
        from .settings import SettingsBuilder
        from .dynamic import DynamicBuilder

        # 初始化各页面构建器
        self.dashboard: DashboardBuilder = DashboardBuilder(view_instance)
        self.connection: ConnectionBuilder = ConnectionBuilder(view_instance)
        self.tts: TTSBuilder = TTSBuilder(view_instance)
        self.history: HistoryBuilder = HistoryBuilder(view_instance)
        self.settings: SettingsBuilder = SettingsBuilder(view_instance)
        self.dynamic: DynamicBuilder = DynamicBuilder(view_instance)

        # 页面初始化标志
        self.page_initialized: list[bool] = [False] * 6

        # TTS管理器引用
        self.tts_manager: TTSManager | None = None
        
        logger.debug("PageBuilder初始化完成")

    def _apply_current_theme_to_page(self, page_index: int) -> None:
        """应用当前主题到指定页面 - 暂时不做任何操作，避免对象被删除"""
        pass

    def create_dashboard_page(self) -> None:
        """创建控制中心页面（只执行一次）"""
        if not self.page_initialized[0]:
            self.dashboard.create_page()
            self.page_initialized[0] = True

    def create_connection_page(self) -> None:
        """创建设备管理页面（只执行一次）"""
        if not self.page_initialized[1]:
            self.connection.create_page()
            self.page_initialized[1] = True

    def create_tts_page(self, tts_manager: TTSManager) -> None:
        """创建TTS语音合成页面（每次都创建，支持自动刷新）"""
        if not self.page_initialized[2]:
            self.tts.create_page(tts_manager)
            self.page_initialized[2] = True

    def create_history_page(self) -> None:
        """创建历史记录页面（只执行一次）"""
        if not self.page_initialized[3]:
            self.history.create_page()
            self.page_initialized[3] = True

    def create_settings_page(self) -> None:
        """创建系统设置页面（只执行一次）"""
        if not self.page_initialized[5]:
            self.settings.create_page()
            self.page_initialized[5] = True

    def create_dynamic_page(self) -> None:
        """创建动态功能页面（只执行一次）"""
        if not self.page_initialized[4]:
            self.dynamic.create_page()
            self.page_initialized[4] = True

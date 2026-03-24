"""
PageBuilder - 页面构建聚合器（PyQt6 重构版）
负责聚合各个具体页面的构建器
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yuntai.gui.styles import ThemeColors, DarkThemeColors, ThemeFonts, ThemeCorner
from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

if TYPE_CHECKING:
    from yuntai.gui.gui_view import GUIView
    from yuntai.services.task_manager import TTSManager


class PageBuilder:
    """页面构建聚合器 - 负责调用各个具体页面的构建器"""

    def __init__(self, view_instance: GUIView) -> None:
        self.view: GUIView = view_instance
        self.components: dict[str, Any] = view_instance.components

        from .dashboard import DashboardBuilder
        from .connection import ConnectionBuilder
        from .tts import TTSBuilder
        from .history import HistoryBuilder
        from .settings import SettingsBuilder
        from .dynamic import DynamicBuilder

        self.dashboard: DashboardBuilder = DashboardBuilder(view_instance)
        self.connection: ConnectionBuilder = ConnectionBuilder(view_instance)
        self.tts: TTSBuilder = TTSBuilder(view_instance)
        self.history: HistoryBuilder = HistoryBuilder(view_instance)
        self.settings: SettingsBuilder = SettingsBuilder(view_instance)
        self.dynamic: DynamicBuilder = DynamicBuilder(view_instance)

        self.page_initialized: list[bool] = [False] * 6

        self.tts_manager: TTSManager | None = None

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

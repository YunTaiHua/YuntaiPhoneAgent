"""
PageBuilder - 页面构建聚合器
负责聚合各个具体页面的构建器
"""

from .theme import ThemeColors
# 导入各个具体的 Builder
from .dashboard import DashboardBuilder
from .connection import ConnectionBuilder
from .tts import TTSBuilder
from .history import HistoryBuilder
from .settings import SettingsBuilder
from .dynamic import DynamicBuilder


class PageBuilder:
    """页面构建聚合器 - 负责调用各个具体页面的构建器"""

    def __init__(self, view_instance):
        """
        Args:
            view_instance: GUIView 实例，用于访问 components 字典等
        """
        self.view = view_instance
        self.components = view_instance.components

        # 初始化各个具体的 Builder
        self.dashboard = DashboardBuilder(view_instance)
        self.connection = ConnectionBuilder(view_instance)
        self.tts = TTSBuilder(view_instance)
        self.history = HistoryBuilder(view_instance)
        self.settings = SettingsBuilder(view_instance)
        self.dynamic = DynamicBuilder(view_instance)

        # 页面初始化标志（6个页面）
        self.page_initialized = [False] * 6

        # TTS manager（用于页面创建时传递）
        self.tts_manager = None

    def create_dashboard_page(self):
        """创建控制中心页面（只执行一次）"""
        if not self.page_initialized[0]:
            self.dashboard.create_page()
            self.page_initialized[0] = True

    def create_connection_page(self):
        """创建设备管理页面（只执行一次）"""
        if not self.page_initialized[1]:
            self.connection.create_page()
            self.page_initialized[1] = True

    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面（每次都创建，支持自动刷新）"""
        if not self.page_initialized[2]:
            self.tts.create_page(tts_manager)
            self.page_initialized[2] = True

    def create_history_page(self):
        """创建历史记录页面（只执行一次）"""
        if not self.page_initialized[3]:
            self.history.create_page()
            self.page_initialized[3] = True

    def create_settings_page(self):
        """创建系统设置页面（只执行一次）"""
        if not self.page_initialized[5]:
            self.settings.create_page()
            self.page_initialized[5] = True

    def create_dynamic_page(self):
        """创建动态功能页面（只执行一次）"""
        if not self.page_initialized[4]:
            self.dynamic.create_page()
            self.page_initialized[4] = True

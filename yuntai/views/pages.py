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

    def create_dashboard_page(self):
        """创建控制中心页面"""
        self.dashboard.create_page()

    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面"""
        self.tts.create_page(tts_manager)

    def create_connection_page(self):
        """创建设备管理页面"""
        self.connection.create_page()

    def create_history_page(self):
        """创建历史记录页面"""
        self.history.create_page()

    def create_settings_page(self):
        """创建系统设置页面"""
        self.settings.create_page()

    def create_dynamic_page(self):
        """创建动态功能页面"""
        self.dynamic.create_page()

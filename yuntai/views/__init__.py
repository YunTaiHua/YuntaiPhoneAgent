from .theme import ThemeColors
from .pages import PageBuilder

# 同时导出具体的 Builder，供其他模块直接使用（如果需要）
from .dashboard import DashboardBuilder
from .connection import ConnectionBuilder
from .tts import TTSBuilder
from .history import HistoryBuilder
from .settings import SettingsBuilder
from .dynamic import DynamicBuilder

__all__ = [
    'ThemeColors',
    'PageBuilder',
    'DashboardBuilder',
    'ConnectionBuilder',
    'TTSBuilder',
    'HistoryBuilder',
    'SettingsBuilder',
    'DynamicBuilder'
]

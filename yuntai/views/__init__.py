"""
视图模块
========

提供 PyQt6 GUI 界面构建器，采用浅色米白色主题设计。

主要组件:
    - ThemeColors: 主题颜色配置
    - DarkThemeColors: 深色主题颜色配置
    - ThemeSpacing: 间距常量
    - ThemeCorner: 圆角常量
    - ThemeHeight: 高度常量
    - ThemeFonts: 字体配置
    - PageBuilder: 页面构建器基类
    - DashboardBuilder: 控制中心页面构建器
    - ConnectionBuilder: 设备管理页面构建器
    - TTSBuilder: TTS 设置页面构建器
    - HistoryBuilder: 历史记录页面构建器
    - SettingsBuilder: 设置页面构建器
    - DynamicBuilder: 动态功能页面构建器
    - ImagePreviewWindow: 图像预览窗口
    - VideoPreviewWindow: 视频预览窗口

设计特点:
    - 现代化卡片式布局
    - 统一的主题颜色系统
    - 响应式交互设计
    - 支持深色/浅色主题切换
"""
import logging

logger = logging.getLogger(__name__)

from .theme import ThemeColors, DarkThemeColors, ThemeSpacing, ThemeCorner, ThemeHeight, ThemeFonts
from .pages import PageBuilder
from .dashboard import DashboardBuilder
from .connection import ConnectionBuilder
from .tts import TTSBuilder
from .history import HistoryBuilder
from .settings import SettingsBuilder
from .dynamic import DynamicBuilder, ImagePreviewWindow, VideoPreviewWindow

__all__ = [
    'ThemeColors',
    'DarkThemeColors',
    'ThemeSpacing',
    'ThemeCorner',
    'ThemeHeight',
    'ThemeFonts',
    'PageBuilder',
    'DashboardBuilder',
    'ConnectionBuilder',
    'TTSBuilder',
    'HistoryBuilder',
    'SettingsBuilder',
    'DynamicBuilder',
    'ImagePreviewWindow',
    'VideoPreviewWindow'
]

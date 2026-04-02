"""
GUI 模块
========

提供 PyQt6 GUI 界面构建功能，包括视图和样式。

主要组件:
    - GUIView: GUI 视图类，负责页面构建和组件管理
    - ThemeColors: 主题颜色配置
    - DarkThemeColors: 深色主题颜色配置

功能特点:
    - 现代化卡片式布局
    - 统一的主题颜色系统
    - 响应式交互设计
    - 支持深色/浅色主题切换
"""
import logging

logger = logging.getLogger(__name__)

from .gui_view import GUIView
from .styles import ThemeColors, DarkThemeColors, ThemeSpacing, ThemeCorner, ThemeHeight, ThemeFonts

__all__ = [
    'GUIView',
    'ThemeColors',
    'DarkThemeColors',
    'ThemeSpacing',
    'ThemeCorner',
    'ThemeHeight',
    'ThemeFonts',
]

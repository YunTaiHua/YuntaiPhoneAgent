"""
GUI 模块
========

提供 PyQt6 GUI 界面构建功能，包括视图、样式和输出捕获。

主要组件:
    - GUIView: GUI 视图类，负责页面构建和组件管理
    - ThemeColors: 主题颜色配置
    - DarkThemeColors: 深色主题颜色配置
    - SimpleOutputCapture: GUI 端输出捕获类

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
from .output_capture import SimpleOutputCapture

# 兼容性别名
GUIOutputCapture = SimpleOutputCapture

__all__ = [
    'GUIView',
    'ThemeColors',
    'DarkThemeColors',
    'ThemeSpacing',
    'ThemeCorner',
    'ThemeHeight',
    'ThemeFonts',
    'SimpleOutputCapture',
    'GUIOutputCapture',  # 兼容性别名
]

"""
ThemeColors - UI主题颜色定义（兼容层）
======================================

浅色米白色现代化主题。

注意：此文件保留用于向后兼容。
新的样式定义已移至 yuntai/gui/styles.py

兼容导出:
    - ThemeColors: 浅色主题颜色类
    - DarkThemeColors: 深色主题颜色类
    - ThemeSpacing: 间距常量类
    - ThemeCorner: 圆角常量类
    - ThemeHeight: 高度常量类
    - ThemeFonts: 字体常量类
    - get_theme_colors: 获取当前主题颜色函数
    - apply_light_theme: 应用浅色主题函数
    - apply_dark_theme: 应用深色主题函数
    - get_main_stylesheet: 获取主样式表函数
    - get_overlay_stylesheet: 获取遮罩层样式表函数
"""

# 从新的样式模块导入所有内容
from yuntai.gui.styles import (
    ThemeColors,
    DarkThemeColors,
    ThemeSpacing,
    ThemeCorner,
    ThemeHeight,
    ThemeFonts,
    get_theme_colors,
    apply_light_theme,
    apply_dark_theme,
    get_main_stylesheet,
    get_overlay_stylesheet
)

# 保持向后兼容性
__all__ = [
    'ThemeColors',
    'DarkThemeColors', 
    'ThemeSpacing',
    'ThemeCorner',
    'ThemeHeight',
    'ThemeFonts',
    'get_theme_colors',
    'apply_light_theme',
    'apply_dark_theme',
    'get_main_stylesheet',
    'get_overlay_stylesheet'
]

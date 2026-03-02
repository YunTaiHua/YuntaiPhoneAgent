"""
ThemeColors - UI主题颜色定义（兼容层）
浅色米白色现代化主题

注意：此文件保留用于向后兼容。
新的样式定义已移至 yuntai/gui/styles.py
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

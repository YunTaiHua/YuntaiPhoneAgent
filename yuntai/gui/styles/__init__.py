"""
styles.py - PyQt6 样式定义
===========================

完全保持与原 tkinter/customtkinter 主题一致的样式。

主要组件:
    - ThemeColors: 浅色主题颜色常量
    - DarkThemeColors: 深色主题颜色常量
    - ThemeSpacing: 间距常量
    - ThemeCorner: 圆角常量
    - ThemeHeight: 高度常量
    - ThemeShadow: 阴影常量
    - ThemeFonts: 字体常量
    - DialogStyle: 弹窗样式常量

主要函数:
    - get_theme_colors: 获取当前主题颜色
    - apply_light_theme: 应用浅色主题
    - apply_dark_theme: 应用深色主题
    - get_main_stylesheet: 获取主样式表
    - get_overlay_stylesheet: 获取遮罩层样式表
    - show_warning_dialog: 显示警告对话框
    - show_confirm_dialog: 显示确认对话框
"""

# 样式常量 - 颜色
from yuntai.gui.styles.colors import ThemeColors, DarkThemeColors, get_theme_colors

# 样式常量 - 字体
from yuntai.gui.styles.fonts import ThemeFonts

# 样式常量 - 尺寸
from yuntai.gui.styles.dimensions import (
    ThemeSpacing, ThemeCorner, ThemeHeight, ThemeShadow, DialogStyle
)

# 样式表函数
from yuntai.gui.styles.stylesheets import (
    get_main_stylesheet,
    get_overlay_stylesheet,
    get_dialog_stylesheet,
    get_dialog_button_stylesheet,
    get_dialog_card_stylesheet,
    get_dialog_textedit_stylesheet,
    get_dialog_list_stylesheet,
    get_dialog_tree_stylesheet,
    get_dialog_combobox_stylesheet,
    get_dialog_checkbox_stylesheet,
    show_warning_dialog,
    show_confirm_dialog,
)

# 主题应用函数
from yuntai.gui.styles.theme import apply_light_theme, apply_dark_theme

__all__ = [
    # 颜色
    'ThemeColors', 'DarkThemeColors', 'get_theme_colors',
    # 字体
    'ThemeFonts',
    # 尺寸
    'ThemeSpacing', 'ThemeCorner', 'ThemeHeight', 'ThemeShadow', 'DialogStyle',
    # 样式表函数
    'get_main_stylesheet', 'get_overlay_stylesheet',
    'get_dialog_stylesheet', 'get_dialog_button_stylesheet',
    'get_dialog_card_stylesheet', 'get_dialog_textedit_stylesheet',
    'get_dialog_list_stylesheet', 'get_dialog_tree_stylesheet',
    'get_dialog_combobox_stylesheet', 'get_dialog_checkbox_stylesheet',
    # 对话框函数
    'show_warning_dialog', 'show_confirm_dialog',
    # 主题函数
    'apply_light_theme', 'apply_dark_theme',
]

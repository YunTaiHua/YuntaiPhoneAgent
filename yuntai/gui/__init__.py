"""
yuntai.gui 模块
PyQt6 GUI 组件
"""

# 延迟导入，避免循环依赖
def __getattr__(name):
    """延迟导入机制"""
    if name == 'GUIController':
        from .gui_controller import GUIController
        return GUIController
    elif name == 'GUIView':
        from .gui_view import GUIView
        return GUIView
    elif name == 'SimpleOutputCapture':
        from .output_capture import SimpleOutputCapture
        return SimpleOutputCapture
    elif name in ('ThemeColors', 'DarkThemeColors', 'ThemeSpacing', 'ThemeCorner', 
                  'ThemeHeight', 'ThemeFonts', 'get_theme_colors', 'apply_light_theme',
                  'apply_dark_theme', 'get_main_stylesheet'):
        from . import styles
        return getattr(styles, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    'GUIController',
    'GUIView',
    'SimpleOutputCapture',
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
]

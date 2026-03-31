"""
theme.py - 主题应用函数
========================

定义应用浅色和深色主题的函数。

主要函数:
    - apply_light_theme: 应用浅色主题
    - apply_dark_theme: 应用深色主题
"""

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from .colors import ThemeColors, DarkThemeColors


def apply_light_theme(app: QApplication):
    """
    应用浅色主题到应用程序

    设置应用程序调色板为浅色主题配色方案。

    Args:
        app: QApplication实例
    """
    colors = ThemeColors

    palette = QPalette()

    # 窗口背景
    palette.setColor(QPalette.ColorRole.Window, QColor(colors.BG_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.TEXT_PRIMARY))

    # 基础颜色
    palette.setColor(QPalette.ColorRole.Base, QColor(colors.BG_CARD))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.BG_CARD_ALT))

    # 文本
    palette.setColor(QPalette.ColorRole.Text, QColor(colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors.TEXT_SECONDARY))

    # 按钮和高亮
    palette.setColor(QPalette.ColorRole.Button, QColor(colors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.TEXT_LIGHT))

    # 禁用状态 - 使用 setColorGroup 方法
    palette.setColorGroup(
        QPalette.ColorGroup.Disabled,
        QColor(colors.TEXT_DISABLED),  # foreground (WindowText)
        QColor(colors.BG_CARD),        # button
        QColor(colors.BG_CARD),        # light
        QColor(colors.BG_CARD_ALT),    # dark
        QColor(colors.BG_CARD_ALT),    # mid
        QColor(colors.TEXT_DISABLED),  # text
        QColor(colors.TEXT_DISABLED),  # bright_text
        QColor(colors.BG_MAIN),        # base
        QColor(colors.BG_MAIN)         # background (Window)
    )

    # 工具提示
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.TEXT_PRIMARY))

    app.setPalette(palette)


def apply_dark_theme(app: QApplication):
    """
    应用深色主题到应用程序

    设置应用程序调色板为深色主题配色方案。

    Args:
        app: QApplication实例
    """
    colors = DarkThemeColors

    palette = QPalette()

    # 窗口背景
    palette.setColor(QPalette.ColorRole.Window, QColor(colors.BG_MAIN))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors.TEXT_PRIMARY))

    # 基础颜色
    palette.setColor(QPalette.ColorRole.Base, QColor(colors.BG_CARD))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors.BG_CARD_ALT))

    # 文本
    palette.setColor(QPalette.ColorRole.Text, QColor(colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors.TEXT_SECONDARY))

    # 按钮和高亮
    palette.setColor(QPalette.ColorRole.Button, QColor(colors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors.TEXT_LIGHT))

    # 禁用状态 - 使用 setColorGroup 方法
    palette.setColorGroup(
        QPalette.ColorGroup.Disabled,
        QColor(colors.TEXT_DISABLED),  # foreground (WindowText)
        QColor(colors.BG_CARD),        # button
        QColor(colors.BG_CARD),        # light
        QColor(colors.BG_CARD_ALT),    # dark
        QColor(colors.BG_CARD_ALT),    # mid
        QColor(colors.TEXT_DISABLED),  # text
        QColor(colors.TEXT_DISABLED),  # bright_text
        QColor(colors.BG_MAIN),        # base
        QColor(colors.BG_MAIN)         # background (Window)
    )

    # 工具提示
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors.TEXT_PRIMARY))

    app.setPalette(palette)

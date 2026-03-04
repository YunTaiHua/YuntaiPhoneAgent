"""
styles.py - PyQt6 样式定义
完全保持与原 tkinter/customtkinter 主题一致的样式
"""

from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWidgets import QApplication


class ThemeColors:
    """现代化浅色UI主题颜色类 - 米白色风格"""
    # 主色调 - 柔和的蓝色系
    PRIMARY = "#5B8DEE"          # 主按钮色 - 柔和蓝
    PRIMARY_HOVER = "#4A7BDD"     # 主按钮悬停色（稍深提升对比度）
    SECONDARY = "#A78BFA"        # 次要按钮色 - 亮紫色
    SECONDARY_HOVER = "#8B5CF6"   # 次要按钮悬停色
    ACCENT = "#F97316"           # 强调色 - 活力橙
    ACCENT_HOVER = "#EA580C"      # 强调色悬停

    # 功能色
    SUCCESS = "#22C55E"          # 成功 - 标准绿
    SUCCESS_HOVER = "#16A34A"     # 成功悬停
    WARNING = "#F59E0B"          # 警告 - 琥珀色
    WARNING_HOVER = "#D97706"     # 警告悬停
    DANGER = "#EF4444"           # 危险 - 标准红
    DANGER_HOVER = "#DC2626"      # 危险悬停

    # 状态指示色 - 浅蓝色系（用于导航栏状态和toast）
    STATUS_ACTIVE = "#64D2FF"     # 激活状态 - 清新透亮的天蓝色
    STATUS_INACTIVE = "#9CA3AF"   # 未激活状态 - 灰色

    # 背景色 - 更纯净的米白色系
    BG_MAIN = "#FDFCFA"          # 主背景 - 暖白
    BG_NAV = "#FFFFFF"           # 导航栏背景 - 纯白
    BG_CARD = "#FFFFFF"          # 卡片背景 - 纯白
    BG_CARD_ALT = "#F8F7F5"      # 卡片背景替代 - 浅灰米白
    BG_HOVER = "#F0EFE9"         # 悬停背景 - 浅米色
    BG_INPUT = "#FFFFFF"         # 输入框背景
    BG_SCROLLBAR = "#E0DDD8"     # 滚动条背景

    # 边框色
    BORDER_LIGHT = "#E5E3E0"     # 浅色边框
    BORDER_MEDIUM = "#D0CDC7"    # 中等边框
    BORDER_FOCUS = "#5B8DEE"     # 聚焦边框

    # 文字色
    TEXT_PRIMARY = "#2C3E50"     # 主文字 - 深蓝灰
    TEXT_SECONDARY = "#6B7280"   # 次要文字 - 中灰
    TEXT_DISABLED = "#9CA3AF"    # 禁用文字 - 浅灰
    TEXT_LIGHT = "#FFFFFF"       # 浅色文字（用于深色背景按钮）

    # 特殊颜色
    NAV_HIGHLIGHT_BG = "#EFF3FF"
    NAV_HIGHLIGHT_HOVER = "#E0E7FF"
    OPTION_BUTTON_COLOR = "#C4C9D0"
    OPTION_BUTTON_HOVER = "#A8AEB5"


class DarkThemeColors:
    """深色主题颜色类"""
    # 主色调
    PRIMARY = "#60A5FA"
    PRIMARY_HOVER = "#3B82F6"
    SECONDARY = "#A78BFA"
    SECONDARY_HOVER = "#8B5CF6"
    ACCENT = "#FB923C"
    ACCENT_HOVER = "#F97316"

    # 功能色
    SUCCESS = "#22C55E"
    SUCCESS_HOVER = "#16A34A"
    WARNING = "#F59E0B"
    WARNING_HOVER = "#D97706"
    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"

    # 状态指示色 - 浅蓝色系（用于导航栏状态和toast）
    STATUS_ACTIVE = "#64D2FF"     # 激活状态 - 清新透亮的天蓝色
    STATUS_INACTIVE = "#6B7280"   # 未激活状态 - 灰色

    # 背景色
    BG_MAIN = "#1A1A2E"
    BG_NAV = "#16213E"
    BG_CARD = "#1F2937"
    BG_CARD_ALT = "#374151"
    BG_HOVER = "#2D3748"
    BG_INPUT = "#1F2937"
    BG_SCROLLBAR = "#4B5563"

    # 边框色
    BORDER_LIGHT = "#374151"
    BORDER_MEDIUM = "#4B5563"
    BORDER_FOCUS = "#60A5FA"

    # 文字色
    TEXT_PRIMARY = "#F3F4F6"
    TEXT_SECONDARY = "#9CA3AF"
    TEXT_DISABLED = "#6B7280"
    TEXT_LIGHT = "#FFFFFF"

    # 特殊颜色
    NAV_HIGHLIGHT_BG = "#1E3A5F"      # 导航高光背景 - 深蓝色，与PRIMARY文字形成对比
    NAV_HIGHLIGHT_HOVER = "#2D4A6F"   # 导航高光悬停 - 稍浅的深蓝色
    OPTION_BUTTON_COLOR = "#4B5563"
    OPTION_BUTTON_HOVER = "#6B7280"


class ThemeSpacing:
    """间距常量"""
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32


class ThemeCorner:
    """圆角常量"""
    SM = 8
    MD = 12
    LG = 16


class ThemeHeight:
    """高度常量"""
    BUTTON_SM = 32
    BUTTON_MD = 40
    BUTTON_LG = 48
    INPUT_SM = 36
    INPUT_MD = 42


class ThemeShadow:
    """阴影常量 - 用于卡片立体感"""
    # 浅色主题阴影 (使用rgba格式，alpha值为0-255)
    LIGHT_SM = (0, 1, 3, (0, 0, 0, 20))      # 小阴影 (0.08 * 255 ≈ 20)
    LIGHT_MD = (0, 2, 8, (0, 0, 0, 26))      # 中等阴影 (0.10 * 255 ≈ 26)
    LIGHT_LG = (0, 4, 12, (0, 0, 0, 31))     # 大阴影 (0.12 * 255 ≈ 31)
    
    # 深色主题阴影
    DARK_SM = (0, 1, 3, (0, 0, 0, 64))       # (0.25 * 255 ≈ 64)
    DARK_MD = (0, 2, 8, (0, 0, 0, 77))       # (0.30 * 255 ≈ 77)
    DARK_LG = (0, 4, 12, (0, 0, 0, 89))      # (0.35 * 255 ≈ 89)


class ThemeFonts:
    """字体常量"""
    # 主字体
    FONT_FAMILY = "Microsoft YaHei"
    FONT_FAMILY_EMOJI = "Segoe UI Emoji"
    FONT_FAMILY_CODE = "Consolas"
    
    # 标题字体
    TITLE_LARGE = QFont(FONT_FAMILY, 28, QFont.Weight.Bold)
    TITLE_MEDIUM = QFont(FONT_FAMILY, 24, QFont.Weight.Bold)
    TITLE_SMALL = QFont(FONT_FAMILY, 18, QFont.Weight.Bold)
    
    # 常用别名
    TITLE = QFont(FONT_FAMILY, 20, QFont.Weight.Bold)  # 标题
    SUBTITLE = QFont(FONT_FAMILY, 16, QFont.Weight.Bold)  # 副标题
    
    # 正文字体
    BODY_LARGE = QFont(FONT_FAMILY, 16)
    BODY_MEDIUM = QFont(FONT_FAMILY, 14)
    BODY_SMALL = QFont(FONT_FAMILY, 13)
    BODY_XSMALL = QFont(FONT_FAMILY, 12)
    BODY_TINY = QFont(FONT_FAMILY, 11)
    BODY_MINI = QFont(FONT_FAMILY, 10)
    
    # 常用别名
    BODY = QFont(FONT_FAMILY, 14)  # 正文
    
    # 代码字体
    CODE_MEDIUM = QFont(FONT_FAMILY_CODE, 13)
    CODE_SMALL = QFont(FONT_FAMILY_CODE, 12)
    
    # Emoji字体
    EMOJI_LARGE = QFont(FONT_FAMILY_EMOJI, 40)
    EMOJI_MEDIUM = QFont(FONT_FAMILY_EMOJI, 14)
    EMOJI_SMALL = QFont(FONT_FAMILY_EMOJI, 12)


def get_theme_colors(is_dark=False):
    """获取当前主题颜色"""
    return DarkThemeColors if is_dark else ThemeColors


def apply_light_theme(app: QApplication):
    """应用浅色主题到应用程序"""
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
    """应用深色主题到应用程序"""
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


# 样式表定义
def get_main_stylesheet(colors=ThemeColors):
    """获取主样式表"""
    return f"""
        /* 全局样式 */
        QWidget {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            color: {colors.TEXT_PRIMARY};
        }}
        
        /* 标签默认无边框 */
        QLabel {{
            background: transparent;
            border: none;
        }}
        
        /* 对话框样式 */
        QDialog {{
            background-color: {colors.BG_MAIN};
        }}
        
        /* 主窗口 */
        QMainWindow {{
            background-color: {colors.BG_MAIN};
        }}
        
        /* 框架 */
        QFrame#navFrame {{
            background-color: {colors.BG_NAV};
            border: none;
        }}
        
        QFrame#contentFrame {{
            background-color: {colors.BG_MAIN};
        }}
        
        QFrame#statusBar {{
            background-color: {colors.BG_NAV};
            border-top: 1px solid {colors.BORDER_LIGHT};
        }}
        
        /* 卡片样式 */
        QFrame#card {{
            background-color: {colors.BG_CARD};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
        }}
        
        /* 标签 */
        QLabel {{
            color: {colors.TEXT_PRIMARY};
            background-color: transparent;
        }}
        
        QLabel#titleLarge {{
            font-size: 28px;
            font-weight: bold;
        }}
        
        QLabel#titleMedium {{
            font-size: 24px;
            font-weight: bold;
        }}
        
        QLabel#titleSmall {{
            font-size: 18px;
            font-weight: bold;
        }}
        
        QLabel#secondary {{
            color: {colors.TEXT_SECONDARY};
        }}
        
        QLabel#disabled {{
            color: {colors.TEXT_DISABLED};
        }}
        
        /* 按钮 */
        QPushButton {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 14px;
            padding: 8px 16px;
            border-radius: {ThemeCorner.MD}px;
            border: none;
        }}
        
        QPushButton#primaryButton {{
            background-color: {colors.PRIMARY};
            color: {colors.TEXT_LIGHT};
            font-weight: 500;
        }}
        
        QPushButton#primaryButton:hover {{
            background-color: {colors.PRIMARY_HOVER};
        }}
        
        QPushButton#primaryButton:pressed {{
            background-color: {colors.PRIMARY_HOVER};
            padding-top: 9px;
            padding-bottom: 7px;
        }}
        
        QPushButton#primaryButton:disabled {{
            background-color: {colors.BG_HOVER};
            color: {colors.TEXT_DISABLED};
        }}
        
        QPushButton#secondaryButton {{
            background-color: {colors.SECONDARY};
            color: {colors.TEXT_LIGHT};
            font-weight: 500;
        }}
        
        QPushButton#secondaryButton:hover {{
            background-color: {colors.SECONDARY_HOVER};
        }}
        
        QPushButton#secondaryButton:pressed {{
            background-color: {colors.SECONDARY_HOVER};
            padding-top: 9px;
            padding-bottom: 7px;
        }}
        
        QPushButton#dangerButton {{
            background-color: {colors.DANGER};
            color: {colors.TEXT_LIGHT};
            font-weight: 500;
        }}
        
        QPushButton#dangerButton:hover {{
            background-color: {colors.DANGER_HOVER};
        }}
        
        QPushButton#dangerButton:pressed {{
            background-color: {colors.DANGER_HOVER};
            padding-top: 9px;
            padding-bottom: 7px;
        }}
        
        QPushButton#successButton {{
            background-color: {colors.SUCCESS};
            color: {colors.TEXT_LIGHT};
            font-weight: 500;
        }}
        
        QPushButton#successButton:hover {{
            background-color: {colors.SUCCESS_HOVER};
        }}
        
        QPushButton#successButton:pressed {{
            background-color: {colors.SUCCESS_HOVER};
            padding-top: 9px;
            padding-bottom: 7px;
        }}
        
        QPushButton#warningButton {{
            background-color: {colors.WARNING};
            color: {colors.TEXT_LIGHT};
            font-weight: 500;
        }}
        
        QPushButton#warningButton:hover {{
            background-color: {colors.WARNING_HOVER};
        }}
        
        QPushButton#warningButton:pressed {{
            background-color: {colors.WARNING_HOVER};
            padding-top: 9px;
            padding-bottom: 7px;
        }}
        
        QPushButton#accentButton {{
            background-color: {colors.ACCENT};
            color: {colors.TEXT_LIGHT};
            font-weight: 500;
        }}
        
        QPushButton#accentButton:hover {{
            background-color: {colors.ACCENT_HOVER};
        }}
        
        QPushButton#accentButton:pressed {{
            background-color: {colors.ACCENT_HOVER};
            padding-top: 9px;
            padding-bottom: 7px;
        }}
        
        QPushButton#navButton {{
            background-color: transparent;
            color: {colors.TEXT_PRIMARY};
            text-align: left;
            padding: 10px 15px;
            border-radius: {ThemeCorner.MD}px;
        }}
        
        QPushButton#navButton:hover {{
            background-color: {colors.BG_HOVER};
        }}
        
        QPushButton#navButton:checked {{
            background-color: {colors.NAV_HIGHLIGHT_BG};
            color: {colors.PRIMARY};
        }}
        
        QPushButton#iconButton {{
            background-color: {colors.BG_HOVER};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: 20px;
        }}
        
        QPushButton#iconButton:hover {{
            background-color: {colors.BG_CARD_ALT};
        }}
        
        /* 输入框 */
        QLineEdit {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 13px;
            padding: 8px 12px;
            background-color: {colors.BG_INPUT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_MEDIUM};
            border-radius: {ThemeCorner.MD}px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {colors.BORDER_FOCUS};
        }}
        
        QLineEdit:disabled {{
            background-color: {colors.BG_HOVER};
            color: {colors.TEXT_DISABLED};
        }}
        
        /* 文本编辑框 */
        QTextEdit {{
            font-family: "{ThemeFonts.FONT_FAMILY_CODE}";
            font-size: 13px;
            padding: 8px;
            background-color: {colors.BG_CARD_ALT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
        }}
        
        QTextEdit:focus {{
            border: 1px solid {colors.BORDER_FOCUS};
        }}
        
        QTextEdit:disabled {{
            background-color: {colors.BG_HOVER};
            color: {colors.TEXT_DISABLED};
        }}
        
        /* 下拉框 */
        QComboBox {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 13px;
            padding: 8px 12px;
            background-color: {colors.BG_INPUT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_MEDIUM};
            border-radius: {ThemeCorner.MD}px;
        }}
        
        QComboBox:hover {{
            border: 1px solid {colors.BORDER_FOCUS};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {colors.TEXT_SECONDARY};
            margin-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors.BG_CARD};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            selection-background-color: {colors.PRIMARY};
            selection-color: {colors.TEXT_LIGHT};
        }}
        
        /* 单选按钮 */
        QRadioButton {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 13px;
            color: {colors.TEXT_PRIMARY};
            spacing: 8px;
        }}
        
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {colors.BORDER_MEDIUM};
            background-color: {colors.BG_INPUT};
        }}
        
        QRadioButton::indicator:checked {{
            border: 2px solid {colors.PRIMARY};
            background-color: {colors.PRIMARY};
        }}
        
        QRadioButton::indicator:hover {{
            border: 2px solid {colors.PRIMARY_HOVER};
        }}
        
        /* 复选框 */
        QCheckBox {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 13px;
            color: {colors.TEXT_PRIMARY};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {colors.BORDER_MEDIUM};
            background-color: {colors.BG_INPUT};
        }}
        
        QCheckBox::indicator:checked {{
            border: 2px solid {colors.PRIMARY};
            background-color: {colors.PRIMARY};
        }}
        
        QCheckBox::indicator:hover {{
            border: 2px solid {colors.PRIMARY_HOVER};
        }}
        
        /* 滚动条 */
        QScrollBar:vertical {{
            background-color: {colors.BG_CARD_ALT};
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors.BG_SCROLLBAR};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors.PRIMARY};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors.BG_CARD_ALT};
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors.BG_SCROLLBAR};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors.PRIMARY};
        }}
        
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        
        /* 进度条 */
        QProgressBar {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 12px;
            background-color: {colors.BG_CARD_ALT};
            border: none;
            border-radius: 4px;
            text-align: center;
            color: {colors.TEXT_PRIMARY};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors.PRIMARY};
            border-radius: 4px;
        }}
        
        /* 滑块 */
        QSlider::groove:horizontal {{
            background-color: {colors.BG_CARD_ALT};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background-color: {colors.PRIMARY};
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background-color: {colors.PRIMARY_HOVER};
        }}
        
        /* 列表 */
        QListWidget {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 13px;
            background-color: {colors.BG_CARD_ALT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        QListWidget::item:selected {{
            background-color: {colors.PRIMARY};
            color: {colors.TEXT_LIGHT};
        }}
        
        QListWidget::item:hover {{
            background-color: {colors.BG_HOVER};
        }}
        
        /* 选项卡 */
        QTabWidget::pane {{
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
            background-color: {colors.BG_CARD};
        }}
        
        QTabBar::tab {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 13px;
            padding: 10px 20px;
            background-color: {colors.BG_CARD_ALT};
            border-top-left-radius: {ThemeCorner.SM}px;
            border-top-right-radius: {ThemeCorner.SM}px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors.PRIMARY};
            color: {colors.TEXT_LIGHT};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors.BG_HOVER};
        }}
        
        /* 消息框 */
        QMessageBox {{
            background-color: {colors.BG_CARD};
        }}
        
        QMessageBox QLabel {{
            color: {colors.TEXT_PRIMARY};
        }}
        
        /* 工具提示 */
        QToolTip {{
            font-family: "{ThemeFonts.FONT_FAMILY}";
            font-size: 12px;
            background-color: {colors.BG_CARD};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: 4px;
            padding: 4px 8px;
        }}
    """


def get_overlay_stylesheet(colors=ThemeColors):
    """获取遮罩层样式表"""
    return f"""
        QFrame#overlayFrame {{
            background-color: {colors.BG_MAIN};
        }}
        
        QFrame#overlayCard {{
            background-color: {colors.BG_CARD};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.LG}px;
        }}
    """


# ==================== 弹窗样式常量和辅助函数 ====================

class DialogStyle:
    """弹窗样式常量"""
    # 弹窗尺寸
    DIALOG_WIDTH_SMALL = 400
    DIALOG_HEIGHT_SMALL = 350
    DIALOG_WIDTH_MEDIUM = 500
    DIALOG_HEIGHT_MEDIUM = 450
    DIALOG_WIDTH_LARGE = 600
    DIALOG_HEIGHT_LARGE = 500
    
    # 弹窗内边距
    DIALOG_MARGIN = 20
    DIALOG_SPACING = 12
    
    # 按钮尺寸
    BUTTON_HEIGHT = 40
    BUTTON_WIDTH = 120
    BUTTON_HEIGHT_SMALL = 36
    BUTTON_WIDTH_SMALL = 100


def get_dialog_stylesheet(colors=ThemeColors):
    """获取弹窗样式表"""
    return f"""
        QDialog {{
            background-color: {colors.BG_MAIN};
        }}
    """


def get_dialog_button_stylesheet(style_type: str, colors=ThemeColors):
    """获取弹窗按钮样式表
    
    Args:
        style_type: 按钮类型 (primary, secondary, danger, success, warning, accent, cancel)
        colors: 颜色主题
    """
    colors_map = {
        "primary": (colors.PRIMARY, colors.PRIMARY_HOVER),
        "secondary": (colors.SECONDARY, colors.SECONDARY_HOVER),
        "danger": (colors.DANGER, colors.DANGER_HOVER),
        "success": (colors.SUCCESS, colors.SUCCESS_HOVER),
        "warning": (colors.WARNING, colors.WARNING_HOVER),
        "accent": (colors.ACCENT, colors.ACCENT_HOVER),
        "cancel": (colors.TEXT_SECONDARY, colors.TEXT_DISABLED),
    }
    
    bg_color, hover_color = colors_map.get(style_type, (colors.PRIMARY, colors.PRIMARY_HOVER))
    
    return f"""
        QPushButton {{
            background-color: {bg_color};
            color: {colors.TEXT_LIGHT};
            border: none;
            border-radius: {ThemeCorner.MD}px;
            padding: 0 15px;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:disabled {{
            background-color: {colors.BG_HOVER};
            color: {colors.TEXT_DISABLED};
        }}
    """


def get_dialog_card_stylesheet(colors=ThemeColors):
    """获取弹窗内卡片样式表"""
    return f"""
        QFrame {{
            background-color: {colors.BG_CARD};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
        }}
    """


def get_dialog_textedit_stylesheet(colors=ThemeColors):
    """获取弹窗内文本框样式表"""
    return f"""
        QTextEdit {{
            background-color: {colors.BG_CARD_ALT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
            padding: 8px;
        }}
    """


def get_dialog_list_stylesheet(colors=ThemeColors):
    """获取弹窗内列表样式表"""
    return f"""
        QListWidget {{
            background-color: {colors.BG_CARD_ALT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
            outline: none;
            padding: 4px;
        }}
        QListWidget::item {{
            padding: 8px 12px;
            border-radius: 4px;
        }}
        QListWidget::item:selected {{
            background-color: {colors.PRIMARY};
            color: {colors.TEXT_LIGHT};
        }}
        QListWidget::item:hover {{
            background-color: {colors.BG_HOVER};
        }}
    """


def get_dialog_tree_stylesheet(colors=ThemeColors):
    """获取弹窗内树形列表样式表"""
    return f"""
        QTreeWidget {{
            background-color: {colors.BG_CARD_ALT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            border-radius: {ThemeCorner.MD}px;
            outline: none;
            padding: 4px;
        }}
        QTreeWidget::item {{
            padding: 6px;
            border-radius: 4px;
        }}
        QTreeWidget::item:selected {{
            background-color: {colors.PRIMARY};
            color: {colors.TEXT_LIGHT};
        }}
        QTreeWidget::item:hover {{
            background-color: {colors.BG_HOVER};
        }}
    """


def get_dialog_combobox_stylesheet(colors=ThemeColors):
    """获取弹窗内下拉框样式表"""
    return f"""
        QComboBox {{
            background-color: {colors.BG_INPUT};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_MEDIUM};
            border-radius: {ThemeCorner.MD}px;
            padding: 6px 12px;
        }}
        QComboBox:hover {{
            border: 1px solid {colors.BORDER_FOCUS};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {colors.TEXT_SECONDARY};
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors.BG_CARD};
            color: {colors.TEXT_PRIMARY};
            border: 1px solid {colors.BORDER_LIGHT};
            selection-background-color: {colors.PRIMARY};
            selection-color: {colors.TEXT_LIGHT};
        }}
    """


def get_dialog_checkbox_stylesheet(colors=ThemeColors):
    """获取弹窗内复选框样式表"""
    return f"""
        QCheckBox {{
            color: {colors.TEXT_PRIMARY};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid {colors.BORDER_MEDIUM};
            background-color: {colors.BG_INPUT};
        }}
        QCheckBox::indicator:checked {{
            border: 2px solid {colors.PRIMARY};
            background-color: {colors.PRIMARY};
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {colors.PRIMARY_HOVER};
        }}
    """


# ==================== 通用对话框函数 ====================

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


def show_warning_dialog(parent, title: str, message: str, button_text: str = "知道了"):
    """显示警告对话框"""
    colors = parent.colors if hasattr(parent, 'colors') else ThemeColors
    
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFixedSize(380, 180)
    dialog.setModal(True)
    dialog.setStyleSheet(get_dialog_stylesheet(colors))
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(
        DialogStyle.DIALOG_MARGIN, 
        DialogStyle.DIALOG_MARGIN, 
        DialogStyle.DIALOG_MARGIN, 
        DialogStyle.DIALOG_MARGIN
    )
    layout.setSpacing(DialogStyle.DIALOG_SPACING)
    
    # 标题
    title_label = QLabel(f"⚠️ {title}")
    title_label.setFont(ThemeFonts.SUBTITLE)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {colors.WARNING}; background: transparent; border: none;")
    layout.addWidget(title_label)
    
    # 消息
    message_label = QLabel(message)
    message_label.setFont(ThemeFonts.BODY_MEDIUM)
    message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    message_label.setWordWrap(True)
    message_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
    layout.addWidget(message_label)
    
    layout.addStretch()
    
    # 确认按钮
    confirm_btn = QPushButton(button_text)
    confirm_btn.setFont(ThemeFonts.BODY_MEDIUM)
    confirm_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
    confirm_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
    confirm_btn.setStyleSheet(get_dialog_button_stylesheet("warning", colors))
    confirm_btn.clicked.connect(dialog.accept)
    layout.addWidget(confirm_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    dialog.exec()


def show_confirm_dialog(parent, title: str, message: str, confirm_text: str = "确认", 
                        cancel_text: str = "取消", confirm_type: str = "danger") -> bool:
    """显示确认对话框，返回用户是否点击确认"""
    colors = parent.colors if hasattr(parent, 'colors') else ThemeColors
    
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFixedSize(420, 200)
    dialog.setModal(True)
    dialog.setStyleSheet(get_dialog_stylesheet(colors))
    
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(
        DialogStyle.DIALOG_MARGIN, 
        DialogStyle.DIALOG_MARGIN, 
        DialogStyle.DIALOG_MARGIN, 
        DialogStyle.DIALOG_MARGIN
    )
    layout.setSpacing(DialogStyle.DIALOG_SPACING)
    
    # 标题
    title_label = QLabel(f"⚠️ {title}")
    title_label.setFont(ThemeFonts.SUBTITLE)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent; border: none;")
    layout.addWidget(title_label)
    
    # 消息
    message_label = QLabel(message)
    message_label.setFont(ThemeFonts.BODY_MEDIUM)
    message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    message_label.setWordWrap(True)
    message_label.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent; border: none;")
    layout.addWidget(message_label)
    
    layout.addStretch()
    
    # 按钮区域
    button_layout = QHBoxLayout()
    button_layout.setSpacing(15)
    
    result = [False]  # 使用列表来存储结果
    
    # 取消按钮
    cancel_btn = QPushButton(cancel_text)
    cancel_btn.setFont(ThemeFonts.BODY_MEDIUM)
    cancel_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
    cancel_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
    cancel_btn.setStyleSheet(get_dialog_button_stylesheet("secondary", colors))
    cancel_btn.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_btn)
    
    # 确认按钮
    confirm_btn = QPushButton(confirm_text)
    confirm_btn.setFont(ThemeFonts.BODY_MEDIUM)
    confirm_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT)
    confirm_btn.setFixedWidth(DialogStyle.BUTTON_WIDTH)
    confirm_btn.setStyleSheet(get_dialog_button_stylesheet(confirm_type, colors))
    def on_confirm():
        result[0] = True
        dialog.accept()
    confirm_btn.clicked.connect(on_confirm)
    button_layout.addWidget(confirm_btn)
    
    layout.addLayout(button_layout)
    
    dialog.exec()
    return result[0]
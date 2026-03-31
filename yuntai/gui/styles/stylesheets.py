"""
stylesheets.py - 样式表函数与对话框辅助函数
============================================

定义所有 get_*_stylesheet() 函数以及通用对话框函数。

主要函数:
    - get_main_stylesheet: 获取主样式表
    - get_overlay_stylesheet: 获取遮罩层样式表
    - get_dialog_stylesheet: 获取弹窗样式表
    - get_dialog_button_stylesheet: 获取弹窗按钮样式表
    - get_dialog_card_stylesheet: 获取弹窗内卡片样式表
    - get_dialog_textedit_stylesheet: 获取弹窗内文本框样式表
    - get_dialog_list_stylesheet: 获取弹窗内列表样式表
    - get_dialog_tree_stylesheet: 获取弹窗内树形列表样式表
    - get_dialog_combobox_stylesheet: 获取弹窗内下拉框样式表
    - get_dialog_checkbox_stylesheet: 获取弹窗内复选框样式表
    - show_warning_dialog: 显示警告对话框
    - show_confirm_dialog: 显示确认对话框
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

from .colors import ThemeColors
from .fonts import ThemeFonts
from .dimensions import ThemeCorner, DialogStyle


# 样式表定义
def get_main_stylesheet(colors=ThemeColors):
    """
    获取主样式表

    生成应用程序的主样式表，包含所有UI组件的样式定义。

    Args:
        colors: 颜色主题类，默认为ThemeColors

    Returns:
        str: CSS样式表字符串
    """
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

"""
ToastWidget - Toast提示组件
============================

底部居中弹出的圆角矩形卡片，提供短暂显示的消息提示功能。

支持不同消息类型（info、success、warning、error），
具有显示/隐藏动画效果，自动定时隐藏。
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint

from yuntai.gui.styles import ThemeColors, DarkThemeColors, ThemeFonts


class ToastWidget(QFrame):
    """
    Toast提示组件 - 底部居中弹出的圆角矩形卡片

    提供短暂显示的消息提示功能，支持不同消息类型（info、success、warning、error）。
    具有显示/隐藏动画效果，自动定时隐藏。

    Attributes:
        is_dark_theme: 是否使用深色主题
        hide_timer: 自动隐藏定时器
        _pending_messages: 待显示消息队列
        _is_showing: 是否正在显示消息
    """

    def __init__(self, parent=None):
        """
        初始化Toast组件

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.is_dark_theme = False
        self._setup_ui()
        self._setup_animation()

        # 自动隐藏定时器
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._start_hide_animation)

        # 当前消息队列
        self._pending_messages = []
        self._is_showing = False

    def _setup_ui(self):
        """设置UI"""
        self.setObjectName("toastWidget")
        self.setFixedHeight(48)
        self.setMinimumWidth(200)
        self.setMaximumWidth(500)

        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # 消息标签
        self.message_label = QLabel()
        self.message_label.setFont(ThemeFonts.BODY_SMALL)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        # 初始隐藏
        self.hide()

    def _setup_animation(self):
        """设置动画"""
        # 显示动画
        self.show_animation = QPropertyAnimation(self, b"pos")
        self.show_animation.setDuration(200)
        self.show_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 隐藏动画
        self.hide_animation = QPropertyAnimation(self, b"pos")
        self.hide_animation.setDuration(200)
        self.hide_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.hide_animation.finished.connect(self._on_hide_finished)

    def _update_style(self, msg_type: str = "info"):
        """更新样式"""
        colors = DarkThemeColors if self.is_dark_theme else ThemeColors

        # 根据消息类型设置颜色
        type_colors = {
            "info": colors.TEXT_SECONDARY,
            "success": colors.STATUS_ACTIVE,
            "warning": colors.WARNING,
            "error": colors.DANGER
        }
        text_color = type_colors.get(msg_type, colors.TEXT_SECONDARY)

        # 根据主题设置不同的背景色，增加与背景的区分度
        if self.is_dark_theme:
            # 深色主题：使用更深的卡片背景
            bg_color = "#2D3748"  # 比BG_CARD更深
            border_color = "#4B5563"  # 更明显的边框
        else:
            # 浅色主题：使用稍深的背景色
            bg_color = "#F8F7F5"  # 比BG_MAIN稍深
            border_color = "#D0CDC7"  # 更明显的边框

        # 设置样式 - 添加阴影效果
        self.setStyleSheet(f"""
            QFrame#toastWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        self.message_label.setStyleSheet(f"color: {text_color}; background: transparent;")

    def show_toast(self, message: str, msg_type: str = "info", duration: int = 2000):
        """显示Toast消息"""
        # 如果正在显示，立即隐藏并显示新消息
        if self._is_showing:
            self.hide_timer.stop()
            self._force_hide_and_show_new(message, msg_type, duration)
            return

        self._show_message(message, msg_type, duration)

    def _force_hide_and_show_new(self, message: str, msg_type: str, duration: int):
        """强制隐藏当前toast并显示新消息"""
        # 立即隐藏
        self.hide()
        self._is_showing = False

        # 显示新消息
        self._show_message(message, msg_type, duration)

    def _show_message(self, message: str, msg_type: str, duration: int):
        """显示消息"""
        self._is_showing = True

        # 更新内容和样式
        self.message_label.setText(message)
        self._update_style(msg_type)

        # 调整大小
        self.adjustSize()

        # 计算位置（底部居中）
        parent = self.parent()
        if parent:
            parent_rect = parent.rect()
            toast_width = self.width()
            toast_height = self.height()

            # 底部居中，留出底部边距
            margin_bottom = 80
            x = (parent_rect.width() - toast_width) // 2
            y = parent_rect.height() - toast_height - margin_bottom

            # 起始位置（从底部下方开始）
            start_y = parent_rect.height() + 10
            end_y = y

            # 设置位置
            self.move(x, start_y)
            self.show()

            # 启动显示动画
            self.show_animation.setStartValue(QPoint(x, start_y))
            self.show_animation.setEndValue(QPoint(x, end_y))
            self.show_animation.start()

        # 设置自动隐藏定时器
        self.hide_timer.start(duration)

    def _start_hide_animation(self):
        """开始隐藏动画"""
        parent = self.parent()
        if parent:
            parent_rect = parent.rect()
            toast_width = self.width()
            toast_height = self.height()

            x = (parent_rect.width() - toast_width) // 2
            start_y = self.y()
            end_y = parent_rect.height() + 10

            self.hide_animation.setStartValue(QPoint(x, start_y))
            self.hide_animation.setEndValue(QPoint(x, end_y))
            self.hide_animation.start()

    def _on_hide_finished(self):
        """隐藏动画完成"""
        self.hide()
        self._is_showing = False

    def update_theme(self, is_dark_theme: bool):
        """更新主题"""
        self.is_dark_theme = is_dark_theme

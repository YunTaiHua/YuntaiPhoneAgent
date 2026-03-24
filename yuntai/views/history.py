"""
HistoryBuilder - 历史记录页面构建器（PyQt6 重构版）
浅色米白色主题版本
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QFont

from yuntai.gui.styles import ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing

if TYPE_CHECKING:
    from yuntai.gui.gui_view import GUIView


class HistoryBuilder:
    """历史记录页面构建器"""

    def __init__(self, view_instance: GUIView) -> None:
        self.view: GUIView = view_instance
        self.components: dict[str, Any] = view_instance.components
    
    @property
    def colors(self) -> ThemeColors:
        """动态获取当前主题颜色"""
        return self.view.colors

    def create_page(self) -> None:
        """创建历史记录页面（只执行一次）"""
        self.view._highlight_nav_button(3)

        page = self.view.content_pages[3]
        
        if page.layout() is not None:
            return
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(30, 30, 30, 30)
        page_layout.setSpacing(0)

        header_card = self._create_card(corner_radius=ThemeCorner.LG)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(8)

        title_label = QLabel("历史记录")
        title_label.setFont(ThemeFonts.TITLE_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("查看和管理对话历史记录")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        page_layout.addWidget(header_card)
        page_layout.addSpacing(20)

        history_frame = self._create_card()
        history_layout = QVBoxLayout(history_frame)
        history_layout.setContentsMargins(20, 15, 20, 20)
        history_layout.setSpacing(0)

        title_button_frame = QFrame()
        title_button_frame.setStyleSheet("background: transparent; border: none;")
        title_button_layout = QHBoxLayout(title_button_frame)
        title_button_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("📋 历史记录列表")
        title_label.setFont(ThemeFonts.BODY_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_button_layout.addWidget(title_label)
        title_button_layout.addStretch()

        self.components["refresh_history_btn"] = QPushButton("🔄 刷新")
        self.components["refresh_history_btn"].setFont(ThemeFonts.BODY_MEDIUM)
        self.components["refresh_history_btn"].setFixedSize(100, 36)
        self.components["refresh_history_btn"].setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.components["refresh_history_btn"].setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors.SECONDARY};
                color: {self.colors.TEXT_LIGHT};
                border: none;
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {self.colors.SECONDARY_HOVER};
            }}
        """)
        title_button_layout.addWidget(self.components["refresh_history_btn"])
        title_button_layout.addSpacing(10)

        self.components["clear_history_btn"] = QPushButton("🗑️ 清空")
        self.components["clear_history_btn"].setFont(ThemeFonts.BODY_MEDIUM)
        self.components["clear_history_btn"].setFixedSize(100, 36)
        self.components["clear_history_btn"].setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.components["clear_history_btn"].setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors.DANGER};
                color: {self.colors.TEXT_LIGHT};
                border: none;
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {self.colors.DANGER_HOVER};
            }}
        """)
        title_button_layout.addWidget(self.components["clear_history_btn"])

        history_layout.addWidget(title_button_frame)
        history_layout.addSpacing(15)

        self.components["history_text"] = QTextEdit()
        self.components["history_text"].setFont(ThemeFonts.CODE_MEDIUM)
        self.components["history_text"].setReadOnly(True)
        self.components["history_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        history_layout.addWidget(self.components["history_text"], 1)

        page_layout.addWidget(history_frame, 1)

    def _create_card(self, corner_radius: int = ThemeCorner.MD, shadow_type: str = 'md') -> QFrame:
        """创建卡片样式的Frame"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {corner_radius}px;
            }}
        """)
        self.view._apply_shadow(card, shadow_type)
        return card

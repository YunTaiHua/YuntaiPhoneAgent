"""
SettingsBuilder - 系统设置页面构建器（PyQt6 重构版）
浅色米白色主题版本
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont, QEnterEvent

from yuntai.gui.styles import ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing


# 设置页面布局常量 - 避免魔法数字
class SettingsLayoutConstants:
    """设置页面布局常量"""
    # 卡片布局常量
    CARD_MIN_HEIGHT = 140          # 卡片最小高度
    CARD_MARGIN = 20               # 卡片内边距
    CARD_SPACING = 24              # 卡片间距
    
    # 字体常量
    CARD_ICON_SIZE = 32            # 图标字体大小
    CARD_TITLE_SIZE = 20           # 标题字体大小


class HoverCard(QFrame):
    """可悬浮变色的卡片"""
    
    # 点击信号（无参数，兼容QPushButton的clicked信号）
    clicked = pyqtSignal()
    
    def __init__(self, card_index, hover_color, colors_getter, parent=None):
        super().__init__(parent)
        self.card_index = card_index
        self.hover_color = hover_color
        self._colors_getter = colors_getter  # 使用函数来动态获取颜色
        self.normal_style = ""
        self.hover_style = ""
        self._is_hoverable = True
        self._title_label = None
    
    @property
    def colors(self):
        """动态获取当前主题颜色"""
        return self._colors_getter()
    
    def set_styles(self, normal_style, hover_style):
        """设置正常和悬浮样式"""
        self.normal_style = normal_style
        self.hover_style = hover_style
        self.setStyleSheet(normal_style)
        
    def set_title_label(self, label):
        """设置标题标签引用"""
        self._title_label = label
        
    def set_hoverable(self, enabled):
        """设置是否可悬浮"""
        self._is_hoverable = enabled
        
    def enterEvent(self, event):
        """鼠标进入事件"""
        if self._is_hoverable:
            self.setStyleSheet(self.hover_style)
            if self._title_label:
                self._title_label.setStyleSheet(f"color: {self.colors.TEXT_LIGHT}; background: transparent; border: none;")
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self._is_hoverable:
            self.setStyleSheet(self.normal_style)
            if self._title_label:
                self._title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SettingsBuilder:
    """系统设置页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components
    
    @property
    def colors(self):
        """动态获取当前主题颜色"""
        return self.view.colors

    def create_page(self):
        """创建系统设置页面（只执行一次）"""
        self.view._highlight_nav_button(5)

        # 获取页面容器
        page = self.view.content_pages[5]
        
        # 检查是否已有布局，如果有则直接返回（页面已创建）
        if page.layout() is not None:
            return
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(30, 30, 30, 30)
        page_layout.setSpacing(0)

        # 标题卡片 - 居中对齐
        header_card = self._create_card(corner_radius=ThemeCorner.LG)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(8)

        title_label = QLabel("系统设置")
        title_label.setFont(ThemeFonts.TITLE_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("配置系统各项参数")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        page_layout.addWidget(header_card)
        page_layout.addSpacing(20)

        # 创建设置卡片容器
        settings_grid = QFrame()
        settings_grid.setStyleSheet("background: transparent; border: none;")
        grid_layout = QGridLayout(settings_grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(SettingsLayoutConstants.CARD_SPACING)

        # 设置选项
        settings = [
            ("连接配置", "🔗", self.colors.PRIMARY),
            ("系统检查", "🔍", self.colors.SUCCESS),
            ("TTS语音", "🎤", self.colors.SECONDARY),
            ("文件管理", "📁", self.colors.ACCENT),
        ]

        # 创建2x2网格
        for i, (title, icon, color) in enumerate(settings):
            row = i // 2
            col = i % 2

            # 创建可悬浮的卡片
            card = HoverCard(i, color, lambda: self.colors)
            card.setMinimumHeight(SettingsLayoutConstants.CARD_MIN_HEIGHT)
            
            # 设置正常和悬浮样式
            normal_style = f"""
                QFrame {{
                    background-color: {self.colors.BG_CARD};
                    border: 2px solid {self.colors.BORDER_LIGHT};
                    border-radius: {ThemeCorner.LG}px;
                }}
            """
            hover_style = f"""
                QFrame {{
                    background-color: {color};
                    border: 2px solid {color};
                    border-radius: {ThemeCorner.LG}px;
                }}
            """
            card.set_styles(normal_style, hover_style)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(
                SettingsLayoutConstants.CARD_MARGIN, 
                SettingsLayoutConstants.CARD_MARGIN, 
                SettingsLayoutConstants.CARD_MARGIN, 
                SettingsLayoutConstants.CARD_MARGIN
            )
            card_layout.setSpacing(12)

            # 图标标签
            icon_label = QLabel(icon)
            icon_label.setFont(QFont(ThemeFonts.FONT_FAMILY, SettingsLayoutConstants.CARD_ICON_SIZE))
            icon_label.setStyleSheet("background: transparent; border: none;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(icon_label)

            # 标题标签
            title_label = QLabel(title)
            title_label.setFont(QFont(ThemeFonts.FONT_FAMILY, SettingsLayoutConstants.CARD_TITLE_SIZE, QFont.Weight.Bold))
            title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(title_label)
            
            # 设置标题标签引用
            card.set_title_label(title_label)
            
            card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            
            # 连接点击信号
            card.clicked.connect(self._on_card_clicked)
            
            # 注册为settings_btn_X，以便handler能正确绑定事件
            self.components[f"settings_btn_{i}"] = card
            self.components[f"settings_card_{i}"] = card

            grid_layout.addWidget(card, row, col)

        # 配置网格权重
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)

        page_layout.addWidget(settings_grid, 1)

    def _on_card_clicked(self):
        """卡片点击事件 - 由handler通过信号绑定处理"""
        pass

    def _create_card(self, corner_radius=ThemeCorner.MD):
        """创建卡片样式的Frame"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {corner_radius}px;
            }}
        """)
        return card

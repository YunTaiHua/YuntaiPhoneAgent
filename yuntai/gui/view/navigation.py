"""
NavigationMixin - 导航面板混入类
=================================

提供左侧导航栏、主内容区、状态栏的创建和导航按钮管理功能。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from yuntai.core.config import APP_VERSION
from yuntai.gui.styles import ThemeCorner, ThemeFonts


class NavigationMixin:
    """
    导航面板混入类

    提供导航栏、主内容区、状态栏的创建和导航按钮高亮管理。

    要求宿主类具有以下属性:
        - colors: ThemeColors or DarkThemeColors
        - components: dict
    """

    def _setup_main_layout(self):
        """设置主布局"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建内容区域（导航栏 + 主内容）
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 创建导航栏
        self._create_navigation_frame()
        content_layout.addWidget(self.nav_frame)

        # 创建主内容区
        self._create_main_content_frame()
        content_layout.addWidget(self.main_container, 1)

        main_layout.addLayout(content_layout, 1)

        # 创建状态栏
        self._create_status_bar()
        main_layout.addWidget(self.status_bar)

    def _create_navigation_frame(self):
        """创建左侧导航栏 - 现代化米白色风格"""
        self.nav_frame = QFrame()
        self.nav_frame.setObjectName("navFrame")
        self.nav_frame.setFixedWidth(240)
        self.nav_frame.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        # 设置样式
        self.nav_frame.setStyleSheet(f"""
            QFrame#navFrame {{
                background-color: {self.colors.BG_NAV};
                border: none;
            }}
        """)

        # 导航栏布局
        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(20, 30, 20, 20)
        nav_layout.setSpacing(0)

        # 应用标题
        title_frame = QFrame()
        title_frame.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        # Emoji图标
        emoji_label = QLabel("📱")
        emoji_label.setFont(ThemeFonts.EMOJI_LARGE)
        emoji_label.setStyleSheet(f"color: {self.colors.PRIMARY}; background: transparent;")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(emoji_label)

        # 标题
        title_label = QLabel("Phone Agent")
        title_label.setFont(ThemeFonts.TITLE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("智能移动助手")
        subtitle_label.setFont(ThemeFonts.BODY_XSMALL)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle_label)

        # 版本信息（移到智能移动助手下方并居中）
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setFont(ThemeFonts.BODY_MINI)
        version_label.setStyleSheet(f"color: {self.colors.TEXT_DISABLED}; background: transparent;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(version_label)

        nav_layout.addWidget(title_frame)
        nav_layout.addSpacing(20)

        # 导航项目
        nav_items = [
            ("🏠 控制中心", "show_dashboard"),
            ("📱 设备管理", "show_connection_panel"),
            ("🎤 TTS语音", "show_tts_panel"),
            ("📊 历史记录", "show_history_panel"),
            ("🎨 动态功能", "show_dynamic_panel"),
            ("⚙️ 系统设置", "show_settings_panel"),
        ]

        self.components["nav_buttons"] = []
        for text, _ in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setFont(ThemeFonts.BODY_MEDIUM)
            btn.setFixedHeight(44)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton#navButton {{
                    background-color: transparent;
                    color: {self.colors.TEXT_PRIMARY};
                    text-align: left;
                    padding: 0 15px;
                    border-radius: {ThemeCorner.MD}px;
                    border: none;
                    border-left: 3px solid transparent;
                }}
                QPushButton#navButton:hover {{
                    background-color: {self.colors.BG_HOVER};
                }}
            """)
            nav_layout.addWidget(btn)
            self.components["nav_buttons"].append(btn)

        nav_layout.addStretch()

        # 底部信息
        info_frame = QFrame()
        info_frame.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        # 连接状态指示器
        status_icons_frame = QFrame()
        status_icons_frame.setStyleSheet("background: transparent;")
        status_layout = QHBoxLayout(status_icons_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)

        self.components["connection_indicator"] = QLabel("● 未连接")
        self.components["connection_indicator"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["connection_indicator"].setStyleSheet(f"""
            color: {self.colors.STATUS_INACTIVE};
            background: transparent;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        status_layout.addWidget(self.components["connection_indicator"])
        status_layout.addStretch()

        info_layout.addWidget(status_icons_frame)

        # TTS状态指示器
        tts_frame = QFrame()
        tts_frame.setStyleSheet("background: transparent;")
        tts_layout = QHBoxLayout(tts_frame)
        tts_layout.setContentsMargins(0, 0, 0, 0)
        tts_layout.setSpacing(8)

        self.components["tts_indicator"] = QLabel("● TTS: 关闭")
        self.components["tts_indicator"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["tts_indicator"].setStyleSheet(f"""
            color: {self.colors.STATUS_INACTIVE};
            background: transparent;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        tts_layout.addWidget(self.components["tts_indicator"])
        tts_layout.addStretch()

        info_layout.addWidget(tts_frame)

        # 主题切换按钮
        self.components["theme_toggle_button"] = QPushButton("🌙")
        self.components["theme_toggle_button"].setFixedSize(32, 32)
        self.components["theme_toggle_button"].setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.components["theme_toggle_button"].setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors.BG_HOVER};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: 16px;
                font-size: 18px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {self.colors.BG_CARD_ALT};
            }}
        """)
        info_layout.addWidget(self.components["theme_toggle_button"])

        nav_layout.addWidget(info_frame)

    def _create_main_content_frame(self):
        """创建主内容容器 - 现代化米白色风格"""
        self.main_container = QFrame()
        self.main_container.setObjectName("contentFrame")
        self.main_container.setStyleSheet(f"""
            QFrame#contentFrame {{
                background-color: {self.colors.BG_MAIN};
                margin: 20px;
            }}
        """)

        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)

        # 创建卡片容器 - 带阴影效果的圆角卡片
        self.components["content_card"] = QFrame()
        self.components["content_card"].setObjectName("card")
        self.components["content_card"].setStyleSheet(f"""
            QFrame#card {{
                background-color: {self.colors.BG_CARD};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)

        card_layout = QVBoxLayout(self.components["content_card"])
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 创建页面堆栈
        self.page_stack = QStackedWidget()
        card_layout.addWidget(self.page_stack)

        # 创建6个页面容器
        self.content_pages = []
        for i in range(6):
            page_frame = QFrame()
            page_frame.setStyleSheet("background: transparent;")
            self.content_pages.append(page_frame)
            self.page_stack.addWidget(page_frame)

        main_layout.addWidget(self.components["content_card"])

    def _create_status_bar(self):
        """创建底部状态栏 - 现代化样式"""
        self.status_bar = QFrame()
        self.status_bar.setObjectName("statusBar")
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet(f"""
            QFrame#statusBar {{
                background-color: {self.colors.BG_NAV};
                border-top: 1px solid {self.colors.BORDER_LIGHT};
            }}
        """)

        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)
        status_layout.addStretch()

    def _highlight_nav_button(self, index):
        """高亮导航按钮 - 现代化样式"""
        colors = self.colors

        if "nav_buttons" in self.components:
            for i, btn in enumerate(self.components["nav_buttons"]):
                if i == index:
                    btn.setStyleSheet(f"""
                        QPushButton#navButton {{
                            background-color: {colors.NAV_HIGHLIGHT_BG};
                            color: {colors.PRIMARY};
                            text-align: left;
                            padding: 0 15px;
                            border-radius: {ThemeCorner.MD}px;
                            border: none;
                            border-left: 3px solid {colors.PRIMARY};
                        }}
                        QPushButton#navButton:hover {{
                            background-color: {colors.NAV_HIGHLIGHT_HOVER};
                        }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton#navButton {{
                            background-color: transparent;
                            color: {colors.TEXT_PRIMARY};
                            text-align: left;
                            padding: 0 15px;
                            border-radius: {ThemeCorner.MD}px;
                            border: none;
                            border-left: 3px solid transparent;
                        }}
                        QPushButton#navButton:hover {{
                            background-color: {colors.BG_HOVER};
                        }}
                    """)

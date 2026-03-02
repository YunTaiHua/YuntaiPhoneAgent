"""
GUIView - 纯界面构建模块（PyQt6 重构版）
负责所有UI组件的创建和布局，不包含业务逻辑
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QFileDialog,
    QScrollArea, QSizePolicy, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QCursor

# 从 yuntai.config 导入配置
from yuntai.core.config import APP_VERSION

# 从 yuntai.gui 导入样式
from yuntai.gui.styles import (
    ThemeColors, DarkThemeColors, ThemeFonts, ThemeCorner,
    ThemeSpacing, ThemeHeight, get_main_stylesheet, 
    get_overlay_stylesheet, apply_light_theme, apply_dark_theme
)


class GUIView(QMainWindow):
    """纯界面构建类，只负责UI创建"""

    def __init__(self):
        super().__init__()
        
        # 窗口设置
        self.setWindowTitle(f"Phone Agent - 智能移动助手 v{APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # 存储UI组件引用
        self.components = {}
        
        # 当前主题（False=浅色，True=深色）
        self.is_dark_theme = False
        
        # 当前页面索引
        self.current_page_index = -1  # 初始无页面
        
        # 页面初始化标志
        self.page_initialized = [False] * 6
        
        # 应用主题
        self._apply_theme()
        
        # 创建界面
        self._setup_main_layout()
        
        # 创建页面构建器（延迟导入避免循环依赖）
        from yuntai.views.pages import PageBuilder
        self.page_builder = PageBuilder(self)
        
    def _apply_theme(self):
        """应用主题"""
        app = QApplication.instance()
        if self.is_dark_theme:
            apply_dark_theme(app)
            self.colors = DarkThemeColors
        else:
            apply_light_theme(app)
            self.colors = ThemeColors
        
        # 应用样式表
        app.setStyleSheet(get_main_stylesheet(self.colors))
        
    def toggle_theme(self):
        """切换主题"""
        self.is_dark_theme = not self.is_dark_theme
        
        # 重置页面初始化标志，以便重新创建页面
        self.page_initialized = [False] * 6
        self.page_builder.page_initialized = [False] * 6
        
        # 清除所有页面的布局
        for page in self.content_pages:
            layout = page.layout()
            if layout is not None:
                # 删除布局中的所有控件
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                    elif item.layout():
                        self._clear_layout(item.layout())
                # 删除布局本身
                from PyQt6.QtWidgets import QWidget
                QWidget().setLayout(layout)
        
        # 清空组件字典中的页面相关组件（保留导航栏等全局组件）
        keys_to_keep = [
            "nav_frame", "nav_buttons", "content_card", "page_stack",
            "status_bar", "status_label", "tts_indicator", "theme_toggle_button",
            "tts_loading_overlay", "tts_loading_label"
        ]
        keys_to_remove = [k for k in list(self.components.keys()) if k not in keys_to_keep]
        for key in keys_to_remove:
            del self.components[key]
        
        # 应用新主题
        self._apply_theme()
        
        # 更新全局组件样式
        self._update_global_components_style()
        
        # 重新创建当前页面
        self.show_page(self.current_page_index)

    def _update_global_components_style(self):
        """更新全局组件的样式（主题切换时调用）"""
        colors = self.colors
        
        # 1. 更新导航栏样式
        if hasattr(self, 'nav_frame') and self.nav_frame:
            self.nav_frame.setStyleSheet(f"""
                QFrame#navFrame {{
                    background-color: {colors.BG_NAV};
                    border: none;
                }}
            """)
            
            # 更新导航栏内的标题和标签样式
            for child in self.nav_frame.findChildren(QLabel):
                child_style = child.styleSheet()
                # 更新颜色
                if "TEXT_PRIMARY" in child_style or "color:" in child_style:
                    if "📱" in child.text() or "Phone Agent" in child.text():
                        child.setStyleSheet(f"color: {colors.TEXT_PRIMARY if 'Phone Agent' in child.text() else colors.PRIMARY}; background: transparent;")
                    elif "智能移动助手" in child.text():
                        child.setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
                    elif "Version" in child.text():
                        child.setStyleSheet(f"color: {colors.TEXT_DISABLED}; background: transparent;")
            
            # 更新导航按钮样式
            if "nav_buttons" in self.components:
                for i, btn in enumerate(self.components["nav_buttons"]):
                    if i == self.current_page_index:
                        btn.setStyleSheet(f"""
                            QPushButton#navButton {{
                                background-color: {colors.NAV_HIGHLIGHT_BG};
                                color: {colors.PRIMARY};
                                text-align: left;
                                padding: 0 15px;
                                border-radius: {ThemeCorner.MD}px;
                                border: none;
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
                            }}
                            QPushButton#navButton:hover {{
                                background-color: {colors.BG_HOVER};
                            }}
                        """)
            
            # 更新连接状态指示器
            if "connection_indicator" in self.components:
                indicator = self.components["connection_indicator"]
                current_text = indicator.text()
                if "未连接" in current_text:
                    indicator.setStyleSheet(f"color: {colors.DANGER}; background: transparent;")
                else:
                    indicator.setStyleSheet(f"color: {colors.SUCCESS}; background: transparent;")
            
            # 更新TTS状态指示器
            if "tts_indicator" in self.components:
                tts_ind = self.components["tts_indicator"]
                current_text = tts_ind.text()
                if "关闭" in current_text:
                    tts_ind.setStyleSheet(f"color: {colors.WARNING}; background: transparent;")
                else:
                    tts_ind.setStyleSheet(f"color: {colors.SUCCESS}; background: transparent;")
            
            # 更新主题切换按钮
            if "theme_toggle_button" in self.components:
                theme_btn = self.components["theme_toggle_button"]
                theme_btn.setText("🌙" if not self.is_dark_theme else "☀️")
                theme_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {colors.BG_HOVER};
                        color: {colors.TEXT_PRIMARY};
                        border: 1px solid {colors.BORDER_LIGHT};
                        border-radius: 16px;
                        font-size: 18px;
                        padding: 0px;
                        margin: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: {colors.BG_CARD_ALT};
                    }}
                """)
        
        # 2. 更新主内容容器样式
        if hasattr(self, 'main_container') and self.main_container:
            self.main_container.setStyleSheet(f"""
                QFrame#contentFrame {{
                    background-color: {colors.BG_MAIN};
                    margin: 20px;
                }}
            """)
        
        # 3. 更新卡片容器样式
        if "content_card" in self.components:
            self.components["content_card"].setStyleSheet(f"""
                QFrame#card {{
                    background-color: {colors.BG_CARD};
                    border: 1px solid {colors.BORDER_LIGHT};
                    border-radius: {ThemeCorner.MD}px;
                }}
            """)
        
        # 4. 更新状态栏样式
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.setStyleSheet(f"""
                QFrame#statusBar {{
                    background-color: {colors.BG_NAV};
                    border-top: 1px solid {colors.BORDER_LIGHT};
                }}
            """)
            
            # 更新状态栏标签
            if "status_label" in self.components:
                self.components["status_label"].setStyleSheet(f"color: {colors.TEXT_SECONDARY}; background: transparent;")
        
        # 5. 更新遮罩层样式
        if hasattr(self, 'tts_loading_overlay') and self.tts_loading_overlay:
            # 根据主题设置遮罩层背景色
            overlay_bg = "rgba(26, 26, 46, 200)" if self.is_dark_theme else "rgba(253, 252, 250, 200)"
            self.tts_loading_overlay.setStyleSheet(f"""
                QFrame#overlayFrame {{
                    background-color: {overlay_bg};
                }}
            """)
            
            # 更新遮罩层内的卡片
            for child in self.tts_loading_overlay.findChildren(QFrame):
                if child.objectName() == "overlayCard":
                    child.setStyleSheet(f"""
                        QFrame#overlayCard {{
                            background-color: {colors.BG_CARD};
                            border: 1px solid {colors.BORDER_LIGHT};
                            border-radius: {ThemeCorner.LG}px;
                        }}
                    """)
            
            # 更新加载标签
            if "tts_loading_label" in self.components:
                self.components["tts_loading_label"].setStyleSheet(f"color: {colors.TEXT_PRIMARY}; background: transparent;")

    def _clear_layout(self, layout):
        """递归清除布局中的所有控件"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def _refresh_all_pages(self):
        """强制刷新所有页面"""
        # 重新应用全局样式表会自动更新所有控件
        app = QApplication.instance()
        app.setStyleSheet(get_main_stylesheet(self.colors))
        
        # 强制更新主窗口
        self.update()
        
        # 更新所有页面
        for page in self.content_pages:
            if page:
                page.update()
        
        # 更新导航栏
        if hasattr(self, 'nav_frame') and self.nav_frame:
            self.nav_frame.update()
        
        # 更新状态栏
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.update()
        
    def _apply_theme_to_all_pages(self):
        """应用主题到所有已初始化的页面"""
        for i in range(6):
            if self.page_initialized[i]:
                self.page_builder._apply_current_theme_to_page(i)
        
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
        
        # 创建TTS加载遮罩层
        self._create_tts_loading_overlay()
        
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
        self.components["connection_indicator"].setStyleSheet(f"color: {self.colors.DANGER}; background: transparent;")
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
        self.components["tts_indicator"].setStyleSheet(f"color: {self.colors.WARNING}; background: transparent;")
        tts_layout.addWidget(self.components["tts_indicator"])
        tts_layout.addStretch()
        
        info_layout.addWidget(tts_frame)
        
        # 版本信息
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setFont(ThemeFonts.BODY_MINI)
        version_label.setStyleSheet(f"color: {self.colors.TEXT_DISABLED}; background: transparent;")
        info_layout.addWidget(version_label)
        
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
        
        # 系统状态
        self.components["status_label"] = QLabel("系统已就绪")
        self.components["status_label"].setFont(ThemeFonts.BODY_TINY)
        self.components["status_label"].setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent;")
        status_layout.addWidget(self.components["status_label"])
        status_layout.addStretch()
        
    def _create_tts_loading_overlay(self):
        """创建TTS加载遮罩层"""
        self.tts_loading_overlay = QFrame(self)
        self.tts_loading_overlay.setObjectName("overlayFrame")
        self.tts_loading_overlay.setStyleSheet(f"""
            QFrame#overlayFrame {{
                background-color: rgba(245, 245, 245, 200);
            }}
        """)
        # 初始设置为窗口大小,后续会在show_tts_loading中更新
        self.tts_loading_overlay.setGeometry(0, 0, self.width(), self.height())
        self.tts_loading_overlay.hide()
        
        # 加载卡片
        loading_card = QFrame(self.tts_loading_overlay)
        loading_card.setObjectName("overlayCard")
        loading_card.setStyleSheet(f"""
            QFrame#overlayCard {{
                background-color: {self.colors.BG_CARD};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.LG}px;
            }}
        """)
        loading_card.setFixedSize(350, 150)
        
        # 居中显示
        loading_layout = QVBoxLayout(loading_card)
        loading_layout.setContentsMargins(30, 30, 30, 30)
        loading_layout.setSpacing(20)
        
        self.components["tts_loading_label"] = QLabel("正在加载TTS语音资源中...")
        self.components["tts_loading_label"].setFont(ThemeFonts.BODY_LARGE)
        self.components["tts_loading_label"].setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent;")
        self.components["tts_loading_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.components["tts_loading_label"])
        
        # 进度条
        from PyQt6.QtWidgets import QProgressBar
        self.components["tts_loading_progress"] = QProgressBar()
        self.components["tts_loading_progress"].setRange(0, 0)  # 不确定进度
        self.components["tts_loading_progress"].setFixedHeight(8)
        self.components["tts_loading_progress"].setTextVisible(False)
        loading_layout.addWidget(self.components["tts_loading_progress"])
        
        # 居中定位遮罩层中的卡片
        self.tts_loading_overlay.setLayout(QVBoxLayout())
        self.tts_loading_overlay.layout().addWidget(loading_card, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def show_tts_loading(self, message: str = "正在加载TTS语音资源中..."):
        """显示TTS加载遮罩"""
        if hasattr(self, 'tts_loading_overlay'):
            if "tts_loading_label" in self.components:
                self.components["tts_loading_label"].setText(message)
            # 更新遮罩层大小以覆盖整个窗口
            self.tts_loading_overlay.setGeometry(0, 0, self.width(), self.height())
            self.tts_loading_overlay.raise_()
            self.tts_loading_overlay.show()
            
    def hide_tts_loading(self):
        """隐藏TTS加载遮罩"""
        if hasattr(self, 'tts_loading_overlay'):
            self.tts_loading_overlay.hide()
    
    def show_enter_button(self):
        """显示模拟回车按钮"""
        enter_btn = self.components.get("enter_button")
        if enter_btn:
            enter_btn.show()
    
    def hide_enter_button(self):
        """隐藏模拟回车按钮"""
        enter_btn = self.components.get("enter_button")
        if enter_btn:
            enter_btn.hide()
            
    def resizeEvent(self, event):
        """窗口大小改变时调整遮罩层大小"""
        super().resizeEvent(event)
        if hasattr(self, 'tts_loading_overlay'):
            self.tts_loading_overlay.setGeometry(self.geometry())
            
    # ========== 页面创建方法（委托给PageBuilder）==========
    
    def show_page(self, page_index: int):
        """显示指定页面（使用堆栈容器）"""
        # 1. 显示目标页面
        if 0 <= page_index < 6:
            self.page_stack.setCurrentIndex(page_index)
            
        # 2. 更新当前页面索引
        self.current_page_index = page_index
        
        # 3. 高亮导航按钮
        self._highlight_nav_button(page_index)
        
        # 4. 调用页面的初始化回调（只执行一次）
        self._call_page_init_callback(page_index)
        
    def _call_page_init_callback(self, page_index: int):
        """调用页面的初始化回调（只执行一次）"""
        # 使用 page_builder 的 page_initialized 统一管理
        if self.page_builder.page_initialized[page_index]:
            return
            
        if page_index == 0:
            self.page_builder.create_dashboard_page()
        elif page_index == 1:
            self.page_builder.create_connection_page()
        elif page_index == 2:
            self.page_builder.create_tts_page(self.page_builder.tts_manager)
        elif page_index == 3:
            self.page_builder.create_history_page()
        elif page_index == 4:
            self.page_builder.create_dynamic_page()
        elif page_index == 5:
            self.page_builder.create_settings_page()
            
        # page_builder 内部会设置 page_initialized，这里不需要重复设置
        
    def create_dashboard_page(self):
        """创建控制中心页面（委托给show_page）"""
        self.show_page(0)
        
    def create_connection_page(self):
        """创建设备管理页面（委托给show_page）"""
        self.show_page(1)
        
    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面（委托给show_page）"""
        # 保存 tts_manager 供 page_builder 使用
        self.page_builder.tts_manager = tts_manager
        self.show_page(2)
        
    def create_history_page(self):
        """创建历史记录页面（委托给show_page）"""
        self.show_page(3)
        
    def create_dynamic_page(self):
        """创建动态功能页面（委托给show_page）"""
        self.show_page(4)
        
    def create_settings_page(self):
        """创建系统设置页面（委托给show_page）"""
        self.show_page(5)
        
    # ========== 辅助方法 ==========
    
    def show_file_upload_dialog(self) -> list[str]:
        """显示文件上传对话框并返回选择的文件路径列表"""
        # PyQt6 的文件过滤器格式: "名称 (*.ext1 *.ext2);;名称2 (*.ext3)"
        filetypes = [
            ("所有支持的文件", "*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.avi *.mov *.mkv *.wmv *.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma *.txt *.py *.csv *.xls *.xlsx *.docx *.pdf *.ppt *.pptx *.html *.js *.htm *.rss *.atom *.json *.xml *.java *.ipynb"),
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"),
            ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv"),
            ("音频文件", "*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma"),
            ("文档文件", "*.txt *.py *.csv *.xls *.xlsx *.docx *.pdf *.ppt *.pptx *.html *.js *.htm *.rss *.atom *.json *.xml *.java *.ipynb"),
            ("所有文件", "*.*")
        ]
        
        # 构建 PyQt6 格式的过滤器字符串
        filter_str = ";;".join([f"{name} ({pattern})" for name, pattern in filetypes])
        
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择要上传的文件",
            "",
            filter_str
        )
        
        return list(files)
        
    def show_attached_files(self, file_paths: list[str], controller=None):
        """在UI中显示已选择的文件"""
        # 获取文件列表滚动框架
        files_scroll_frame = self.get_component("files_list_scroll_frame")
        if not files_scroll_frame:
            print("⚠️  未找到files_list_scroll_frame组件")
            return
            
        # 清空现有文件显示
        layout = files_scroll_frame.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
        if not file_paths:
            return
            
        # 显示每个文件
        for i, file_path in enumerate(file_paths):
            file_frame = QFrame()
            file_frame.setFixedHeight(32)  # 固定高度,更紧凑
            file_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.colors.BG_HOVER};
                    border-radius: {ThemeCorner.SM}px;
                    margin: 1px 0;
                }}
            """)
            file_layout = QHBoxLayout(file_frame)
            file_layout.setContentsMargins(8, 4, 8, 4)
            file_layout.setSpacing(6)
            
            # 文件名（带图标）
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower()
            
            # 根据文件类型选择图标
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                icon = "🖼️"
            elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
                icon = "🎬"
            elif ext in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']:
                icon = "🎵"
            elif ext == '.txt':
                icon = "📄"
            else:
                icon = "📎"
                
            file_label = QLabel(f"{icon} {file_name}")
            file_label.setFont(ThemeFonts.BODY_XSMALL)
            file_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent;")
            # 设置文本省略模式,防止文件名太长溢出
            file_label.setWordWrap(False)
            file_label.setTextFormat(Qt.TextFormat.PlainText)
            # 限制最大宽度,超出部分显示省略号
            file_label.setMaximumWidth(180)
            file_label.setToolTip(file_name)  # 鼠标悬停显示完整文件名
            file_layout.addWidget(file_label, 1)
            
            # 删除按钮（仅在controller存在时显示）
            if controller:
                delete_btn = QPushButton("×")
                delete_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
                delete_btn.setFixedSize(24, 24)
                delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                delete_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.colors.DANGER};
                        color: white;
                        border: none;
                        border-radius: 12px;
                        padding: 0px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.colors.DANGER_HOVER};
                    }}
                """)
                delete_btn.clicked.connect(lambda checked, f=file_path, c=controller: c.remove_attached_file(f))
                file_layout.addWidget(delete_btn)
                
            layout.addWidget(file_frame)
            
        # 添加stretch在最后，让文件顶格显示
        layout.addStretch(1)
        
        # 清空所有按钮（仅在controller存在时显示）
        if controller and file_paths:
            clear_all_btn = QPushButton("清空所有")
            clear_all_btn.setFont(ThemeFonts.BODY_XSMALL)
            clear_all_btn.setFixedHeight(30)
            clear_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            clear_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.colors.WARNING};
                    color: {self.colors.TEXT_LIGHT};
                    border: none;
                    border-radius: 15px;
                    padding: 0 15px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.WARNING_HOVER};
                }}
            """)
            clear_all_btn.clicked.connect(controller.clear_attached_files)
            layout.addWidget(clear_all_btn, alignment=Qt.AlignmentFlag.AlignRight)
            
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
                        }}
                        QPushButton#navButton:hover {{
                            background-color: {colors.BG_HOVER};
                        }}
                    """)
                    
    def _on_device_type_change(self, device_type: str):
        """设备类型改变时的回调"""
        if hasattr(self, '_device_type_callback'):
            self._device_type_callback(device_type)
            
    def get_component(self, name):
        """获取UI组件"""
        return self.components.get(name)
        
    def update_component(self, name, **kwargs):
        """更新UI组件属性"""
        if name in self.components:
            component = self.components[name]
            for key, value in kwargs.items():
                if hasattr(component, key):
                    try:
                        setattr(component, key, value)
                    except:
                        # 对于某些属性需要使用特定方法
                        if hasattr(component, 'setText') and key == 'text':
                            component.setText(value)
                        elif hasattr(component, 'setStyleSheet') and key == 'style':
                            component.setStyleSheet(value)
                            
    def show_enter_button(self):
        """显示模拟回车按钮"""
        enter_btn = self.components.get("enter_button")
        if enter_btn:
            enter_btn.show()
            
    def hide_enter_button(self):
        """隐藏模拟回车按钮"""
        enter_btn = self.components.get("enter_button")
        if enter_btn:
            enter_btn.hide()

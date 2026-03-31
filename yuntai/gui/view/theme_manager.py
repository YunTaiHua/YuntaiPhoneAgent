"""
ThemeManagerMixin - 主题管理混入类
===================================

提供主题应用、切换和全局组件样式更新功能。
支持浅色/深色主题切换。
"""

import logging

from PyQt6.QtWidgets import QApplication, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

from yuntai.gui.styles import (
    ThemeColors, DarkThemeColors, ThemeCorner,
    ThemeShadow, get_main_stylesheet,
    apply_light_theme, apply_dark_theme
)

# 初始化模块日志记录器
logger = logging.getLogger(__name__)


class ThemeManagerMixin:
    """
    主题管理混入类

    提供主题应用、切换和全局组件样式更新功能。
    需要与其它混入类一起使用在GUIView中。

    要求宿主类具有以下属性:
        - is_dark_theme: bool
        - colors: ThemeColors or DarkThemeColors
        - page_initialized: list[bool]
        - page_builder: PageBuilder实例
        - components: dict
        - content_pages: list
        - current_page_index: int
    """

    def _apply_theme(self):
        """
        应用主题

        根据当前主题设置应用全局样式表和颜色。
        浅色主题使用ThemeColors，深色主题使用DarkThemeColors。
        """
        app = QApplication.instance()
        if self.is_dark_theme:
            apply_dark_theme(app)
            self.colors = DarkThemeColors
        else:
            apply_light_theme(app)
            self.colors = ThemeColors

        # 应用样式表
        app.setStyleSheet(get_main_stylesheet(self.colors))

    def _apply_shadow(self, widget, shadow_type='md'):
        """为控件应用阴影效果

        Args:
            widget: 要应用阴影的控件
            shadow_type: 阴影类型 ('sm', 'md', 'lg')
        """
        # 根据主题选择阴影配置
        if self.is_dark_theme:
            shadow_map = {
                'sm': ThemeShadow.DARK_SM,
                'md': ThemeShadow.DARK_MD,
                'lg': ThemeShadow.DARK_LG
            }
        else:
            shadow_map = {
                'sm': ThemeShadow.LIGHT_SM,
                'md': ThemeShadow.LIGHT_MD,
                'lg': ThemeShadow.LIGHT_LG
            }

        shadow_config = shadow_map.get(shadow_type, ThemeShadow.LIGHT_MD)
        x_offset, y_offset, blur_radius, color_rgba = shadow_config

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setOffset(x_offset, y_offset)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(*color_rgba))

        widget.setGraphicsEffect(shadow)

    def toggle_theme(self):
        """
        切换主题

        在浅色和深色主题之间切换，重新创建所有页面组件。
        切换时会清除当前页面的所有组件并重新初始化。
        """
        self.is_dark_theme = not self.is_dark_theme
        logger.info("主题切换: %s", '深色' if self.is_dark_theme else '浅色')

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
            "status_bar", "tts_indicator", "theme_toggle_button",
            "tts_loading_overlay", "tts_loading_label"
        ]
        keys_to_remove = [k for k in list(self.components.keys()) if k not in keys_to_keep]
        for key in keys_to_remove:
            del self.components[key]

        # 应用新主题
        self._apply_theme()

        # 更新Toast主题
        if hasattr(self, 'toast_widget'):
            self.toast_widget.update_theme(self.is_dark_theme)

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

            # 更新连接状态指示器
            if "connection_indicator" in self.components:
                indicator = self.components["connection_indicator"]
                current_text = indicator.text()
                if "未连接" in current_text:
                    indicator.setStyleSheet(f"""
                        color: {colors.STATUS_INACTIVE};
                        background: transparent;
                        padding: 4px 8px;
                        border-radius: 4px;
                    """)
                else:
                    indicator.setStyleSheet(f"""
                        color: {colors.STATUS_ACTIVE};
                        background: transparent;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: 500;
                    """)

            # 更新TTS状态指示器
            if "tts_indicator" in self.components:
                tts_ind = self.components["tts_indicator"]
                current_text = tts_ind.text()
                if "关闭" in current_text:
                    tts_ind.setStyleSheet(f"""
                        color: {colors.STATUS_INACTIVE};
                        background: transparent;
                        padding: 4px 8px;
                        border-radius: 4px;
                    """)
                else:
                    tts_ind.setStyleSheet(f"""
                        color: {colors.STATUS_ACTIVE};
                        background: transparent;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-weight: 500;
                    """)

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

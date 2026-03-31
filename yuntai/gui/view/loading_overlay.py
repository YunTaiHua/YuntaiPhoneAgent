"""
LoadingOverlayMixin - 加载遮罩层混入类
========================================

提供TTS加载遮罩层的创建、显示和隐藏功能。
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize

from yuntai.gui.styles import ThemeCorner, ThemeFonts


class LoadingOverlayMixin:
    """
    加载遮罩层混入类

    提供TTS加载遮罩层的创建、显示和隐藏功能。

    要求宿主类具有以下属性:
        - colors: ThemeColors or DarkThemeColors
        - components: dict
        - is_dark_theme: bool
    """

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
            # 禁止窗口最大化
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMaximized)
            # 保存当前窗口状态并禁止最大化按钮
            self._saved_maximizable = self.maximumSize().isNull() or self.maximumSize() == QSize(16777215, 16777215)
            self.setFixedSize(self.size())

    def hide_tts_loading(self):
        """隐藏TTS加载遮罩"""
        if hasattr(self, 'tts_loading_overlay'):
            self.tts_loading_overlay.hide()
            # 恢复窗口大小调整功能
            self.setMinimumSize(1200, 700)
            self.setMaximumSize(QSize(16777215, 16777215))  # 恢复默认最大尺寸

    def resizeEvent(self, event):
        """窗口大小改变时调整遮罩层大小"""
        super().resizeEvent(event)
        if hasattr(self, 'tts_loading_overlay'):
            self.tts_loading_overlay.setGeometry(self.geometry())

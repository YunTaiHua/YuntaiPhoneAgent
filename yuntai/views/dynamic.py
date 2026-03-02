"""
DynamicBuilder - 动态功能页面构建器（PyQt6 重构版）
浅色米白色主题版本 - 左右分栏布局
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTextEdit, QLineEdit,
    QComboBox, QCheckBox, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QFont

from yuntai.gui.styles import ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing


# 动态页面布局常量 - 避免魔法数字
class DynamicLayoutConstants:
    """动态页面布局常量"""
    # 左侧区域布局常量
    LEFT_MARGIN = 20            # 左侧区域内边距
    LEFT_SPACING = 8            # 左侧元素间距（减小）
    
    # 描述框常量
    PROMPT_MIN_HEIGHT = 80      # 描述框最小高度
    
    # 参数框架常量
    PARAMS_MARGIN = 15          # 参数框架内边距
    PARAMS_SPACING = 12         # 参数元素间距
    
    # 按钮区域常量
    BUTTON_TOP_MARGIN = 8       # 按钮区域顶部边距（减小）
    BUTTON_SPACING = 12         # 按钮间距


class DynamicBuilder:
    """动态功能页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components
    
    @property
    def colors(self):
        """动态获取当前主题颜色"""
        return self.view.colors

    def create_page(self):
        """创建动态功能页面（只执行一次）"""
        self.view._highlight_nav_button(4)

        # 获取页面容器
        page = self.view.content_pages[4]
        
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

        title_label = QLabel("动态功能")
        title_label.setFont(ThemeFonts.TITLE_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("图像生成与视频合成")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        page_layout.addWidget(header_card)
        page_layout.addSpacing(20)

        # 创建选项卡
        self.components["dynamic_tabview"] = QTabWidget()
        self.components["dynamic_tabview"].setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                background-color: {self.colors.BG_CARD};
            }}
            QTabBar {{
                alignment: center;
            }}
            QTabBar::tab {{
                font-family: "{ThemeFonts.FONT_FAMILY}";
                font-size: 13px;
                padding: 10px 20px;
                background-color: {self.colors.BG_CARD_ALT};
                border-top-left-radius: {ThemeCorner.SM}px;
                border-top-right-radius: {ThemeCorner.SM}px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.colors.PRIMARY};
                color: {self.colors.TEXT_LIGHT};
            }}
            QTabBar::tab:hover {{
                background-color: {self.colors.BG_HOVER};
            }}
        """)

        # 创建图像生成选项卡
        image_tab = QWidget()
        self._create_image_generation_tab(image_tab)
        self.components["dynamic_tabview"].addTab(image_tab, "🖼️ 图像生成")
        self.components["image_tab"] = image_tab

        # 创建视频生成选项卡
        video_tab = QWidget()
        self._create_video_generation_tab(video_tab)
        self.components["dynamic_tabview"].addTab(video_tab, "🎬 视频生成")
        self.components["video_tab"] = video_tab

        page_layout.addWidget(self.components["dynamic_tabview"], 1)

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

    def _create_button(self, text: str, style_type: str, height: int = 40) -> QPushButton:
        """创建按钮"""
        btn = QPushButton(text)
        btn.setFont(ThemeFonts.BODY_MEDIUM)
        btn.setFixedHeight(height)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        colors_map = {
            "primary": (self.colors.PRIMARY, self.colors.PRIMARY_HOVER),
            "secondary": (self.colors.SECONDARY, self.colors.SECONDARY_HOVER),
            "danger": (self.colors.DANGER, self.colors.DANGER_HOVER),
            "success": (self.colors.SUCCESS, self.colors.SUCCESS_HOVER),
            "warning": (self.colors.WARNING, self.colors.WARNING_HOVER),
            "accent": (self.colors.ACCENT, self.colors.ACCENT_HOVER),
        }

        bg_color, hover_color = colors_map.get(style_type, (self.colors.PRIMARY, self.colors.PRIMARY_HOVER))

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {self.colors.TEXT_LIGHT};
                border: none;
                border-radius: 20px;
                padding: 0 15px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)

        return btn

    def _create_combobox(self, items: list, width: int = 150, height: int = 38) -> QComboBox:
        """创建下拉框"""
        combo = QComboBox()
        combo.addItems(items)
        combo.setFont(ThemeFonts.BODY_XSMALL)
        combo.setFixedSize(width, height)
        combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.colors.BG_INPUT};
                color: {self.colors.TEXT_PRIMARY};
                border: none;
                border-radius: {ThemeCorner.MD}px;
                padding: 0 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self.colors.TEXT_SECONDARY};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.colors.BG_CARD};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                selection-background-color: {self.colors.PRIMARY};
                selection-color: {self.colors.TEXT_LIGHT};
            }}
        """)
        return combo

    def _create_image_generation_tab(self, parent):
        """创建图像生成选项卡 - 左右分栏布局"""
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 左侧：描述输入和参数设置
        left_frame = self._create_card()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(
            DynamicLayoutConstants.LEFT_MARGIN, 
            DynamicLayoutConstants.LEFT_MARGIN, 
            DynamicLayoutConstants.LEFT_MARGIN, 
            DynamicLayoutConstants.LEFT_MARGIN
        )
        left_layout.setSpacing(DynamicLayoutConstants.LEFT_SPACING)

        # 提示词输入
        prompt_label = QLabel("📝 图像描述")
        prompt_label.setFont(ThemeFonts.BODY_LARGE)
        prompt_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        left_layout.addWidget(prompt_label)

        self.components["image_prompt_text"] = QTextEdit()
        self.components["image_prompt_text"].setFont(ThemeFonts.BODY_SMALL)
        self.components["image_prompt_text"].setMinimumHeight(DynamicLayoutConstants.PROMPT_MIN_HEIGHT)
        self.components["image_prompt_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        left_layout.addWidget(self.components["image_prompt_text"], 1)

        # 参数设置框架
        params_frame = QFrame()
        params_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD_ALT};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)
        params_layout = QVBoxLayout(params_frame)
        params_layout.setContentsMargins(
            DynamicLayoutConstants.PARAMS_MARGIN, 
            DynamicLayoutConstants.PARAMS_MARGIN, 
            DynamicLayoutConstants.PARAMS_MARGIN, 
            DynamicLayoutConstants.PARAMS_MARGIN
        )
        params_layout.setSpacing(DynamicLayoutConstants.PARAMS_SPACING)

        # 尺寸选择
        size_frame = QFrame()
        size_frame.setStyleSheet("background: transparent; border: none;")
        size_layout = QHBoxLayout(size_frame)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(15)

        size_label = QLabel("📐 图像尺寸")
        size_label.setFont(ThemeFonts.BODY_SMALL)
        size_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        size_layout.addWidget(size_label)

        self.components["image_size_menu"] = self._create_combobox(
            ["1280x1280", "1024x1024", "1024x768", "768x1024", "1920x1080", "1080x1920"]
        )
        size_layout.addWidget(self.components["image_size_menu"])
        size_layout.addStretch()

        params_layout.addWidget(size_frame)

        # 质量选择
        quality_frame = QFrame()
        quality_frame.setStyleSheet("background: transparent; border: none;")
        quality_layout = QHBoxLayout(quality_frame)
        quality_layout.setContentsMargins(0, 0, 0, 0)
        quality_layout.setSpacing(15)

        quality_label = QLabel("✨ 图像质量")
        quality_label.setFont(ThemeFonts.BODY_SMALL)
        quality_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        quality_layout.addWidget(quality_label)

        self.components["image_quality_menu"] = self._create_combobox(["standard", "hd"])
        quality_layout.addWidget(self.components["image_quality_menu"])
        quality_layout.addStretch()

        params_layout.addWidget(quality_frame)

        left_layout.addWidget(params_frame)

        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, DynamicLayoutConstants.BUTTON_TOP_MARGIN, 0, 0)
        button_layout.setSpacing(DynamicLayoutConstants.BUTTON_SPACING)

        self.components["generate_image_btn"] = self._create_button("🖼️ 生成图像", "primary")
        button_layout.addWidget(self.components["generate_image_btn"])

        self.components["preview_image_btn"] = self._create_button("👁️ 图像预览", "secondary")
        button_layout.addWidget(self.components["preview_image_btn"])

        button_layout.addStretch()
        left_layout.addWidget(button_frame)

        layout.addWidget(left_frame, 3)

        # 右侧：日志输出区域
        right_frame = self._create_card()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(12)

        log_label = QLabel("📋 生成日志")
        log_label.setFont(ThemeFonts.BODY_LARGE)
        log_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        right_layout.addWidget(log_label)

        self.components["image_log_text"] = QTextEdit()
        self.components["image_log_text"].setFont(ThemeFonts.CODE_SMALL)
        self.components["image_log_text"].setReadOnly(True)
        self.components["image_log_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        right_layout.addWidget(self.components["image_log_text"], 1)

        layout.addWidget(right_frame, 2)

    def _create_video_generation_tab(self, parent):
        """创建视频生成选项卡 - 左右分栏布局"""
        layout = QHBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 左侧：描述输入、URL输入和参数设置
        left_frame = self._create_card()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(
            DynamicLayoutConstants.LEFT_MARGIN, 
            DynamicLayoutConstants.LEFT_MARGIN, 
            DynamicLayoutConstants.LEFT_MARGIN, 
            DynamicLayoutConstants.LEFT_MARGIN
        )
        left_layout.setSpacing(DynamicLayoutConstants.LEFT_SPACING)

        # 提示词输入
        prompt_label = QLabel("📝 视频描述")
        prompt_label.setFont(ThemeFonts.BODY_LARGE)
        prompt_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        left_layout.addWidget(prompt_label)

        self.components["video_prompt_text"] = QTextEdit()
        self.components["video_prompt_text"].setFont(ThemeFonts.BODY_SMALL)
        self.components["video_prompt_text"].setMinimumHeight(DynamicLayoutConstants.PROMPT_MIN_HEIGHT)
        self.components["video_prompt_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        left_layout.addWidget(self.components["video_prompt_text"], 1)

        # 图片URL输入区域
        url_label = QLabel("🖼️ 参考图片URL (可选，最多2个)")
        url_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 14, QFont.Weight.Bold))
        url_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        left_layout.addWidget(url_label)

        # URL输入框1
        self.components["image_url1_entry"] = QLineEdit()
        self.components["image_url1_entry"].setPlaceholderText("图片URL 1 - 必须是公开可访问的HTTP/HTTPS链接")
        self.components["image_url1_entry"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["image_url1_entry"].setFixedHeight(38)
        self.components["image_url1_entry"].setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 0 12px;
            }}
        """)
        left_layout.addWidget(self.components["image_url1_entry"])

        # URL输入框2
        self.components["image_url2_entry"] = QLineEdit()
        self.components["image_url2_entry"].setPlaceholderText("图片URL 2 - 双图生成时建议图片尺寸一致")
        self.components["image_url2_entry"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["image_url2_entry"].setFixedHeight(38)
        self.components["image_url2_entry"].setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 0 12px;
            }}
        """)
        left_layout.addWidget(self.components["image_url2_entry"])

        # 参数设置框架
        params_frame = QFrame()
        params_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD_ALT};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)
        params_layout = QHBoxLayout(params_frame)
        params_layout.setContentsMargins(
            DynamicLayoutConstants.PARAMS_MARGIN, 
            DynamicLayoutConstants.PARAMS_MARGIN, 
            DynamicLayoutConstants.PARAMS_MARGIN, 
            DynamicLayoutConstants.PARAMS_MARGIN
        )
        params_layout.setSpacing(15)

        # 尺寸选择
        size_label = QLabel("📐 尺寸")
        size_label.setFont(ThemeFonts.BODY_XSMALL)
        size_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        params_layout.addWidget(size_label)

        self.components["video_size_menu"] = self._create_combobox(
            ["1920x1080", "1080x1920", "1280x720", "720x1280", "1024x1024"], 120, 34
        )
        params_layout.addWidget(self.components["video_size_menu"])

        # 帧率选择
        fps_label = QLabel("🎞️ 帧率")
        fps_label.setFont(ThemeFonts.BODY_XSMALL)
        fps_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        params_layout.addWidget(fps_label)

        self.components["video_fps_menu"] = self._create_combobox(["30", "60"], 80, 34)
        params_layout.addWidget(self.components["video_fps_menu"])

        # 质量选择
        quality_label = QLabel("✨ 质量")
        quality_label.setFont(ThemeFonts.BODY_XSMALL)
        quality_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        params_layout.addWidget(quality_label)

        self.components["video_quality_menu"] = self._create_combobox(["quality", "speed"], 100, 34)
        params_layout.addWidget(self.components["video_quality_menu"])

        # 音效开关
        self.components["video_audio_check"] = QCheckBox("🔊 生成音效")
        self.components["video_audio_check"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["video_audio_check"].setChecked(True)
        self.components["video_audio_check"].setStyleSheet(f"""
            QCheckBox {{
                color: {self.colors.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {self.colors.BORDER_MEDIUM};
                background-color: {self.colors.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {self.colors.PRIMARY};
                background-color: {self.colors.PRIMARY};
            }}
        """)
        params_layout.addWidget(self.components["video_audio_check"])

        left_layout.addWidget(params_frame)

        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, DynamicLayoutConstants.BUTTON_TOP_MARGIN, 0, 0)
        button_layout.setSpacing(DynamicLayoutConstants.BUTTON_SPACING)

        self.components["generate_video_btn"] = self._create_button("🎬 生成视频", "accent")
        button_layout.addWidget(self.components["generate_video_btn"])

        self.components["preview_video_btn"] = self._create_button("👁️ 视频预览", "warning")
        button_layout.addWidget(self.components["preview_video_btn"])

        button_layout.addStretch()
        left_layout.addWidget(button_frame)

        layout.addWidget(left_frame, 3)

        # 右侧：日志输出区域
        right_frame = self._create_card()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(12)

        log_label = QLabel("📋 生成日志")
        log_label.setFont(ThemeFonts.BODY_LARGE)
        log_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        right_layout.addWidget(log_label)

        self.components["video_log_text"] = QTextEdit()
        self.components["video_log_text"].setFont(ThemeFonts.CODE_SMALL)
        self.components["video_log_text"].setReadOnly(True)
        self.components["video_log_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        right_layout.addWidget(self.components["video_log_text"], 1)

        layout.addWidget(right_frame, 2)

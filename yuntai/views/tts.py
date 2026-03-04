"""
TTSBuilder - TTS语音合成页面构建器（PyQt6 重构版）
浅色米白色主题版本
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTextEdit, QListWidget,
    QListWidgetItem, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

from yuntai.gui.styles import ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing


# TTS页面布局常量 - 避免魔法数字
class TTSLayoutConstants:
    """TTS页面布局常量"""
    # 表单布局常量
    FORM_LABEL_WIDTH = 120      # 左侧标签宽度（统一，适配SoVITS模型）
    FORM_VALUE_WIDTH = 180      # 中间值标签宽度（统一）
    FORM_BUTTON_WIDTH = 80      # 按钮宽度（统一）
    FORM_SPACING = 15           # 元素间距
    FORM_ROW_SPACING = 12       # 行间距（减小间隙）
    
    # 合成文本区域常量
    SYNTH_TOP_MARGIN = 18       # 合成文本区域顶部边距
    SYNTH_BOTTOM_MARGIN = 12    # 合成文本区域底部边距
    SYNTH_LABEL_SPACING = 6     # 标签与输入框间距
    SYNTH_INPUT_MIN_HEIGHT = 80 # 合成文本输入框最小高度
    
    # 按钮区域常量
    BUTTON_TOP_MARGIN = 10      # 按钮区域顶部边距
    BUTTON_SPACING = 12         # 按钮间距
    
    # 右侧区域比例常量
    RIGHT_LOG_STRETCH = 5       # 执行输出框拉伸比例
    RIGHT_AUDIO_STRETCH = 5     # 历史音频框拉伸比例


class TTSBuilder:
    """TTS语音合成页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components
    
    @property
    def colors(self):
        """动态获取当前主题颜色"""
        return self.view.colors

    def create_page(self, tts_manager):
        """创建TTS语音合成页面"""
        self.view._highlight_nav_button(2)

        # 获取页面容器
        page = self.view.content_pages[2]
        
        # 检查组件是否已创建，如果已创建则直接返回
        if self.components.get("tts_audio_listbox") is not None:
            return
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(30, 30, 30, 30)
        page_layout.setSpacing(0)

        # 标题卡片 - 居中对齐
        header_card = self._create_card(corner_radius=ThemeCorner.LG)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(8)

        title_label = QLabel("TTS语音合成")
        title_label.setFont(ThemeFonts.TITLE_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("配置本地语音合成与播报")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        page_layout.addWidget(header_card)
        page_layout.addSpacing(15)

        # 主内容区域
        main_content = QFrame()
        main_content.setStyleSheet("background: transparent; border: none;")
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # 左侧：模型配置和合成区域
        left_frame = self._create_card()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(25, 25, 25, 25)
        left_layout.setSpacing(0)

        # 模型配置部分
        config_title = QLabel("🎛️ 模型与音频配置")
        config_title.setFont(ThemeFonts.TITLE_SMALL)
        config_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        left_layout.addWidget(config_title)
        left_layout.addSpacing(20)

        # 模型选择表单
        self._create_tts_form(left_layout, tts_manager)

        # 合成文本区域 - 减少上下空白
        synth_frame = QFrame()
        synth_frame.setStyleSheet("background: transparent; border: none;")
        synth_layout = QVBoxLayout(synth_frame)
        synth_layout.setContentsMargins(
            0, 
            TTSLayoutConstants.SYNTH_TOP_MARGIN, 
            0, 
            TTSLayoutConstants.SYNTH_BOTTOM_MARGIN
        )
        synth_layout.setSpacing(TTSLayoutConstants.SYNTH_LABEL_SPACING)

        synth_label = QLabel("📝 合成文本")
        synth_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 14, QFont.Weight.Bold))
        synth_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        synth_layout.addWidget(synth_label)

        self.components["tts_text_input"] = QTextEdit()
        self.components["tts_text_input"].setFont(ThemeFonts.BODY_SMALL)
        self.components["tts_text_input"].setMinimumHeight(TTSLayoutConstants.SYNTH_INPUT_MIN_HEIGHT)
        self.components["tts_text_input"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
            QTextEdit:focus {{
                border: 1px solid {self.colors.BORDER_FOCUS};
            }}
        """)
        synth_layout.addWidget(self.components["tts_text_input"], 1)

        left_layout.addWidget(synth_frame, 1)

        # 功能按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, TTSLayoutConstants.BUTTON_TOP_MARGIN, 0, 0)
        button_layout.setSpacing(TTSLayoutConstants.BUTTON_SPACING)

        self.components["tts_synth_btn"] = self._create_button("▶ 执行合成", "primary")
        button_layout.addWidget(self.components["tts_synth_btn"])

        self.components["tts_load_btn"] = self._create_button("📂 加载模型", "success")
        button_layout.addWidget(self.components["tts_load_btn"])

        self.components["tts_stop_btn"] = self._create_button("⏹ 停止播放", "danger")
        button_layout.addWidget(self.components["tts_stop_btn"])

        button_layout.addStretch()
        left_layout.addWidget(button_frame)

        main_layout.addWidget(left_frame, 3)

        # 右侧：执行输出和历史音频
        right_frame = self._create_card()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # 执行输出区域
        log_title = QLabel("📋 执行输出")
        log_title.setFont(ThemeFonts.BODY_LARGE)
        log_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        right_layout.addWidget(log_title)

        # 日志文本框 - 增加空间
        self.components["tts_log_text"] = QTextEdit()
        self.components["tts_log_text"].setFont(ThemeFonts.CODE_SMALL)
        self.components["tts_log_text"].setReadOnly(True)
        self.components["tts_log_text"].setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.components["tts_log_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        right_layout.addWidget(self.components["tts_log_text"], TTSLayoutConstants.RIGHT_LOG_STRETCH)

        # 历史音频列表
        audio_frame = QFrame()
        audio_frame.setStyleSheet("background: transparent; border: none;")
        audio_layout = QVBoxLayout(audio_frame)
        audio_layout.setContentsMargins(0, 10, 0, 0)
        audio_layout.setSpacing(12)

        audio_title = QLabel("🎵 历史合成音频")
        audio_title.setFont(QFont(ThemeFonts.FONT_FAMILY, 14, QFont.Weight.Bold))
        audio_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        audio_layout.addWidget(audio_title)

        # 音频列表
        self.components["tts_audio_listbox"] = QListWidget()
        self.components["tts_audio_listbox"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["tts_audio_listbox"].setMinimumHeight(100)
        self.components["tts_audio_listbox"].setStyleSheet(f"""
            QListWidget {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {self.colors.PRIMARY};
                color: {self.colors.TEXT_LIGHT};
            }}
        """)
        audio_layout.addWidget(self.components["tts_audio_listbox"], 1)

        # 音频列表按钮
        audio_btn_frame = QFrame()
        audio_btn_frame.setStyleSheet("background: transparent; border: none;")
        audio_btn_layout = QHBoxLayout(audio_btn_frame)
        audio_btn_layout.setContentsMargins(0, 0, 0, 0)
        audio_btn_layout.setSpacing(10)

        self.components["tts_play_btn"] = self._create_button("▶ 播放", "primary", height=36)
        audio_btn_layout.addWidget(self.components["tts_play_btn"])

        self.components["tts_refresh_btn"] = self._create_button("🔄 刷新", "secondary", height=36)
        audio_btn_layout.addWidget(self.components["tts_refresh_btn"])

        self.components["tts_delete_btn"] = self._create_button("🗑️ 删除", "danger", height=36)
        audio_btn_layout.addWidget(self.components["tts_delete_btn"])

        audio_btn_layout.addStretch()
        audio_layout.addWidget(audio_btn_frame)

        right_layout.addWidget(audio_frame, TTSLayoutConstants.RIGHT_AUDIO_STRETCH)

        main_layout.addWidget(right_frame, 1)

        page_layout.addWidget(main_content, 1)

    def _create_card(self, corner_radius=ThemeCorner.MD, shadow_type='md'):
        """创建卡片样式的Frame"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {corner_radius}px;
            }}
        """)
        # 应用阴影效果
        self.view._apply_shadow(card, shadow_type)
        return card

    def _create_button(self, text: str, style_type: str, height: int = 40) -> QPushButton:
        """创建按钮"""
        btn = QPushButton(text)
        btn.setFont(ThemeFonts.BODY_MEDIUM if height == 40 else ThemeFonts.BODY_XSMALL)
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
        radius = 20 if height == 40 else 18

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {self.colors.TEXT_LIGHT};
                border: none;
                border-radius: {radius}px;
                padding: 0 15px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: {self.colors.BG_HOVER};
                color: {self.colors.TEXT_DISABLED};
            }}
        """)

        return btn

    def _create_tts_form(self, parent_layout, tts_manager):
        """创建TTS配置表单 - 现代化样式"""
        # 使用常量定义布局参数
        label_width = TTSLayoutConstants.FORM_LABEL_WIDTH
        value_width = TTSLayoutConstants.FORM_VALUE_WIDTH
        button_width = TTSLayoutConstants.FORM_BUTTON_WIDTH
        spacing = TTSLayoutConstants.FORM_SPACING
        row_spacing = TTSLayoutConstants.FORM_ROW_SPACING
        
        # GPT模型选择
        gpt_frame = QFrame()
        gpt_frame.setStyleSheet("background: transparent; border: none;")
        gpt_layout = QHBoxLayout(gpt_frame)
        gpt_layout.setContentsMargins(0, 0, 0, 0)
        gpt_layout.setSpacing(spacing)

        gpt_label = QLabel("🤖 GPT模型")
        gpt_label.setFont(ThemeFonts.BODY_SMALL)
        gpt_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        gpt_label.setFixedWidth(label_width)
        gpt_layout.addWidget(gpt_label)

        self.components["tts_gpt_label"] = QLabel("未选择")
        self.components["tts_gpt_label"].setFont(ThemeFonts.BODY_SMALL)
        self.components["tts_gpt_label"].setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.components["tts_gpt_label"].setFixedWidth(value_width)
        gpt_layout.addWidget(self.components["tts_gpt_label"])

        self.components["tts_select_gpt_btn"] = self._create_button("选择", "secondary", height=36)
        self.components["tts_select_gpt_btn"].setFixedWidth(button_width)
        gpt_layout.addWidget(self.components["tts_select_gpt_btn"])

        gpt_layout.addStretch()
        parent_layout.addWidget(gpt_frame)
        parent_layout.addSpacing(row_spacing)

        # SoVITS模型选择
        sovits_frame = QFrame()
        sovits_frame.setStyleSheet("background: transparent; border: none;")
        sovits_layout = QHBoxLayout(sovits_frame)
        sovits_layout.setContentsMargins(0, 0, 0, 0)
        sovits_layout.setSpacing(spacing)

        sovits_label = QLabel("🎙 SoVITS模型")
        sovits_label.setFont(ThemeFonts.BODY_SMALL)
        sovits_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        sovits_label.setFixedWidth(label_width)
        sovits_layout.addWidget(sovits_label)

        self.components["tts_sovits_label"] = QLabel("未选择")
        self.components["tts_sovits_label"].setFont(ThemeFonts.BODY_SMALL)
        self.components["tts_sovits_label"].setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.components["tts_sovits_label"].setFixedWidth(value_width)
        sovits_layout.addWidget(self.components["tts_sovits_label"])

        self.components["tts_select_sovits_btn"] = self._create_button("选择", "secondary", height=36)
        self.components["tts_select_sovits_btn"].setFixedWidth(button_width)
        sovits_layout.addWidget(self.components["tts_select_sovits_btn"])

        sovits_layout.addStretch()
        parent_layout.addWidget(sovits_frame)
        parent_layout.addSpacing(row_spacing)

        # 参考音频选择
        audio_frame = QFrame()
        audio_frame.setStyleSheet("background: transparent; border: none;")
        audio_layout = QHBoxLayout(audio_frame)
        audio_layout.setContentsMargins(0, 0, 0, 0)
        audio_layout.setSpacing(spacing)

        audio_label = QLabel("🎵 参考音频")
        audio_label.setFont(ThemeFonts.BODY_SMALL)
        audio_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        audio_label.setFixedWidth(label_width)
        audio_layout.addWidget(audio_label)

        self.components["tts_audio_label"] = QLabel("未选择")
        self.components["tts_audio_label"].setFont(ThemeFonts.BODY_SMALL)
        self.components["tts_audio_label"].setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.components["tts_audio_label"].setFixedWidth(value_width)
        audio_layout.addWidget(self.components["tts_audio_label"])

        self.components["tts_select_audio_btn"] = self._create_button("选择", "secondary", height=36)
        self.components["tts_select_audio_btn"].setFixedWidth(button_width)
        audio_layout.addWidget(self.components["tts_select_audio_btn"])

        audio_layout.addStretch()
        parent_layout.addWidget(audio_frame)
        parent_layout.addSpacing(row_spacing)

        # 参考文本选择
        text_frame = QFrame()
        text_frame.setStyleSheet("background: transparent; border: none;")
        text_layout = QHBoxLayout(text_frame)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(spacing)

        text_label = QLabel("📄 参考文本")
        text_label.setFont(ThemeFonts.BODY_SMALL)
        text_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        text_label.setFixedWidth(label_width)
        text_layout.addWidget(text_label)

        self.components["tts_text_label"] = QLabel("未选择")
        self.components["tts_text_label"].setFont(ThemeFonts.BODY_SMALL)
        self.components["tts_text_label"].setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.components["tts_text_label"].setFixedWidth(value_width)
        text_layout.addWidget(self.components["tts_text_label"])

        self.components["tts_select_text_btn"] = self._create_button("选择", "secondary", height=36)
        self.components["tts_select_text_btn"].setFixedWidth(button_width)
        text_layout.addWidget(self.components["tts_select_text_btn"])

        text_layout.addStretch()
        parent_layout.addWidget(text_frame)

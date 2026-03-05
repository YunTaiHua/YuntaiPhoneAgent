"""
DynamicBuilder - 动态功能页面构建器（PyQt6 重构版）
浅色米白色主题版本 - 左右分栏布局
"""

import os
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTextEdit, QLineEdit,
    QComboBox, QCheckBox, QTabWidget, QSizePolicy, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor, QFont, QPixmap, QImage
from PIL import Image

from yuntai.gui.styles import (
    ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing,
    DialogStyle, get_dialog_stylesheet, get_dialog_button_stylesheet,
    get_dialog_card_stylesheet
)


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


class ImagePreviewWindow(QDialog):  # pragma: no cover
    """图像预览窗口（PyQt6版本）"""

    def __init__(self, parent, image_path: str, title: str = "图像预览"):
        """
        初始化图像预览窗口

        Args:
            parent: 父窗口
            image_path: 图像路径
            title: 窗口标题
        """
        super().__init__(parent)
        self.image_path = image_path
        
        # 获取当前主题颜色
        self.colors = parent.colors if hasattr(parent, 'colors') else ThemeColors
        
        self.setWindowTitle(title)
        self.setFixedSize(800, 600)
        self.setStyleSheet(get_dialog_stylesheet(self.colors))
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        main_layout.setSpacing(DialogStyle.DIALOG_SPACING)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(ThemeFonts.TITLE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 图像显示区域
        image_frame = QFrame()
        image_frame.setStyleSheet(get_dialog_card_stylesheet(self.colors))
        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(15, 15, 15, 15)
        
        try:
            # 使用PIL加载和显示图片
            pil_image = Image.open(image_path)
            
            # 调整图片大小以适应窗口
            max_width = 700
            max_height = 400
            pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # 转换为QPixmap
            if pil_image.mode == "RGBA":
                q_image = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, 
                               pil_image.width * 4, QImage.Format.Format_RGBA8888)
            else:
                q_image = QImage(pil_image.tobytes(), pil_image.width, pil_image.height,
                               pil_image.width * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            # 创建标签显示图片
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("background: transparent;")
            image_layout.addWidget(image_label, 1)
            
        except Exception as e:
            error_label = QLabel(f"无法加载图像: {str(e)}\n文件路径: {image_path}")
            error_label.setFont(ThemeFonts.BODY_MEDIUM)
            error_label.setStyleSheet(f"color: {self.colors.DANGER}; background: transparent; border: none;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_layout.addWidget(error_label, 1)
        
        main_layout.addWidget(image_frame, 1)
        
        # 信息区域
        info_frame = QFrame()
        info_frame.setStyleSheet(get_dialog_card_stylesheet(self.colors))
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 10, 15, 10)
        
        # 文件信息
        file_name = os.path.basename(image_path)
        file_size = os.path.getsize(image_path) / 1024  # KB
        file_info = f"文件: {file_name} ({file_size:.1f} KB)"
        info_label = QLabel(file_info)
        info_label.setFont(ThemeFonts.BODY_XSMALL)
        info_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        
        main_layout.addWidget(info_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 打开文件夹按钮
        open_folder_btn = QPushButton("打开所在文件夹")
        open_folder_btn.setFont(ThemeFonts.BODY_XSMALL)
        open_folder_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        open_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_folder_btn.setStyleSheet(get_dialog_button_stylesheet("primary", self.colors))
        open_folder_btn.clicked.connect(lambda: self.open_file_location(image_path))
        button_layout.addWidget(open_folder_btn)
        
        # 查看原图按钮
        view_original_btn = QPushButton("查看原图")
        view_original_btn.setFont(ThemeFonts.BODY_XSMALL)
        view_original_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        view_original_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        view_original_btn.setStyleSheet(get_dialog_button_stylesheet("secondary", self.colors))
        view_original_btn.clicked.connect(lambda: self.view_original_image(image_path))
        button_layout.addWidget(view_original_btn)
        
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFont(ThemeFonts.BODY_XSMALL)
        close_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(get_dialog_button_stylesheet("cancel", self.colors))
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)

    def view_original_image(self, image_path: str):
        """用默认程序打开原图"""
        try:
            import platform

            if platform.system() == "Windows":
                os.startfile(image_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", image_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", image_path])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开图像: {str(e)}")

    def open_file_location(self, file_path: str):
        """打开文件所在文件夹"""
        try:
            import platform

            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{file_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件夹: {str(e)}")


class VideoPreviewWindow(QDialog):  # pragma: no cover
    """视频预览窗口（PyQt6版本）"""

    def __init__(self, parent, video_path: str, cover_path: str = None,
                 title: str = "视频预览"):
        """
        初始化视频预览窗口

        Args:
            parent: 父窗口
            video_path: 视频路径
            cover_path: 封面路径（可选）
            title: 窗口标题
        """
        super().__init__(parent)
        self.video_path = video_path
        self.cover_path = cover_path
        
        # 获取当前主题颜色
        self.colors = parent.colors if hasattr(parent, 'colors') else ThemeColors
        
        self.setWindowTitle(title)
        self.setFixedSize(900, 700)
        self.setStyleSheet(get_dialog_stylesheet(self.colors))
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN, 
            DialogStyle.DIALOG_MARGIN
        )
        main_layout.setSpacing(DialogStyle.DIALOG_SPACING)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(ThemeFonts.TITLE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 视频/封面显示区域
        media_frame = QFrame()
        media_frame.setStyleSheet(get_dialog_card_stylesheet(self.colors))
        media_layout = QVBoxLayout(media_frame)
        media_layout.setContentsMargins(15, 15, 15, 15)
        
        # 尝试显示视频封面或占位符
        try:
            if cover_path and os.path.exists(cover_path):
                try:
                    # 使用PIL加载封面
                    pil_image = Image.open(cover_path)
                    
                    # 调整大小
                    max_width = 800
                    max_height = 450
                    pil_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                    
                    # 转换为QPixmap
                    if pil_image.mode == "RGBA":
                        q_image = QImage(pil_image.tobytes(), pil_image.width, pil_image.height,
                                       pil_image.width * 4, QImage.Format.Format_RGBA8888)
                    else:
                        q_image = QImage(pil_image.tobytes(), pil_image.width, pil_image.height,
                                       pil_image.width * 3, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_image)
                    
                    # 创建标签显示封面
                    cover_label = QLabel()
                    cover_label.setPixmap(pixmap)
                    cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    cover_label.setStyleSheet("background: transparent;")
                    media_layout.addWidget(cover_label, 1)
                    
                    # 添加播放按钮图标
                    play_label = QLabel("▶")
                    play_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
                    play_label.setStyleSheet(f"color: white; background: transparent;")
                    play_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    media_layout.addWidget(play_label)
                    
                except Exception as img_error:
                    # 如果封面加载失败，显示占位符
                    print(f"封面加载失败: {img_error}")
                    self._show_video_placeholder(media_layout, "🎬 视频封面")
            else:
                # 显示视频占位符
                self._show_video_placeholder(media_layout, "🎬 视频预览")
                
        except Exception as e:
            self._show_video_placeholder(media_layout, f"无法加载预览: {str(e)[:50]}")
        
        main_layout.addWidget(media_frame, 1)
        
        # 信息区域
        info_frame = QFrame()
        info_frame.setStyleSheet(get_dialog_card_stylesheet(self.colors))
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 10, 15, 10)
        
        # 文件信息
        video_name = os.path.basename(video_path)
        video_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        
        file_info = f"视频: {video_name} ({video_size:.1f} MB)"
        if cover_path and os.path.exists(cover_path):
            cover_size = os.path.getsize(cover_path) / 1024  # KB
            file_info += f" | 封面: {os.path.basename(cover_path)} ({cover_size:.1f} KB)"
        
        info_label = QLabel(file_info)
        info_label.setFont(ThemeFonts.BODY_XSMALL)
        info_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        
        main_layout.addWidget(info_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 播放视频按钮
        play_btn = QPushButton("播放视频")
        play_btn.setFont(ThemeFonts.BODY_XSMALL)
        play_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        play_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        play_btn.setStyleSheet(get_dialog_button_stylesheet("primary", self.colors))
        play_btn.clicked.connect(lambda: self.play_video(video_path))
        button_layout.addWidget(play_btn)
        
        # 打开文件夹按钮
        open_folder_btn = QPushButton("打开所在文件夹")
        open_folder_btn.setFont(ThemeFonts.BODY_XSMALL)
        open_folder_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        open_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_folder_btn.setStyleSheet(get_dialog_button_stylesheet("secondary", self.colors))
        open_folder_btn.clicked.connect(lambda: self.open_file_location(video_path))
        button_layout.addWidget(open_folder_btn)
        
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFont(ThemeFonts.BODY_XSMALL)
        close_btn.setFixedHeight(DialogStyle.BUTTON_HEIGHT_SMALL)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(get_dialog_button_stylesheet("cancel", self.colors))
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)

    def _show_video_placeholder(self, layout, text: str):
        """显示视频占位符"""
        placeholder = QLabel(text)
        placeholder.setFont(ThemeFonts.TITLE_SMALL)
        placeholder.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder, 1)

    def play_video(self, video_path: str):
        """播放视频"""
        try:
            import platform

            if platform.system() == "Windows":
                os.startfile(video_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", video_path])
            
            # 视频播放成功后自动关闭预览窗口
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法播放视频: {str(e)}")

    def open_file_location(self, file_path: str):
        """打开文件所在文件夹"""
        try:
            import platform

            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{file_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", file_path])
            elif platform.system() == "Linux":
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件夹: {str(e)}")

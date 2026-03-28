"""
DashboardBuilder - 控制中心页面构建器（PyQt6 重构版）
======================================================

浅色米白色主题版本。

负责构建控制中心页面的UI组件，包括执行输出显示、命令输入、
快捷键按钮和文件管理功能。

主要组件:
    - CommandTextEdit: 自定义命令输入框，支持回车发送和Ctrl+回车换行
    - DashboardBuilder: 控制中心页面构建器

功能特性:
    - 执行输出显示区域
    - 命令输入框（支持多行、自适应高度）
    - 快捷键按钮（微信、QQ、抖音等）
    - 文件上传和管理
    - 手机投屏功能

使用示例:
    >>> builder = DashboardBuilder(view)
    >>> builder.create_page()  # 创建控制中心页面
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QTextEdit, QScrollArea,
    QSizePolicy, QSpacerItem, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QCursor, QKeyEvent

from yuntai.gui.styles import ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing

# 初始化模块日志记录器
logger = logging.getLogger(__name__)


class CommandTextEdit(QTextEdit):
    """
    自定义命令输入框 - 支持回车发送和Ctrl+回车换行
    
    扩展QTextEdit，添加回车键发送命令功能。
    普通回车发送命令，Ctrl+回车换行。
    
    Signals:
        enter_pressed: 回车键按下信号，用于触发命令执行
    """
    
    enter_pressed = pyqtSignal()  # 回车键按下信号
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        处理键盘事件
        
        Args:
            event: 键盘事件对象
        """
        # 回车键
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Ctrl+回车：换行
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                cursor = self.textCursor()
                cursor.insertText('\n')
                self.setTextCursor(cursor)
            # 普通回车：发送命令
            else:
                self.enter_pressed.emit()
                event.accept()
                return
        else:
            # 其他按键正常处理
            super().keyPressEvent(event)


class DashboardBuilder:
    """
    控制中心页面构建器
    
    负责构建控制中心页面的UI组件，包括执行输出显示、命令输入、
    快捷键按钮和文件管理功能。
    
    Attributes:
        view: GUIView实例
        components: UI组件字典
        _last_line_count: 上一次输入框行数（用于自适应高度）
        shortcuts: 快捷键配置字典
    """

    def __init__(self, view_instance):
        """
        初始化控制中心页面构建器
        
        Args:
            view_instance: GUIView实例
        """
        self.view = view_instance
        self.components = view_instance.components
        self._last_line_count = 1  # 跟踪上一次行数
        logger.debug("DashboardBuilder初始化完成")

        # 快捷键配置
        self.shortcuts = {
            'w': ('打开微信', '💬'),
            'q': ('打开QQ', '🐧'),
            'd': ('打开抖音', '🎵'),
            'k': ('打开快手', '🎬'),
            't': ('打开淘宝', '🛒'),
            'm': ('QQ音乐', '🎶')
        }
    
    @property
    def colors(self):
        """动态获取当前主题颜色"""
        return self.view.colors

    def create_page(self):
        """创建控制中心页面（只执行一次）"""
        self.view._highlight_nav_button(0)

        # 获取页面容器
        page = self.view.content_pages[0]
        
        # 检查是否已有布局，如果有则直接返回（页面已创建）
        if page.layout() is not None:
            return
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(25, 25, 25, 25)
        page_layout.setSpacing(0)

        # 标题卡片 - 居中对齐
        header_card = self._create_card()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(8)

        title_label = QLabel("控制中心")
        title_label.setFont(ThemeFonts.TITLE_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("执行输出和命令控制中心")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        page_layout.addWidget(header_card)
        page_layout.addSpacing(20)

        # 主内容区域 - 左右两列布局
        main_content = QFrame()
        main_content.setStyleSheet("background: transparent; border: none;")
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # 左侧：执行输出区域
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, 3)

        # 右侧：快捷键和文件管理卡片
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, 1)

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

    def _create_left_panel(self):
        """创建左侧面板（执行输出和命令输入）"""
        panel = QFrame()
        panel.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 执行输出卡片
        output_frame = self._create_card()
        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(20, 15, 20, 15)
        output_layout.setSpacing(0)
        self.components["output_frame"] = output_frame

        # 标题行：执行输出标签 + 模拟回车按钮
        output_header = QFrame()
        output_header.setStyleSheet("background: transparent; border: none;")
        header_layout = QHBoxLayout(output_header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        output_title = QLabel("📋 执行输出")
        output_title.setFont(ThemeFonts.BODY_LARGE)
        output_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        header_layout.addWidget(output_title)
        header_layout.addStretch()

        # 模拟回车按钮
        self.components["enter_button"] = QPushButton("↵ 模拟回车")
        self.components["enter_button"].setFont(ThemeFonts.BODY_XSMALL)
        self.components["enter_button"].setFixedSize(100, 36)
        self.components["enter_button"].setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.components["enter_button"].setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors.PRIMARY};
                color: {self.colors.TEXT_LIGHT};
                border: none;
                border-radius: 18px;
            }}
            QPushButton:hover {{
                background-color: {self.colors.PRIMARY_HOVER};
            }}
        """)
        header_layout.addWidget(self.components["enter_button"])
        self.components["enter_button"].hide()

        output_layout.addWidget(output_header)
        output_layout.addSpacing(10)

        # 输出文本框
        self.components["output_text"] = QTextEdit()
        self.components["output_text"].setFont(ThemeFonts.CODE_MEDIUM)
        self.components["output_text"].setReadOnly(True)
        self.components["output_text"].setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.components["output_text"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
        """)
        output_layout.addWidget(self.components["output_text"], 1)

        layout.addWidget(output_frame, 1)

        # 命令输入区域
        input_frame = self._create_card()
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 15, 20, 15)
        input_layout.setSpacing(10)
        self.components["input_frame"] = input_frame

        input_title = QLabel("💬 命令输入")
        input_title.setFont(ThemeFonts.BODY_LARGE)
        input_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        input_layout.addWidget(input_title)

        # 命令输入框
        self.components["command_input"] = CommandTextEdit()
        self.components["command_input"].setFont(ThemeFonts.BODY_SMALL)
        self.components["command_input"].setFixedHeight(42)
        self.components["command_input"].setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.components["command_input"].setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.components["command_input"].setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.colors.BG_CARD_ALT};
                color: {self.colors.TEXT_PRIMARY};
                border: 2px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
                padding: 8px;
            }}
            QTextEdit:focus {{
                border: 2px solid {self.colors.BORDER_FOCUS};
            }}
        """)
        self.components["command_input"].textChanged.connect(self._on_input_text_changed)
        # 连接回车键信号到执行命令
        self.components["command_input"].enter_pressed.connect(self._on_enter_pressed)
        input_layout.addWidget(self.components["command_input"])

        # 已选文件显示区域
        self.components["attached_files_frame"] = QFrame()
        self.components["attached_files_frame"].setStyleSheet("background: transparent; border: none;")
        files_layout = QVBoxLayout(self.components["attached_files_frame"])
        files_layout.setContentsMargins(0, 10, 0, 0)
        files_layout.setSpacing(0)
        input_layout.addWidget(self.components["attached_files_frame"])
        self.components["attached_files_frame"].hide()

        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.setSpacing(10)

        # 执行命令按钮
        self.components["execute_button"] = self._create_button("▶ 执行命令", "primary")
        button_layout.addWidget(self.components["execute_button"])

        # 终止按钮
        self.components["terminate_button"] = self._create_button("⏹ 终止操作", "danger")
        self.components["terminate_button"].setEnabled(False)
        button_layout.addWidget(self.components["terminate_button"])

        # 语音播报按钮
        self.components["tts_button"] = self._create_button("🔊 语音播报", "secondary")
        button_layout.addWidget(self.components["tts_button"])

        # 清空按钮
        self.components["clear_output_btn"] = self._create_button("🗑 清空历史", "accent")
        button_layout.addWidget(self.components["clear_output_btn"])

        # 手机投屏按钮
        self.components["scrcpy_button"] = self._create_button("📱 手机投屏", "secondary")
        button_layout.addWidget(self.components["scrcpy_button"])

        button_layout.addStretch()
        input_layout.addWidget(button_frame)

        layout.addWidget(input_frame)

        return panel

    def _create_right_panel(self):
        """创建右侧面板（快捷键和文件管理）"""
        panel = QFrame()
        panel.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 快捷键卡片
        shortcuts_card = self._create_card()
        shortcuts_layout = QVBoxLayout(shortcuts_card)
        shortcuts_layout.setContentsMargins(15, 15, 15, 15)
        shortcuts_layout.setSpacing(0)
        self.components["shortcuts_card"] = shortcuts_card

        shortcuts_title = QLabel("⚡ 快捷键")
        shortcuts_title.setFont(ThemeFonts.BODY_LARGE)
        shortcuts_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        shortcuts_layout.addWidget(shortcuts_title)
        shortcuts_layout.addSpacing(15)

        # 快捷键按钮网格
        shortcuts_grid = QFrame()
        shortcuts_grid.setStyleSheet("background: transparent; border: none;")
        grid_layout = QGridLayout(shortcuts_grid)
        grid_layout.setSpacing(8)

        row, col = 0, 0
        for key, (app_name, icon) in self.shortcuts.items():
            btn = QPushButton(f"{icon} {app_name}")
            btn.setFont(ThemeFonts.BODY_SMALL)
            btn.setFixedHeight(45)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.colors.BG_HOVER};
                    color: {self.colors.TEXT_PRIMARY};
                    border: none;
                    border-radius: {ThemeCorner.MD}px;
                    padding: 0 15px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors.PRIMARY};
                    color: {self.colors.TEXT_LIGHT};
                }}
            """)
            grid_layout.addWidget(btn, row, col)
            self.components[f"shortcut_btn_{key}"] = btn

            col += 1
            if col > 1:
                col = 0
                row += 1

        shortcuts_layout.addWidget(shortcuts_grid)
        layout.addWidget(shortcuts_card)

        # 文件管理卡片
        file_card = self._create_card()
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(15, 15, 15, 15)
        file_layout.setSpacing(10)
        self.components["file_management_card"] = file_card

        file_title = QLabel("📁 文件管理")
        file_title.setFont(ThemeFonts.BODY_LARGE)
        file_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        file_layout.addWidget(file_title)

        # 文件列表容器
        files_container = QFrame()
        files_container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD_ALT};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)
        files_container_layout = QVBoxLayout(files_container)
        files_container_layout.setContentsMargins(8, 8, 8, 8)
        files_container_layout.setSpacing(0)

        # 可滚动的文件列表
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent; border: none;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {self.colors.BG_CARD_ALT};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.colors.BG_SCROLLBAR};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.colors.PRIMARY};
            }}
        """)

        self.components["files_list_scroll_frame"] = QFrame()
        self.components["files_list_scroll_frame"].setStyleSheet("background: transparent; border: none;")
        self.components["files_list_scroll_frame"].setLayout(QVBoxLayout())
        self.components["files_list_scroll_frame"].layout().setContentsMargins(0, 0, 0, 0)
        self.components["files_list_scroll_frame"].layout().setSpacing(2)
        self.components["files_list_scroll_frame"].layout().addStretch(1)

        scroll_area.setWidget(self.components["files_list_scroll_frame"])
        files_container_layout.addWidget(scroll_area)

        file_layout.addWidget(files_container, 1)

        # 上传文件按钮
        self.components["file_upload_button"] = QPushButton("📤 上传文件")
        self.components["file_upload_button"].setFont(ThemeFonts.BODY_MEDIUM)
        self.components["file_upload_button"].setFixedHeight(40)
        self.components["file_upload_button"].setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.components["file_upload_button"].setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors.PRIMARY};
                color: {self.colors.TEXT_LIGHT};
                border: none;
                border-radius: 20px;
            }}
            QPushButton:hover {{
                background-color: {self.colors.PRIMARY_HOVER};
            }}
        """)
        file_layout.addWidget(self.components["file_upload_button"])

        layout.addWidget(file_card, 1)

        return panel

    def _create_button(self, text: str, style_type: str) -> QPushButton:
        """创建按钮"""
        btn = QPushButton(text)
        btn.setFont(ThemeFonts.BODY_MEDIUM)
        btn.setFixedHeight(40)
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
            QPushButton:disabled {{
                background-color: {self.colors.BG_HOVER};
                color: {self.colors.TEXT_DISABLED};
            }}
        """)

        return btn

    def _on_input_text_changed(self):
        """输入框内容变化时自适应高度"""
        text_widget = self.components.get("command_input")
        if not text_widget:
            return

        try:
            content = text_widget.toPlainText()
            current_line_count = content.count('\n') + 1 if content else 1

            if not content:
                if self._last_line_count == 1:
                    return
                text_widget.setFixedHeight(42)
                self._last_line_count = 1
                return

            if current_line_count == self._last_line_count:
                return

            self._last_line_count = current_line_count

            line_height = 20
            current_height = min(current_line_count * line_height + 15, 175)

            if current_height < 42:
                current_height = 42

            text_widget.setFixedHeight(current_height)
        except AttributeError as e:
            # UI 组件属性不存在
            logger.debug("仪表盘组件属性缺失: %s", e)
        except RuntimeError as e:
            # UI 组件已被销毁
            logger.debug("仪表盘UI组件已销毁: %s", e)
        except Exception as e:
            logger.warning("仪表盘高度调整异常: %s", e)

    def _on_enter_pressed(self):
        """回车键按下时执行命令"""
        # 获取执行按钮并点击
        execute_btn = self.components.get("execute_button")
        if execute_btn:
            execute_btn.click()

    def _init_attached_files_display(self):
        """初始化已选文件显示区域"""
        if hasattr(self.view, 'show_attached_files'):
            self.view.show_attached_files([], None)

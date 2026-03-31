"""
DialogsMixin - 对话框和工具方法混入类
========================================

提供文件对话框、附件显示和组件获取/更新等辅助方法。
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

from yuntai.gui.styles import ThemeCorner, ThemeFonts


class DialogsMixin:
    """
    对话框和工具方法混入类

    提供文件对话框、附件显示和组件获取/更新等辅助方法。

    要求宿主类具有以下属性:
        - colors: ThemeColors or DarkThemeColors
        - components: dict
    """

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
            file_name = Path(file_path).name
            ext = Path(file_name).suffix.lower()

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
                icon = "📌"

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
                    except (AttributeError, TypeError):
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

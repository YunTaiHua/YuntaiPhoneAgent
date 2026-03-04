"""
ConnectionBuilder - 设备管理页面构建器（PyQt6 重构版）
浅色米白色主题版本
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QLineEdit, QComboBox,
    QRadioButton, QButtonGroup, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont

from yuntai.gui.styles import ThemeColors, ThemeFonts, ThemeCorner, ThemeSpacing


class ConnectionBuilder:
    """设备管理页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components
    
    @property
    def colors(self):
        """动态获取当前主题颜色"""
        return self.view.colors

    def create_page(self):
        """创建设备管理页面（只执行一次）"""
        self.view._highlight_nav_button(1)

        # 获取页面容器
        page = self.view.content_pages[1]
        
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

        title_label = QLabel("设备管理")
        title_label.setFont(ThemeFonts.TITLE_LARGE)
        title_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("管理您的手机设备连接")
        subtitle_label.setFont(ThemeFonts.BODY_MEDIUM)
        subtitle_label.setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle_label)

        page_layout.addWidget(header_card)
        page_layout.addSpacing(20)

        # 连接状态卡片 - 有边框
        self.components["status_card"] = QFrame()
        self.components["status_card"].setObjectName("statusCard")
        self.components["status_card"].setFixedHeight(90)
        self.components["status_card"].setStyleSheet(f"""
            QFrame#statusCard {{
                background-color: {self.colors.BG_CARD};
                border: 1px solid {self.colors.BORDER_LIGHT};
                border-radius: {ThemeCorner.LG}px;
            }}
        """)
        # 应用阴影效果
        self.view._apply_shadow(self.components["status_card"], 'md')
        status_layout = QVBoxLayout(self.components["status_card"])
        status_layout.setContentsMargins(30, 20, 30, 20)
        status_layout.setSpacing(6)

        self.components["connection_status_label"] = QLabel("● 未连接")
        self.components["connection_status_label"].setFont(ThemeFonts.TITLE_SMALL)
        self.components["connection_status_label"].setStyleSheet(f"color: {self.colors.DANGER}; background: transparent; border: none; padding: 5px;")
        self.components["connection_status_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.components["connection_status_label"].setFixedHeight(40)
        status_layout.addWidget(self.components["connection_status_label"])

        self.components["connection_info_label"] = QLabel("请配置下方连接参数")
        self.components["connection_info_label"].setFont(ThemeFonts.BODY_SMALL)
        self.components["connection_info_label"].setStyleSheet(f"color: {self.colors.TEXT_SECONDARY}; background: transparent; border: none;")
        self.components["connection_info_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.components["connection_info_label"])

        page_layout.addWidget(self.components["status_card"])
        page_layout.addSpacing(16)

        # 连接设置表单
        self._create_connection_form(page_layout)

        page_layout.addStretch()

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

    def _create_connection_form(self, parent_layout):
        """创建设备连接表单 - 现代化卡片样式"""
        form_frame = self._create_card()
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(25, 25, 25, 25)
        form_layout.setSpacing(20)

        # 表单标题
        form_title = QLabel("🔗 设备连接设置")
        form_title.setFont(ThemeFonts.TITLE_SMALL)
        form_title.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        form_layout.addWidget(form_title)

        # 设备类型选择
        device_type_frame = QFrame()
        device_type_frame.setStyleSheet("background: transparent; border: none;")
        device_type_layout = QVBoxLayout(device_type_frame)
        device_type_layout.setContentsMargins(0, 0, 0, 0)
        device_type_layout.setSpacing(10)

        device_type_label = QLabel("📱 设备类型")
        device_type_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 14, QFont.Weight.Bold))
        device_type_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        device_type_layout.addWidget(device_type_label)

        # 设备类型下拉框容器
        device_type_border = QFrame()
        device_type_border.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)
        device_type_border_layout = QVBoxLayout(device_type_border)
        device_type_border_layout.setContentsMargins(1, 1, 1, 1)

        self.components["device_type_menu"] = QComboBox()
        self.components["device_type_menu"].addItems(["Android (ADB)", "HarmonyOS (HDC)"])
        self.components["device_type_menu"].setFont(ThemeFonts.BODY_SMALL)
        self.components["device_type_menu"].setFixedHeight(42)
        self.components["device_type_menu"].setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.components["device_type_menu"].currentTextChanged.connect(self.view._on_device_type_change)
        self.components["device_type_menu"].setStyleSheet(f"""
            QComboBox {{
                background-color: {self.colors.BG_INPUT};
                color: {self.colors.TEXT_PRIMARY};
                border: none;
                border-radius: {ThemeCorner.MD - 1}px;
                padding: 0 12px;
            }}
            QComboBox:hover {{
                border: 1px solid {self.colors.BORDER_FOCUS};
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
        device_type_border_layout.addWidget(self.components["device_type_menu"])

        device_type_layout.addWidget(device_type_border)
        form_layout.addWidget(device_type_frame)

        # 连接方式选择
        conn_type_frame = QFrame()
        conn_type_frame.setStyleSheet("background: transparent; border: none;")
        conn_type_layout = QVBoxLayout(conn_type_frame)
        conn_type_layout.setContentsMargins(0, 0, 0, 0)
        conn_type_layout.setSpacing(12)

        conn_type_label = QLabel("📡 连接方式")
        conn_type_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 14, QFont.Weight.Bold))
        conn_type_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        conn_type_layout.addWidget(conn_type_label)

        # 单选按钮容器
        radio_container = QFrame()
        radio_container.setStyleSheet("background: transparent; border: none;")
        radio_layout = QHBoxLayout(radio_container)
        radio_layout.setContentsMargins(0, 0, 0, 0)
        radio_layout.setSpacing(30)

        self.components["conn_button_group"] = QButtonGroup(radio_container)

        usb_option = QRadioButton("USB调试连接")
        usb_option.setFont(ThemeFonts.BODY_SMALL)
        usb_option.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        usb_option.setStyleSheet(f"""
            QRadioButton {{
                color: {self.colors.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {self.colors.BORDER_MEDIUM};
                background-color: {self.colors.BG_INPUT};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {self.colors.PRIMARY};
                background-color: {self.colors.PRIMARY};
            }}
            QRadioButton::indicator:hover {{
                border: 2px solid {self.colors.PRIMARY_HOVER};
            }}
        """)
        self.components["conn_button_group"].addButton(usb_option)
        self.components["usb_option"] = usb_option
        radio_layout.addWidget(usb_option)

        wireless_option = QRadioButton("无线调试连接")
        wireless_option.setFont(ThemeFonts.BODY_SMALL)
        wireless_option.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        wireless_option.setChecked(True)
        wireless_option.setStyleSheet(f"""
            QRadioButton {{
                color: {self.colors.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {self.colors.BORDER_MEDIUM};
                background-color: {self.colors.BG_INPUT};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {self.colors.PRIMARY};
                background-color: {self.colors.PRIMARY};
            }}
            QRadioButton::indicator:hover {{
                border: 2px solid {self.colors.PRIMARY_HOVER};
            }}
        """)
        self.components["conn_button_group"].addButton(wireless_option)
        self.components["wireless_option"] = wireless_option
        radio_layout.addWidget(wireless_option)

        radio_layout.addStretch()
        conn_type_layout.addWidget(radio_container)
        form_layout.addWidget(conn_type_frame)

        # USB设置
        self.components["usb_frame"] = QFrame()
        self.components["usb_frame"].setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD_ALT};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)
        usb_layout = QVBoxLayout(self.components["usb_frame"])
        usb_layout.setContentsMargins(20, 15, 20, 15)
        usb_layout.setSpacing(8)

        usb_label = QLabel("🔌 USB设备ID")
        usb_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 13, QFont.Weight.Bold))
        usb_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        usb_layout.addWidget(usb_label)

        self.components["usb_entry"] = QLineEdit()
        self.components["usb_entry"].setPlaceholderText("通过 adb devices / hdc list targets / idevice_id -l 查看")
        self.components["usb_entry"].setFont(ThemeFonts.BODY_SMALL)
        self.components["usb_entry"].setFixedHeight(42)
        self.components["usb_entry"].setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors.BG_INPUT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 0 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.colors.BORDER_FOCUS};
            }}
        """)
        usb_layout.addWidget(self.components["usb_entry"])

        # 无线设置
        self.components["wireless_frame"] = QFrame()
        self.components["wireless_frame"].setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors.BG_CARD_ALT};
                border-radius: {ThemeCorner.MD}px;
            }}
        """)
        wireless_layout = QVBoxLayout(self.components["wireless_frame"])
        wireless_layout.setContentsMargins(20, 15, 20, 15)
        wireless_layout.setSpacing(12)

        # IP地址
        ip_label = QLabel("🌐 IP地址")
        ip_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 13, QFont.Weight.Bold))
        ip_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        wireless_layout.addWidget(ip_label)

        self.components["ip_entry"] = QLineEdit()
        self.components["ip_entry"].setPlaceholderText("例如: 192.168.1.100")
        self.components["ip_entry"].setFont(ThemeFonts.BODY_SMALL)
        self.components["ip_entry"].setFixedHeight(42)
        self.components["ip_entry"].setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors.BG_INPUT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 0 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.colors.BORDER_FOCUS};
            }}
        """)
        wireless_layout.addWidget(self.components["ip_entry"])

        # 端口
        port_label = QLabel("📟 端口")
        port_label.setFont(QFont(ThemeFonts.FONT_FAMILY, 13, QFont.Weight.Bold))
        port_label.setStyleSheet(f"color: {self.colors.TEXT_PRIMARY}; background: transparent; border: none;")
        wireless_layout.addWidget(port_label)

        self.components["port_entry"] = QLineEdit()
        self.components["port_entry"].setPlaceholderText("默认: 5555")
        self.components["port_entry"].setText("5555")
        self.components["port_entry"].setFont(ThemeFonts.BODY_SMALL)
        self.components["port_entry"].setFixedHeight(42)
        self.components["port_entry"].setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.colors.BG_INPUT};
                color: {self.colors.TEXT_PRIMARY};
                border: 1px solid {self.colors.BORDER_MEDIUM};
                border-radius: {ThemeCorner.MD}px;
                padding: 0 12px;
            }}
            QLineEdit:focus {{
                border: 2px solid {self.colors.BORDER_FOCUS};
            }}
        """)
        wireless_layout.addWidget(self.components["port_entry"])

        # 默认显示无线设置，USB设置默认隐藏
        form_layout.addWidget(self.components["wireless_frame"])
        form_layout.addWidget(self.components["usb_frame"])
        self.components["usb_frame"].hide()

        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("background: transparent; border: none;")
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 5, 0, 0)
        button_layout.setSpacing(12)

        # 检测设备按钮
        self.components["detect_devices_btn"] = self._create_button("🔍 检测设备", "secondary")
        button_layout.addWidget(self.components["detect_devices_btn"])

        # 连接设备按钮
        self.components["connect_device_btn"] = self._create_button("🔗 连接设备", "primary")
        button_layout.addWidget(self.components["connect_device_btn"])

        # 断开连接按钮
        self.components["disconnect_device_btn"] = self._create_button("⏹ 断开连接", "danger")
        button_layout.addWidget(self.components["disconnect_device_btn"])

        button_layout.addStretch()
        form_layout.addWidget(button_frame)

        parent_layout.addWidget(form_frame)

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

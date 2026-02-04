"""
ConnectionBuilder - 设备管理页面构建器
浅色米白色主题版本
"""
import customtkinter as ctk
from .theme import ThemeColors


class ConnectionBuilder:
    """设备管理页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建设备管理页面（只执行一次）"""
        self.view._highlight_nav_button(1)

        content_frame = ctk.CTkFrame(
            self.view.content_pages[1], 
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="设备管理",
            font=("Microsoft YaHei", 28, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            content_frame,
            text="管理您的手机设备连接",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 30))

        # 连接状态卡片 - 现代化样式
        self.components["status_card"] = ctk.CTkFrame(
            content_frame, 
            corner_radius=12,
            height=100,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        self.components["status_card"].pack(fill="x", pady=(0, 16))

        status_inner = ctk.CTkFrame(
            self.components["status_card"], 
            fg_color="transparent"
        )
        status_inner.pack(expand=True, padx=30, pady=25)

        self.components["connection_status_label"] = ctk.CTkLabel(
            status_inner,
            text="● 未连接",
            font=("Microsoft YaHei", 24, "bold"),
            text_color=ThemeColors.DANGER
        )
        self.components["connection_status_label"].pack(anchor="w", pady=(0, 8))

        # 添加状态描述
        ctk.CTkLabel(
            status_inner,
            text="请配置下方连接参数",
            font=("Microsoft YaHei", 13),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w")

        # 连接设置表单
        self._create_connection_form(content_frame)

    def _create_connection_form(self, parent):
        """创建设备连接表单 - 现代化卡片样式"""
        form_frame = ctk.CTkFrame(
            parent, 
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        form_frame.pack(fill="x", pady=(0, 16))

        # 表单标题
        ctk.CTkLabel(
            form_frame,
            text="🔗 设备连接设置",
            font=("Microsoft YaHei", 18, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=25, pady=25)

        # 设备类型选择
        device_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        device_type_frame.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkLabel(
            device_type_frame,
            text="📱 设备类型",
            font=("Microsoft YaHei", 14, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 10))

        self.components["device_type_var"] = ctk.StringVar(value="Android (ADB)")

        device_type_menu = ctk.CTkOptionMenu(
            device_type_frame,
            values=["Android (ADB)", "HarmonyOS (HDC)"],
            variable=self.components["device_type_var"],
            font=("Microsoft YaHei", 13),
            height=42,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            button_color="#C4C9D0",
            button_hover_color="#A8AEB5",
            text_color=ThemeColors.TEXT_PRIMARY,
            command=self.view._on_device_type_change
        )
        device_type_menu.pack(anchor="w", pady=5)

        # 连接方式选择
        conn_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        conn_type_frame.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkLabel(
            conn_type_frame,
            text="📡 连接方式",
            font=("Microsoft YaHei", 14, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 12))

        self.components["conn_var"] = ctk.StringVar(value="wireless")

        # 单选按钮容器
        radio_container = ctk.CTkFrame(conn_type_frame, fg_color="transparent")
        radio_container.pack(fill="x")

        usb_option = ctk.CTkRadioButton(
            radio_container,
            text="USB调试连接",
            variable=self.components["conn_var"],
            value="usb",
            font=("Microsoft YaHei", 13),
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        usb_option.pack(side="left", padx=(0, 30))

        wireless_option = ctk.CTkRadioButton(
            radio_container,
            text="无线调试连接",
            variable=self.components["conn_var"],
            value="wireless",
            font=("Microsoft YaHei", 13),
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        wireless_option.pack(side="left")

        # USB设置
        self.components["usb_frame"] = ctk.CTkFrame(
            form_frame, 
            fg_color=ThemeColors.BG_CARD_ALT,
            corner_radius=12
        )

        ctk.CTkLabel(
            self.components["usb_frame"],
            text="🔌 USB设备ID",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 8))

        self.components["usb_entry"] = ctk.CTkEntry(
            self.components["usb_frame"],
            placeholder_text="通过 adb devices / hdc list targets / idevice_id -l 查看",
            font=("Microsoft YaHei", 13),
            height=42,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["usb_entry"].pack(fill="x", padx=20, pady=(0, 15))

        # 无线设置
        self.components["wireless_frame"] = ctk.CTkFrame(
            form_frame, 
            fg_color=ThemeColors.BG_CARD_ALT,
            corner_radius=12
        )

        # IP地址
        ctk.CTkLabel(
            self.components["wireless_frame"],
            text="🌐 IP地址",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(15, 8))

        self.components["ip_entry"] = ctk.CTkEntry(
            self.components["wireless_frame"],
            placeholder_text="例如: 192.168.1.100",
            font=("Microsoft YaHei", 13),
            height=42,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["ip_entry"].pack(fill="x", padx=20, pady=(0, 12))

        # 端口
        ctk.CTkLabel(
            self.components["wireless_frame"],
            text="📟 端口",
            font=("Microsoft YaHei", 13, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(0, 8))

        self.components["port_entry"] = ctk.CTkEntry(
            self.components["wireless_frame"],
            placeholder_text="默认: 5555",
            font=("Microsoft YaHei", 13),
            height=42,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["port_entry"].insert(0, "5555")
        self.components["port_entry"].pack(fill="x", padx=20, pady=(0, 15))

        # 按钮区域
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=25, pady=25)

        self.components["detect_devices_btn"] = ctk.CTkButton(
            button_frame,
            text="🔍 检测设备",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.SECONDARY,
            hover_color=ThemeColors.SECONDARY_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["detect_devices_btn"].pack(side="left", padx=(0, 12))

        self.components["connect_device_btn"] = ctk.CTkButton(
            button_frame,
            text="🔗 连接设备",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["connect_device_btn"].pack(side="left", padx=(0, 12))

        self.components["disconnect_device_btn"] = ctk.CTkButton(
            button_frame,
            text="⏹ 断开连接",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.DANGER,
            hover_color=ThemeColors.DANGER_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["disconnect_device_btn"].pack(side="left")

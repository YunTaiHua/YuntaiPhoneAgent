"""
ConnectionBuilder - 设备管理页面构建器
"""
import customtkinter as ctk
from .theme import ThemeColors


class ConnectionBuilder:
    """设备管理页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建设备管理页面"""
        self.view._clear_content_card()
        self.view._highlight_nav_button(1)

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="📱 设备管理",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            content_frame,
            text="管理您的手机设备连接",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 30))

        # 连接状态卡片
        self.components["status_card"] = ctk.CTkFrame(content_frame, corner_radius=15, height=100)
        self.components["status_card"].pack(fill="x", pady=(0, 30))

        status_inner = ctk.CTkFrame(self.components["status_card"], fg_color="transparent")
        status_inner.pack(expand=True, padx=30, pady=20)

        self.components["connection_status_label"] = ctk.CTkLabel(
            status_inner,
            text="● 未连接",
            font=("Microsoft YaHei", 24, "bold"),
            text_color=ThemeColors.DANGER
        )
        self.components["connection_status_label"].pack(anchor="w", pady=(0, 10))

        # 连接设置表单
        self._create_connection_form(content_frame)

    def _create_connection_form(self, parent):
        """创建设备连接表单"""
        form_frame = ctk.CTkFrame(parent, corner_radius=15)
        form_frame.pack(fill="x", pady=(0, 20))

        # 表单标题
        ctk.CTkLabel(
            form_frame,
            text="设备连接设置",
            font=("Microsoft YaHei", 16, "bold")
        ).pack(anchor="w", padx=20, pady=20)

        # 设备类型选择
        device_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        device_type_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            device_type_frame,
            text="设备类型:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", pady=(0, 10))

        self.components["device_type_var"] = ctk.StringVar(value="android")

        android_option = ctk.CTkRadioButton(
            device_type_frame,
            text="Android (ADB)",
            variable=self.components["device_type_var"],
            value="android",
            font=("Microsoft YaHei", 13),
            command=lambda: self.view._on_device_type_change("android")
        )
        android_option.pack(anchor="w", pady=5)

        # 连接方式选择
        conn_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        conn_type_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            conn_type_frame,
            text="连接方式:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", pady=(0, 10))

        self.components["conn_var"] = ctk.StringVar(value="wireless")

        usb_option = ctk.CTkRadioButton(
            conn_type_frame,
            text="USB调试连接",
            variable=self.components["conn_var"],
            value="usb",
            font=("Microsoft YaHei", 13)
        )
        usb_option.pack(anchor="w", pady=5)

        wireless_option = ctk.CTkRadioButton(
            conn_type_frame,
            text="无线调试连接",
            variable=self.components["conn_var"],
            value="wireless",
            font=("Microsoft YaHei", 13)
        )
        wireless_option.pack(anchor="w", pady=5)

        # USB设置
        self.components["usb_frame"] = ctk.CTkFrame(form_frame, fg_color="transparent")

        ctk.CTkLabel(
            self.components["usb_frame"],
            text="USB设备ID:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.components["usb_entry"] = ctk.CTkEntry(
            self.components["usb_frame"],
            placeholder_text="通过 adb devices / hdc list targets / idevice_id -l 查看",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["usb_entry"].pack(fill="x", padx=20, pady=(0, 10))

        # 无线设置
        self.components["wireless_frame"] = ctk.CTkFrame(form_frame, fg_color="transparent")

        # IP地址
        ctk.CTkLabel(
            self.components["wireless_frame"],
            text="IP地址:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.components["ip_entry"] = ctk.CTkEntry(
            self.components["wireless_frame"],
            placeholder_text="例如: 192.168.1.100",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["ip_entry"].pack(fill="x", padx=20, pady=(0, 10))

        # 端口
        ctk.CTkLabel(
            self.components["wireless_frame"],
            text="端口:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.components["port_entry"] = ctk.CTkEntry(
            self.components["wireless_frame"],
            placeholder_text="默认: 5555",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["port_entry"].insert(0, "5555")
        self.components["port_entry"].pack(fill="x", padx=20)

        # 按钮区域
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        self.components["detect_devices_btn"] = ctk.CTkButton(
            button_frame,
            text="🔍 检测设备",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["detect_devices_btn"].pack(side="left", padx=(0, 10))

        self.components["connect_device_btn"] = ctk.CTkButton(
            button_frame,
            text="🔗 连接设备",
            font=("Microsoft YaHei", 13),
            height=40,
            fg_color=ThemeColors.PRIMARY,
            hover_color="#3a56d4"
        )
        self.components["connect_device_btn"].pack(side="left", padx=(0, 10))

        self.components["disconnect_device_btn"] = ctk.CTkButton(
            button_frame,
            text="断开连接",
            font=("Microsoft YaHei", 13),
            height=40,
            fg_color=ThemeColors.DANGER,
            hover_color="#c62828"
        )
        self.components["disconnect_device_btn"].pack(side="left")

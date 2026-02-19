import tkinter as tk
import os
import subprocess
import threading
import customtkinter as ctk
import pyperclip
from typing import Optional, Dict, Any, Callable

from yuntai.gui.gui_view import GUIView
from yuntai.core.config import ThemeColors, DEVICE_TYPE_HARMONY


class ConnectionHandler:
    """设备连接管理处理器"""

    def __init__(self, controller):
        self.controller = controller
        self.root = controller.root
        self.view = controller.view
        self.task_manager = controller.task_manager

    def show_panel(self):
        """显示设备管理页面"""
        self.view.create_connection_page()
        self._bind_events()
        self._update_connection_status_gui(self.task_manager.is_connected)

    def _bind_events(self):
        """绑定连接页面事件"""
        # 检测设备按钮
        detect_btn = self.view.get_component("detect_devices_btn")
        if detect_btn:
            detect_btn.configure(command=self.detect_devices_gui)

        # 连接设备按钮
        connect_btn = self.view.get_component("connect_device_btn")
        if connect_btn:
            connect_btn.configure(command=self.connect_device_gui)

        # 断开连接按钮
        disconnect_btn = self.view.get_component("disconnect_device_btn")
        if disconnect_btn:
            disconnect_btn.configure(command=self.disconnect_device)

        # 连接方式切换事件
        conn_var = self.view.get_component("conn_var")
        if conn_var:
            conn_var.trace("w", lambda *args: self._show_connection_form())

    def _show_connection_form(self):
        """显示连接表单"""
        conn_var = self.view.get_component("conn_var")
        usb_frame = self.view.get_component("usb_frame")
        wireless_frame = self.view.get_component("wireless_frame")

        if conn_var and usb_frame and wireless_frame:
            if conn_var.get() == "usb":
                wireless_frame.pack_forget()
                usb_frame.pack(fill="x")
            else:
                usb_frame.pack_forget()
                wireless_frame.pack(fill="x")

    def _get_device_type(self) -> str:
        """获取当前选择的设备类型"""
        device_type_var = self.view.get_component("device_type_var")
        if device_type_var:
            if "HarmonyOS" in device_type_var.get():
                return DEVICE_TYPE_HARMONY
        return "android"

    def _get_device_type_display(self) -> str:
        """获取当前选择的设备类型显示文本"""
        device_type_var = self.view.get_component("device_type_var")
        if device_type_var:
            return device_type_var.get()
        return "Android (ADB)"

    def connect_device_gui(self):
        """GUI界面连接设备"""
        config = self._get_connection_config_from_ui()
        if not config:
            return

        def connect_thread():
            success, device_id, message = self.task_manager.connect_device(config)

            if success:
                self.controller.message_queue.put(("success", f"✅ {message}"))
                self._update_connection_status_gui(True)
                if hasattr(self.controller, '_sync_device_to_task_chain'):
                    self.controller._sync_device_to_task_chain()
            else:
                self.controller.message_queue.put(("error", f"❌ 连接失败: {message}"))
                self._update_connection_status_gui(False)

        threading.Thread(target=connect_thread, daemon=True).start()

    def _get_connection_config_from_ui(self):
        """从UI获取连接配置"""
        conn_var = self.view.get_component("conn_var")
        if not conn_var:
            self.controller.show_toast("UI组件未初始化", "error")
            return None

        device_type = self._get_device_type()
        device_type_display = self._get_device_type_display()

        config = {
            "connection_type": conn_var.get(),
            "wireless_ip": "",
            "wireless_port": "5555",
            "usb_device_id": "",
            "device_type": device_type,
            "device_type_display": device_type_display
        }

        if conn_var.get() == "usb":
            usb_entry = self.view.get_component("usb_entry")
            if usb_entry:
                device_id = usb_entry.get().strip()
                if not device_id:
                    self.controller.show_toast("请输入USB设备ID", "warning")
                    return None
                config["usb_device_id"] = device_id
        else:
            ip_entry = self.view.get_component("ip_entry")
            port_entry = self.view.get_component("port_entry")

            if ip_entry and port_entry:
                ip = ip_entry.get().strip()
                port = port_entry.get().strip()

                if not ip:
                    self.controller.show_toast("请输入IP地址", "warning")
                    return None

                config["wireless_ip"] = ip
                config["wireless_port"] = port if port else "5555"

        return config

    def detect_devices_gui(self):
        """GUI界面检测设备 - 弹窗显示结果"""
        def detect_thread():
            device_type = self._get_device_type()
            device_type_display = self._get_device_type_display()
            devices = self.task_manager.detect_devices(device_type)

            def show_result_dialog():
                result_window = ctk.CTkToplevel(self.root)
                result_window.title("设备检测结果")
                result_window.geometry("600x500")
                result_window.resizable(True, True)
                result_window.transient(self.root)
                result_window.grab_set()

                ctk.CTkLabel(
                    result_window,
                    text="📱 设备检测结果",
                    font=("Microsoft YaHei", 20, "bold")
                ).pack(pady=20)

                ctk.CTkLabel(
                    result_window,
                    text=f"设备类型: {device_type_display}",
                    font=("Microsoft YaHei", 12),
                    text_color=ThemeColors.TEXT_SECONDARY
                ).pack(pady=(0, 10))

                if devices:
                    device_count = len(devices)
                    status_text = f"✅ 检测到 {device_count} 个设备"

                    ctk.CTkLabel(
                        result_window,
                        text=status_text,
                        font=("Microsoft YaHei", 14, "bold"),
                        text_color=ThemeColors.SUCCESS
                    ).pack(pady=(0, 10))

                    text_frame = ctk.CTkFrame(result_window, corner_radius=10)
                    text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

                    toolbar = ctk.CTkFrame(text_frame, fg_color="transparent", height=40)
                    toolbar.pack(fill="x", padx=10, pady=(10, 0))

                    ctk.CTkLabel(
                        toolbar,
                        text="设备列表（可全选复制）:",
                        font=("Microsoft YaHei", 12, "bold")
                    ).pack(side="left")

                    def copy_to_clipboard():
                        device_text = "\n".join([f"{i + 1}. {device}" for i, device in enumerate(devices)])
                        pyperclip.copy(device_text)
                        self.controller.show_toast("已复制到剪贴板", "success")

                    ctk.CTkButton(
                        toolbar,
                        text="📋 复制",
                        font=("Microsoft YaHei", 12),
                        height=30,
                        width=80,
                        command=copy_to_clipboard
                    ).pack(side="right", padx=5)

                    result_text = ctk.CTkTextbox(
                        text_frame,
                        font=("Consolas", 12),
                        activate_scrollbars=True
                    )
                    result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

                    result_text.insert("1.0", "设备ID列表:\n" + "=" * 50 + "\n\n")
                    for i, device in enumerate(devices, 1):
                        result_text.insert("end", f"{i:2d}. {device}\n")

                    result_text.insert("end", "\n" + "=" * 50 + "\n")
                    result_text.insert("end", "💡 使用说明:\n")
                    result_text.insert("end", "1. 选择文本进行复制\n")
                    result_text.insert("end", "2. 点击上方复制按钮可复制全部\n")
                    result_text.insert("end", "3. 在USB连接方式下使用设备ID连接\n")

                    result_text.configure(state="normal")
                    result_text.bind("<Control-c>", lambda e: copy_to_clipboard())
                    result_text.configure(state="disabled")

                else:
                    status_text = f"❌ 未检测到任何设备 ({device_type_display})"

                    ctk.CTkLabel(
                        result_window,
                        text=status_text,
                        font=("Microsoft YaHei", 14, "bold"),
                        text_color=ThemeColors.DANGER
                    ).pack(pady=(0, 10))

                    text_frame = ctk.CTkFrame(result_window, corner_radius=10)
                    text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

                    toolbar = ctk.CTkFrame(text_frame, fg_color="transparent", height=40)
                    toolbar.pack(fill="x", padx=10, pady=(10, 0))

                    ctk.CTkLabel(
                        toolbar,
                        text="故障排除指南:",
                        font=("Microsoft YaHei", 12, "bold")
                    ).pack(side="left")

                    tool_name = "hdc" if device_type == DEVICE_TYPE_HARMONY else "adb"
                    troubleshooting_text = f"""请检查以下项目：
    1. 手机是否已通过USB线连接电脑
    2. 手机是否已开启【开发者选项】和【USB调试】
    3. 连接电脑时，手机上是否点击了【允许USB调试】
    4. 尝试重新插拔USB线或重启{tool_name.upper()}服务
    5. 如果是无线连接，请确保IP和端口正确"""

                    def copy_troubleshooting():
                        pyperclip.copy(troubleshooting_text)
                        self.controller.show_toast("故障排除指南已复制", "success")

                    ctk.CTkButton(
                        toolbar,
                        text="📋 复制指南",
                        font=("Microsoft YaHei", 12),
                        height=30,
                        width=100,
                        command=copy_troubleshooting
                    ).pack(side="right", padx=5)

                    result_text = ctk.CTkTextbox(
                        text_frame,
                        font=("Microsoft YaHei", 12),
                        activate_scrollbars=True
                    )
                    result_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

                    result_text.insert("1.0", "请检查以下项目：\n" + "=" * 50 + "\n\n")
                    checks = [
                        "1. 📱 手机是否已通过USB线连接电脑",
                        "2. ⚙️ 手机是否已开启【开发者选项】和【USB调试】",
                        "3. 📲 连接电脑时，手机上是否点击了【允许USB调试】",
                        f"4. 🔄 尝试重新插拔USB线或重启{tool_name.upper()}服务",
                        "5. 🔌 如果是无线连接，请确保IP和端口正确"
                    ]

                    for check in checks:
                        result_text.insert("end", f"{check}\n")

                    result_text.insert("end", "\n" + "=" * 50 + "\n")
                    result_text.insert("end", "💡 解决方案:\n")
                    result_text.insert("end", "• 在手机设置中搜索【开发者选项】\n")
                    result_text.insert("end", "• 打开【USB调试】开关\n")
                    result_text.insert("end", "• 连接电脑时授权调试权限\n")

                    result_text.configure(state="normal")

                ctk.CTkButton(
                    result_window,
                    text="关闭",
                    font=("Microsoft YaHei", 14),
                    height=40,
                    width=120,
                    command=result_window.destroy
                ).pack(pady=20)

                if devices:
                    self.controller.show_toast(f"检测到 {len(devices)} 个设备", "success")
                else:
                    self.controller.show_toast("未检测到设备", "warning")

            self.root.after(0, show_result_dialog)

        threading.Thread(target=detect_thread, daemon=True).start()

    def disconnect_device(self):
        """断开设备连接"""
        self.task_manager.disconnect_device()
        self._update_connection_status_gui(False)
        self.controller.show_toast("设备已断开", "info")

    def _update_connection_status_gui(self, connected):
        """更新连接状态显示"""
        self.root.after(0, lambda: self.__update_connection_status_gui(connected))

    def __update_connection_status_gui(self, connected):
        """在GUI线程中更新连接状态"""
        connection_indicator = self.view.get_component("connection_indicator")
        status_label = self.view.get_component("status_label")

        if connected:
            if connection_indicator:
                connection_indicator.configure(
                    text="● 已连接",
                    text_color=ThemeColors.SUCCESS
                )
            if status_label:
                status_label.configure(text="设备已连接")
        else:
            if connection_indicator:
                connection_indicator.configure(
                    text="● 未连接",
                    text_color=ThemeColors.DANGER
                )
            if status_label:
                status_label.configure(text="设备未连接")

        # 更新连接页面状态 - 只显示状态，不显示设备ID
        conn_status_label = self.view.get_component("connection_status_label")
        if conn_status_label:
            if connected:
                conn_status_label.configure(
                    text="● 已连接",
                    text_color=ThemeColors.SUCCESS,
                    font=("Microsoft YaHei", 24, "bold")
                )
            else:
                conn_status_label.configure(
                    text="● 未连接",
                    text_color=ThemeColors.DANGER,
                    font=("Microsoft YaHei", 24, "bold")
                )

        # 删除对connection_info_label的更新，让第二行不显示
        conn_info_label = self.view.get_component("connection_info_label")
        if conn_info_label:
            conn_info_label.configure(text="")  # 清空第二行

    def show_scrcpy_popup(self):
        """显示投屏设置弹窗"""
        popup = ctk.CTkToplevel(self.root)
        popup.title("📱 手机投屏")
        popup.geometry("400x350")  # 增加高度以容纳设备选择
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        # 标题
        ctk.CTkLabel(
            popup,
            text="📱 手机投屏设置",
            font=("Microsoft YaHei", 20, "bold")
        ).pack(pady=20)

        # 获取可用设备列表
        devices = self.task_manager.detect_devices()

        # 设备选择区域
        device_frame = ctk.CTkFrame(popup, fg_color="transparent")
        device_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            device_frame,
            text="选择设备:",
            font=("Microsoft YaHei", 14)
        ).pack(anchor="w", pady=(0, 5))

        # 设备选择变量
        device_var = ctk.StringVar()

        if devices:
            # 创建设备选择下拉菜单
            device_menu = ctk.CTkOptionMenu(
                device_frame,
                variable=device_var,
                values=devices,
                font=("Microsoft YaHei", 12),
                width=300
            )
            device_menu.pack(fill="x", pady=(0, 10))
            # 默认选择第一个设备
            if devices:
                device_var.set(devices[0])
        else:
            ctk.CTkLabel(
                device_frame,
                text="⚠️ 未检测到可用设备",
                font=("Microsoft YaHei", 12),
                text_color=ThemeColors.WARNING
            ).pack(pady=(0, 10))
            device_var.set("")

        # 窗口置顶勾选框
        always_on_top_var = ctk.BooleanVar(value=False)
        always_on_top_check = ctk.CTkCheckBox(
            popup,
            text="窗口置顶",
            variable=always_on_top_var,
            font=("Microsoft YaHei", 14)
        )
        always_on_top_check.pack(pady=10)

        # 启动按钮
        def start_scrcpy():
            if not devices:
                self.controller.show_toast("没有可用设备", "warning")
                return

            selected_device = device_var.get()
            if not selected_device:
                self.controller.show_toast("请选择一个设备", "warning")
                return

            # 构建命令
            cmd = [self.controller.scrcpy_path, "--stay-awake"]

            # 添加设备选择参数
            cmd.append("-s")
            cmd.append(selected_device)

            if always_on_top_var.get():
                cmd.append("--always-on-top")

            try:
                # 在新线程中启动scrcpy
                def run_scrcpy():
                    try:
                        process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        self.controller.active_subprocesses.append(process)
                        self.controller.show_toast(f"手机投屏已启动 ({selected_device})", "success")
                        # 等待进程结束
                        process.wait()
                        if process in self.controller.active_subprocesses:
                            self.controller.active_subprocesses.remove(process)
                    except Exception as e:
                        print(f"启动scrcpy失败: {e}")
                        self.controller.show_toast(f"启动失败: {str(e)}", "error")

                threading.Thread(target=run_scrcpy, daemon=True).start()
                popup.destroy()

            except Exception as e:
                self.controller.show_toast(f"启动失败: {str(e)}", "error")

        start_button = ctk.CTkButton(
            popup,
            text="启动投屏",
            font=("Microsoft YaHei", 14),
            height=40,
            width=120,
            fg_color="#9b59b6",
            command=start_scrcpy
        )
        start_button.pack(pady=20)

        # 提示信息
        info_label = ctk.CTkLabel(
            popup,
            text="注意：请确保手机已开启USB调试模式\n点击其他地方时窗口会自动最小化",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_SECONDARY
        )
        info_label.pack(pady=10)

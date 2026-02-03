"""
DashboardBuilder - 控制中心页面构建器
"""
import tkinter as tk
import customtkinter as ctk
from .theme import ThemeColors


class DashboardBuilder:
    """控制中心页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建控制中心页面（只执行一次）"""
        self.view._highlight_nav_button(0)

        content_frame = ctk.CTkFrame(self.view.content_pages[0], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 顶部标题
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="🏠 控制中心",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text="执行输出和命令控制中心",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))

        # 执行输出区域
        output_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        output_frame.pack(fill="both", expand=True, pady=(0, 20))

        # 标题行：执行输出标签 + 模拟回车按钮
        output_header_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_header_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            output_header_frame,
            text="执行输出:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(side="left")

        # 模拟回车按钮
        self.components["enter_button"] = ctk.CTkButton(
            output_header_frame,
            text="↵ 模拟回车",
            font=("Microsoft YaHei", 12),
            width=100,
            height=30,
            fg_color=ThemeColors.PRIMARY,
            hover_color="#3451b2",
            corner_radius=6
        )
        self.view.hide_enter_button()

        # 输出文本框
        self.components["output_text"] = ctk.CTkTextbox(
            output_frame,
            font=("Consolas", 13),
            activate_scrollbars=True,
            wrap="none"
        )
        self.components["output_text"].pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.components["output_text"].configure(state="disabled")

        # 命令输入区域
        input_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        input_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            input_frame,
            text="命令输入:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        # 输入框和附件区域容器
        input_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=15)

        # 第一行：输入框和"+"号按钮
        input_button_frame = ctk.CTkFrame(input_container, fg_color="transparent")
        input_button_frame.pack(fill="x")

        # "+"号按钮 - 用于上传文件
        self.components["attach_button"] = ctk.CTkButton(
            input_button_frame,
            text="+",
            font=("Microsoft YaHei", 16, "bold"),
            width=45,
            height=35,
            fg_color=ThemeColors.SECONDARY,
            hover_color="#5e35b1",
            corner_radius=8
        )
        self.components["attach_button"].pack(side="left", padx=(0, 10))

        # 命令输入框（可自适应高度的文本框）
        self.components["command_input"] = ctk.CTkTextbox(
            input_button_frame,
            font=("Microsoft YaHei", 13),
            height=35,
            width=500,
            wrap="word",
            activate_scrollbars=False
        )
        self.components["command_input"].pack(side="left", fill="x", expand=True)
        self.components["command_input"].bind("<KeyRelease>", self._on_input_keyrelease)

        # 已选文件显示区域（紧跟在输入框下方）
        self.components["attached_files_frame"] = ctk.CTkFrame(input_container, fg_color="transparent")
        self.components["attached_files_frame"].pack(fill="x", pady=(5, 0))
        self.components["attached_files_frame"].pack_forget()

        # 按钮区域
        self.components["button_frame"] = button_frame = ctk.CTkFrame(input_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        # 各功能按钮
        self.components["execute_button"] = ctk.CTkButton(
            button_frame,
            text="执行命令",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.PRIMARY
        )
        self.components["execute_button"].pack(side="left", padx=(0, 10))

        self.components["terminate_button"] = ctk.CTkButton(
            button_frame,
            text="终止操作",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.DANGER,
            hover_color="#c62828",
            state="disabled"
        )
        self.components["terminate_button"].pack(side="left", padx=(0, 10))

        self.components["tts_button"] = ctk.CTkButton(
            button_frame,
            text="语音播报",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.SECONDARY
        )
        self.components["tts_button"].pack(side="left", padx=(0, 10))

        self.components["clear_output_btn"] = ctk.CTkButton(
            button_frame,
            text="清空输出",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.ACCENT
        )
        self.components["clear_output_btn"].pack(side="left")

        self.components["scrcpy_button"] = ctk.CTkButton(
            button_frame,
            text="📱 手机投屏",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color="#9b59b6",
            hover_color="#8e44ad"
        )
        self.components["scrcpy_button"].pack(side="left", padx=(10, 0))

    def _on_input_keyrelease(self, event=None):
        """输入框内容变化时自适应高度"""
        text_widget = self.components.get("command_input")
        if not text_widget:
            return

        try:
            content = text_widget.get("1.0", "end-1c")
            if not content:
                text_widget.configure(height=35)
                return

            lines = content.count('\n') + 1
            line_height = 20
            current_height = min(lines * line_height + 10, 175)

            if current_height < 35:
                current_height = 35

            text_widget.configure(height=current_height)
        except Exception as e:
            pass

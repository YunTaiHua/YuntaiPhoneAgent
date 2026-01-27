"""
HistoryBuilder - 历史记录页面构建器
"""
import customtkinter as ctk
from .theme import ThemeColors


class HistoryBuilder:
    """历史记录页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建历史记录页面"""
        self.view._clear_content_card()
        self.view._highlight_nav_button(3)

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="📊 历史记录",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 30))

        # 工具栏
        toolbar = ctk.CTkFrame(content_frame, fg_color="transparent", height=40)
        toolbar.pack(fill="x", pady=(0, 20))

        self.components["refresh_history_btn"] = ctk.CTkButton(
            toolbar,
            text="刷新",
            font=("Microsoft YaHei", 14),
            width=80,
            height=30
        )
        self.components["refresh_history_btn"].pack(side="left", padx=(0, 10))

        self.components["clear_history_btn"] = ctk.CTkButton(
            toolbar,
            text="清空",
            font=("Microsoft YaHei", 14),
            width=80,
            height=30,
            fg_color=ThemeColors.DANGER,
            hover_color="#c62828"
        )
        self.components["clear_history_btn"].pack(side="left")

        # 历史记录显示区域
        history_frame = ctk.CTkFrame(content_frame, corner_radius=15)
        history_frame.pack(fill="both", expand=True)

        # 创建历史记录文本框
        self.components["history_text"] = ctk.CTkTextbox(
            history_frame,
            font=("Consolas", 13),
            activate_scrollbars=True
        )
        self.components["history_text"].pack(fill="both", expand=True, padx=10, pady=10)
        self.components["history_text"].configure(state="disabled")

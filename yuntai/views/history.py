"""
HistoryBuilder - 历史记录页面构建器
浅色米白色主题版本
"""
import customtkinter as ctk
from .theme import ThemeColors


class HistoryBuilder:
    """历史记录页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建历史记录页面（只执行一次）"""
        self.view._highlight_nav_button(3)

        content_frame = ctk.CTkFrame(
            self.view.content_pages[3],
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 标题卡片 - 居中对齐
        header_card = ctk.CTkFrame(
            content_frame,
            corner_radius=16,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        header_card.pack(fill="x", pady=(0, 20))

        header_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        header_inner.pack(expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            header_inner,
            text="历史记录",
            font=("Microsoft YaHei", 28, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            header_inner,
            text="查看和管理对话历史记录",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack()

        # 历史记录显示区域
        history_frame = ctk.CTkFrame(
            content_frame,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        history_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            history_frame,
            text="📋 历史记录列表",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=15)

        # 创建历史记录文本框
        self.components["history_text"] = ctk.CTkTextbox(
            history_frame,
            font=("Consolas", 13),
            activate_scrollbars=True,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_LIGHT,
            border_width=1,
            corner_radius=12
        )
        self.components["history_text"].pack(fill="both", expand=True, padx=15, pady=(0, 20))
        self.components["history_text"].configure(state="disabled")

        # 底部按钮区域 - 居中对齐
        button_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        # 创建居中容器
        button_center = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_center.pack()

        self.components["refresh_history_btn"] = ctk.CTkButton(
            button_center,
            text="🔄 刷新",
            font=("Microsoft YaHei", 14),
            width=100,
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.SECONDARY,
            hover_color=ThemeColors.SECONDARY_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["refresh_history_btn"].pack(side="left", padx=(0, 12))

        self.components["clear_history_btn"] = ctk.CTkButton(
            button_center,
            text="🗑️ 清空",
            font=("Microsoft YaHei", 14),
            width=100,
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.DANGER,
            hover_color=ThemeColors.DANGER_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["clear_history_btn"].pack(side="left")

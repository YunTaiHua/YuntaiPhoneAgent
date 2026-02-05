"""
SettingsBuilder - 系统设置页面构建器
浅色米白色主题版本
"""
import customtkinter as ctk
from .theme import ThemeColors


class SettingsBuilder:
    """系统设置页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建系统设置页面（只执行一次）"""
        self.view._highlight_nav_button(5)

        content_frame = ctk.CTkFrame(
            self.view.content_pages[5],
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
            text="系统设置",
            font=("Microsoft YaHei", 28, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            header_inner,
            text="配置系统各项参数",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack()

        # 创建设置卡片容器
        settings_grid = ctk.CTkFrame(
            content_frame,
            fg_color="transparent"
        )
        settings_grid.pack(fill="both", expand=True)

        # 设置选项
        settings = [
            ("连接配置", "🔗", ThemeColors.PRIMARY),
            ("系统检查", "🔍", ThemeColors.SUCCESS),
            ("TTS语音", "🎤", ThemeColors.SECONDARY),
            ("文件管理", "📁", ThemeColors.ACCENT),
        ]

        # 创建2x2网格
        for i, (title, icon, color) in enumerate(settings):
            row = i // 2
            col = i % 2

            # 创建卡片框架
            card = ctk.CTkFrame(
                settings_grid,
                corner_radius=12,
                fg_color=ThemeColors.BG_CARD,
                border_width=1,
                border_color=ThemeColors.BORDER_LIGHT
            )
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")

            # 卡片内容
            btn = ctk.CTkButton(
                card,
                text=f"{icon} {title}",
                font=("Microsoft YaHei", 18, "bold"),
                height=120,
                corner_radius=12,
                fg_color="transparent",
                hover_color=color,
                text_color=ThemeColors.TEXT_PRIMARY
            )
            btn.pack(fill="both", expand=True, padx=15, pady=15)
            self.components[f"settings_btn_{i}"] = btn

        # 配置网格权重
        settings_grid.grid_columnconfigure(0, weight=1)
        settings_grid.grid_columnconfigure(1, weight=1)
        settings_grid.grid_rowconfigure(0, weight=1)
        settings_grid.grid_rowconfigure(1, weight=1)

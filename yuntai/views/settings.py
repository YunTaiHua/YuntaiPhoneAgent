"""
SettingsBuilder - 系统设置页面构建器
"""
import customtkinter as ctk
from .theme import ThemeColors


class SettingsBuilder:
    """系统设置页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建系统设置页面"""
        self.view._clear_content_card()
        self.view._highlight_nav_button(4)

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="⚙️ 系统设置",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 30))

        # 创建设置卡片
        settings_grid = ctk.CTkFrame(content_frame, fg_color="transparent")
        settings_grid.pack(fill="both", expand=True)

        # 设置选项
        settings = [
            ("连接配置", "🔗"),
            ("系统检查", "🔍"),
            ("TTS语音", "🎤"),
            ("文件管理", "📁"),
        ]

        # 创建2x2网格
        for i, (title, icon) in enumerate(settings):
            row = i // 2
            col = i % 2

            btn = ctk.CTkButton(
                settings_grid,
                text=f"{icon} {title}",
                font=("Microsoft YaHei", 16),
                height=100,
                corner_radius=12,
                fg_color=ThemeColors.BG_HOVER,
                hover_color=ThemeColors.PRIMARY
            )
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.components[f"settings_btn_{i}"] = btn

        # 配置网格权重
        settings_grid.grid_columnconfigure(0, weight=1)
        settings_grid.grid_columnconfigure(1, weight=1)
        settings_grid.grid_rowconfigure(0, weight=1)
        settings_grid.grid_rowconfigure(1, weight=1)

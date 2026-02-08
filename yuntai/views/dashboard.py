"""
DashboardBuilder - 控制中心页面构建器
浅色米白色主题版本
"""
import tkinter as tk
import customtkinter as ctk
from .theme import ThemeColors


class DashboardBuilder:
    """控制中心页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components
        self._last_line_count = 1  # 跟踪上一次行数

        # 快捷键配置
        self.shortcuts = {
            'w': ('打开微信', '💬'),
            'q': ('打开QQ', '🐧'),
            'd': ('打开抖音', '🎵'),
            'k': ('打开快手', '🎬'),
            't': ('打开淘宝', '🛒'),
            'm': ('打开QQ音乐', '🎶')
        }

    def create_page(self):
        """创建控制中心页面（只执行一次）"""
        self.view._highlight_nav_button(0)

        content_frame = ctk.CTkFrame(
            self.view.content_pages[0],
            fg_color="transparent"
        )
        content_frame.pack(fill="both", expand=True, padx=25, pady=25)

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
            text="控制中心",
            font=("Microsoft YaHei", 28, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            header_inner,
            text="执行输出和命令控制中心",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack()

        # 主内容区域 - 左右两列布局
        main_content = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_content.pack(fill="both", expand=True)

        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=3)
        main_content.grid_columnconfigure(1, weight=1)

        # 左侧：执行输出区域
        output_container = ctk.CTkFrame(main_content, fg_color="transparent")
        output_container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # 执行输出卡片
        output_frame = ctk.CTkFrame(
            output_container,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        output_frame.pack(fill="both", expand=True, pady=(0, 16))
        self.components["output_frame"] = output_frame

        # 标题行：执行输出标签 + 模拟回车按钮
        output_header_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        output_header_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            output_header_frame,
            text="📋 执行输出",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(side="left")

        # 模拟回车按钮
        self.components["enter_button"] = ctk.CTkButton(
            output_header_frame,
            text="↵ 模拟回车",
            font=("Microsoft YaHei", 12),
            width=100,
            height=36,
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            corner_radius=18,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.view.hide_enter_button()

        # 输出文本框
        self.components["output_text"] = ctk.CTkTextbox(
            output_frame,
            font=("Consolas", 13),
            activate_scrollbars=True,
            wrap="none",
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT,
            corner_radius=12
        )
        self.components["output_text"].pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.components["output_text"].configure(state="disabled")

        # 命令输入区域
        input_frame = ctk.CTkFrame(
            output_container,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        input_frame.pack(fill="x")
        self.components["input_frame"] = input_frame

        ctk.CTkLabel(
            input_frame,
            text="💬 命令输入",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=15)

        # 输入框和附件区域容器
        input_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=20, pady=(0, 15))

        # 命令输入框
        self.components["command_input"] = ctk.CTkTextbox(
            input_container,
            font=("Microsoft YaHei", 13),
            height=42,
            wrap="word",
            activate_scrollbars=False,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_width=2,
            border_color=ThemeColors.BORDER_LIGHT,
            corner_radius=12
        )
        self.components["command_input"].pack(fill="x")
        self.components["command_input"].bind("<KeyRelease>", self._on_input_keyrelease)

        # 已选文件显示区域（输入框下方）
        self.components["attached_files_frame"] = ctk.CTkFrame(
            input_container,
            fg_color="transparent"
        )
        self.components["attached_files_frame"].pack(fill="x", pady=(10, 0))
        self.components["attached_files_frame"].pack_forget()

        # 按钮区域
        button_frame = ctk.CTkFrame(
            input_container,
            fg_color="transparent"
        )
        button_frame.pack(fill="x", pady=(15, 0))

        # 各功能按钮
        self.components["execute_button"] = ctk.CTkButton(
            button_frame,
            text="▶ 执行命令",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            corner_radius=20,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["execute_button"].pack(side="left", padx=(0, 10))

        self.components["terminate_button"] = ctk.CTkButton(
            button_frame,
            text="⏹ 终止",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.DANGER,
            hover_color=ThemeColors.DANGER_HOVER,
            corner_radius=20,
            text_color=ThemeColors.TEXT_LIGHT,
            state="disabled"
        )
        self.components["terminate_button"].pack(side="left", padx=(0, 10))

        self.components["tts_button"] = ctk.CTkButton(
            button_frame,
            text="🔊 语音播报",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.SECONDARY,
            hover_color=ThemeColors.SECONDARY_HOVER,
            corner_radius=20,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["tts_button"].pack(side="left", padx=(0, 10))

        self.components["clear_output_btn"] = ctk.CTkButton(
            button_frame,
            text="🗑 清空",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.ACCENT,
            hover_color=ThemeColors.ACCENT_HOVER,
            corner_radius=20,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["clear_output_btn"].pack(side="left")

        self.components["scrcpy_button"] = ctk.CTkButton(
            button_frame,
            text="📱 手机投屏",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.SECONDARY,
            hover_color=ThemeColors.SECONDARY_HOVER,
            corner_radius=20,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["scrcpy_button"].pack(side="left", padx=(10, 0))

        # 右侧：快捷键、已选文件和文件管理卡片
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right_panel.grid_rowconfigure(0, weight=0)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_rowconfigure(2, weight=0)
        right_panel.grid_columnconfigure(0, weight=1)

        # 快捷键卡片（固定高度）- 放在最上面
        shortcuts_card = ctk.CTkFrame(
            right_panel,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        shortcuts_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.components["shortcuts_card"] = shortcuts_card

        ctk.CTkLabel(
            shortcuts_card,
            text="⚡ 快捷键",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 15))

        # 快捷键按钮网格
        shortcuts_grid = ctk.CTkFrame(shortcuts_card, fg_color="transparent")
        shortcuts_grid.pack(fill="x", padx=15, pady=(0, 15))

        shortcuts_grid.grid_columnconfigure(0, weight=1)
        shortcuts_grid.grid_columnconfigure(1, weight=1)

        row, col = 0, 0
        for key, (app_name, icon) in self.shortcuts.items():
            btn = ctk.CTkButton(
                shortcuts_grid,
                text=f"{icon} {app_name}",
                font=("Microsoft YaHei", 13),
                height=45,
                fg_color=ThemeColors.BG_HOVER,
                hover_color=ThemeColors.PRIMARY,
                corner_radius=12,
                text_color=ThemeColors.TEXT_PRIMARY
            )
            btn.grid(row=row, column=col, sticky="ew", padx=4, pady=4)
            self.components[f"shortcut_btn_{key}"] = btn

            col += 1
            if col > 1:
                col = 0
                row += 1

        # 文件展示卡片（可扩展高度）- 放在中间
        file_display_card = ctk.CTkFrame(
            right_panel,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        file_display_card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        self.components["file_display_card"] = file_display_card

        ctk.CTkLabel(
            file_display_card,
            text="📎 已选文件",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # 创建可滚动的文件列表
        files_scroll_frame = ctk.CTkScrollableFrame(
            file_display_card,
            label_text="",
            fg_color="transparent",
            scrollbar_button_color=ThemeColors.BG_HOVER,
            scrollbar_button_hover_color=ThemeColors.PRIMARY
        )
        files_scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.components["files_list_scroll_frame"] = files_scroll_frame

        # 文件管理卡片（固定高度）- 放在最下面
        file_management_card = ctk.CTkFrame(
            right_panel,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        file_management_card.grid(row=2, column=0, sticky="ew")
        self.components["file_management_card"] = file_management_card

        ctk.CTkLabel(
            file_management_card,
            text="📁 文件管理",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # 上传文件按钮
        self.components["file_upload_button"] = ctk.CTkButton(
            file_management_card,
            text="📤 上传文件",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            corner_radius=20,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["file_upload_button"].pack(fill="x", padx=15, pady=(0, 15))

        # 初始化已选文件显示区域
        self._init_attached_files_display()

    def _on_input_keyrelease(self, event=None):
        """输入框内容变化时自适应高度（只在换行时重新计算）"""
        text_widget = self.components.get("command_input")
        if not text_widget:
            return

        try:
            content = text_widget.get("1.0", "end-1c")

            current_line_count = content.count('\n') + 1 if content else 1

            if not content:
                if self._last_line_count == 1:
                    return
                text_widget.configure(height=42)
                self._last_line_count = 1
                return

            if current_line_count == self._last_line_count:
                return

            self._last_line_count = current_line_count

            line_height = 20
            current_height = min(current_line_count * line_height + 15, 175)

            if current_height < 42:
                current_height = 42

            text_widget.configure(height=current_height)
        except Exception as e:
            pass

    def _init_attached_files_display(self):
        """初始化已选文件显示区域"""
        if hasattr(self.view, 'show_attached_files'):
            self.view.show_attached_files([], None)

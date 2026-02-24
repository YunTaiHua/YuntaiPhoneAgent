"""
DynamicBuilder - 动态功能页面构建器
浅色米白色主题版本 - 左右分栏布局
"""
import tkinter as tk
import customtkinter as ctk
from .theme import ThemeColors


class DynamicBuilder:
    """动态功能页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self):
        """创建动态功能页面（只执行一次）"""
        self.view._highlight_nav_button(4)

        content_frame = ctk.CTkFrame(
            self.view.content_pages[4],
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
            text="动态功能",
            font=("Microsoft YaHei", 28, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            header_inner,
            text="图像生成与视频合成",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack()

        # 创建选项卡 - 现代化样式
        self.components["dynamic_tabview"] = ctk.CTkTabview(
            content_frame,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            segmented_button_fg_color=ThemeColors.BG_CARD_ALT,
            segmented_button_selected_color=ThemeColors.PRIMARY,
            segmented_button_selected_hover_color=ThemeColors.PRIMARY_HOVER,
            segmented_button_unselected_color=ThemeColors.BG_INPUT,
            segmented_button_unselected_hover_color=ThemeColors.BG_HOVER,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        self.components["dynamic_tabview"].pack(fill="both", expand=True)

        # 添加选项卡
        self.components["dynamic_tabview"].add("🖼️ 图像生成")
        self.components["dynamic_tabview"].add("🎬 视频生成")

        # 确保组件字典中有这两个选项卡的引用
        self.components["image_tab"] = self.components["dynamic_tabview"].tab("🖼️ 图像生成")
        self.components["video_tab"] = self.components["dynamic_tabview"].tab("🎬 视频生成")

        # 创建图像生成选项卡内容
        self._create_image_generation_tab(self.components["image_tab"])

        # 创建视频生成选项卡内容
        self._create_video_generation_tab(self.components["video_tab"])

    def _create_image_generation_tab(self, parent):
        """创建图像生成选项卡 - 左右分栏布局"""
        # 创建主容器，使用grid布局实现左右分栏
        main_container = ctk.CTkFrame(parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=3)  # 左侧占3份
        main_container.grid_columnconfigure(1, weight=2)  # 右侧占2份
        main_container.grid_rowconfigure(0, weight=1)

        # 左侧：描述输入和参数设置
        left_frame = ctk.CTkFrame(
            main_container,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 左侧内容容器
        left_content = ctk.CTkFrame(left_frame, fg_color="transparent")
        left_content.pack(fill="both", expand=True, padx=20, pady=20)

        # 提示词输入 - 加高到200
        ctk.CTkLabel(
            left_content,
            text="📝 图像描述",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 12))

        self.components["image_prompt_text"] = ctk.CTkTextbox(
            left_content,
            font=("Microsoft YaHei", 13),
            height=200,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["image_prompt_text"].pack(fill="x", pady=(0, 20))

        # 参数设置框架
        params_frame = ctk.CTkFrame(
            left_content, 
            fg_color=ThemeColors.BG_CARD_ALT,
            corner_radius=12
        )
        params_frame.pack(fill="x", pady=(0, 20))

        # 尺寸选择
        size_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        size_frame.pack(fill="x", padx=15, pady=(15, 12))

        ctk.CTkLabel(
            size_frame,
            text="📐 图像尺寸",
            font=("Microsoft YaHei", 13),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(side="left", padx=(0, 15))

        self.components["image_size_var"] = ctk.StringVar(value="1280x1280")
        self.components["image_size_menu"] = ctk.CTkOptionMenu(
            size_frame,
            variable=self.components["image_size_var"],
            values=["1280x1280", "1024x1024", "1024x768", "768x1024", "1920x1080", "1080x1920"],
            font=("Microsoft YaHei", 12),
            width=150,
            height=38,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.OPTION_BUTTON_COLOR,
            button_hover_color=ThemeColors.OPTION_BUTTON_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.components["image_size_menu"].pack(side="left")

        # 质量选择
        quality_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        quality_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            quality_frame,
            text="✨ 图像质量",
            font=("Microsoft YaHei", 13),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(side="left", padx=(0, 15))

        self.components["image_quality_var"] = ctk.StringVar(value="standard")
        self.components["image_quality_menu"] = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.components["image_quality_var"],
            values=["standard", "hd"],
            font=("Microsoft YaHei", 12),
            width=150,
            height=38,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.OPTION_BUTTON_COLOR,
            button_hover_color=ThemeColors.OPTION_BUTTON_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.components["image_quality_menu"].pack(side="left")

        # 按钮区域
        button_frame = ctk.CTkFrame(left_content, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        self.components["generate_image_btn"] = ctk.CTkButton(
            button_frame,
            text="🖼️ 生成图像",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["generate_image_btn"].pack(side="left", padx=(0, 12))

        self.components["preview_image_btn"] = ctk.CTkButton(
            button_frame,
            text="👁️ 预览",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.SECONDARY,
            hover_color=ThemeColors.SECONDARY_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["preview_image_btn"].pack(side="left")

        # 右侧：日志输出区域
        right_frame = ctk.CTkFrame(
            main_container,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # 日志内容容器
        log_content = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_content.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            log_content,
            text="📋 生成日志",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 12))

        self.components["image_log_text"] = ctk.CTkTextbox(
            log_content,
            font=("Consolas", 11),
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_LIGHT,
            border_width=1
        )
        self.components["image_log_text"].pack(fill="both", expand=True)
        self.components["image_log_text"].configure(state="disabled")

    def _create_video_generation_tab(self, parent):
        """创建视频生成选项卡 - 左右分栏布局"""
        # 创建主容器，使用grid布局实现左右分栏
        main_container = ctk.CTkFrame(parent, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=3)  # 左侧占3份
        main_container.grid_columnconfigure(1, weight=2)  # 右侧占2份
        main_container.grid_rowconfigure(0, weight=1)

        # 左侧：描述输入、URL输入和参数设置
        left_frame = ctk.CTkFrame(
            main_container,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 左侧内容容器
        left_content = ctk.CTkFrame(left_frame, fg_color="transparent")
        left_content.pack(fill="both", expand=True, padx=20, pady=20)

        # 提示词输入 - 加高到180
        ctk.CTkLabel(
            left_content,
            text="📝 视频描述",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 12))

        self.components["video_prompt_text"] = ctk.CTkTextbox(
            left_content,
            font=("Microsoft YaHei", 13),
            height=180,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["video_prompt_text"].pack(fill="x", pady=(0, 15))

        # 图片URL输入区域
        ctk.CTkLabel(
            left_content,
            text="🖼️ 参考图片URL (可选，最多2个)",
            font=("Microsoft YaHei", 14, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 10))

        # URL输入框1
        url_frame1 = ctk.CTkFrame(left_content, fg_color="transparent")
        url_frame1.pack(fill="x", pady=(0, 8))

        self.components["image_url1_entry"] = ctk.CTkEntry(
            url_frame1,
            placeholder_text="图片URL 1 - 必须是公开可访问的HTTP/HTTPS链接",
            font=("Microsoft YaHei", 12),
            height=38,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["image_url1_entry"].pack(fill="x")

        # URL输入框2
        url_frame2 = ctk.CTkFrame(left_content, fg_color="transparent")
        url_frame2.pack(fill="x", pady=(0, 15))

        self.components["image_url2_entry"] = ctk.CTkEntry(
            url_frame2,
            placeholder_text="图片URL 2 - 双图生成时建议图片尺寸一致",
            font=("Microsoft YaHei", 12),
            height=38,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_MEDIUM,
            border_width=1
        )
        self.components["image_url2_entry"].pack(fill="x")

        # 参数设置框架
        params_frame = ctk.CTkFrame(
            left_content, 
            fg_color=ThemeColors.BG_CARD_ALT,
            corner_radius=12
        )
        params_frame.pack(fill="x", pady=(0, 15))

        # 参数行
        row1 = ctk.CTkFrame(params_frame, fg_color="transparent")
        row1.pack(fill="x", padx=15, pady=(15, 12))

        # 尺寸选择
        size_label = ctk.CTkLabel(
            row1,
            text="📐 尺寸",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_PRIMARY
        )
        size_label.pack(side="left", padx=(0, 10))

        self.components["video_size_var"] = ctk.StringVar(value="1920x1080")
        self.components["video_size_menu"] = ctk.CTkOptionMenu(
            row1,
            variable=self.components["video_size_var"],
            values=["1920x1080", "1080x1920", "1280x720", "720x1280", "1024x1024"],
            font=("Microsoft YaHei", 11),
            width=120,
            height=34,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.OPTION_BUTTON_COLOR,
            button_hover_color=ThemeColors.OPTION_BUTTON_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.components["video_size_menu"].pack(side="left", padx=(0, 15))

        # 帧率选择
        fps_label = ctk.CTkLabel(
            row1,
            text="🎞️ 帧率",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_PRIMARY
        )
        fps_label.pack(side="left", padx=(0, 10))

        self.components["video_fps_var"] = ctk.StringVar(value="30")
        self.components["video_fps_menu"] = ctk.CTkOptionMenu(
            row1,
            variable=self.components["video_fps_var"],
            values=["30", "60"],
            font=("Microsoft YaHei", 11),
            width=80,
            height=34,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.OPTION_BUTTON_COLOR,
            button_hover_color=ThemeColors.OPTION_BUTTON_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.components["video_fps_menu"].pack(side="left", padx=(0, 15))

        # 质量选择
        quality_label = ctk.CTkLabel(
            row1,
            text="✨ 质量",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_PRIMARY
        )
        quality_label.pack(side="left", padx=(0, 10))

        self.components["video_quality_var"] = ctk.StringVar(value="quality")
        self.components["video_quality_menu"] = ctk.CTkOptionMenu(
            row1,
            variable=self.components["video_quality_var"],
            values=["quality", "speed"],
            font=("Microsoft YaHei", 11),
            width=100,
            height=34,
            corner_radius=12,
            fg_color=ThemeColors.BG_INPUT,
            button_color=ThemeColors.OPTION_BUTTON_COLOR,
            button_hover_color=ThemeColors.OPTION_BUTTON_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.components["video_quality_menu"].pack(side="left", padx=(0, 15))

        # 音效开关
        self.components["video_audio_var"] = ctk.BooleanVar(value=True)
        self.components["video_audio_check"] = ctk.CTkCheckBox(
            row1,
            text="🔊 生成音效",
            variable=self.components["video_audio_var"],
            font=("Microsoft YaHei", 12),
            fg_color=ThemeColors.PRIMARY,
            hover_color=ThemeColors.PRIMARY_HOVER,
            text_color=ThemeColors.TEXT_PRIMARY
        )
        self.components["video_audio_check"].pack(side="left")

        # 按钮区域
        button_frame = ctk.CTkFrame(left_content, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        self.components["generate_video_btn"] = ctk.CTkButton(
            button_frame,
            text="🎬 生成视频",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.ACCENT,
            hover_color=ThemeColors.ACCENT_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["generate_video_btn"].pack(side="left", padx=(0, 12))

        self.components["preview_video_btn"] = ctk.CTkButton(
            button_frame,
            text="👁️ 预览",
            font=("Microsoft YaHei", 14),
            height=40,
            corner_radius=20,
            fg_color=ThemeColors.WARNING,
            hover_color=ThemeColors.WARNING_HOVER,
            text_color=ThemeColors.TEXT_LIGHT
        )
        self.components["preview_video_btn"].pack(side="left")

        # 右侧：日志输出区域
        right_frame = ctk.CTkFrame(
            main_container,
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # 日志内容容器
        log_content = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_content.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            log_content,
            text="📋 生成日志",
            font=("Microsoft YaHei", 16, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 12))

        self.components["video_log_text"] = ctk.CTkTextbox(
            log_content,
            font=("Consolas", 11),
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD_ALT,
            text_color=ThemeColors.TEXT_PRIMARY,
            border_color=ThemeColors.BORDER_LIGHT,
            border_width=1
        )
        self.components["video_log_text"].pack(fill="both", expand=True)
        self.components["video_log_text"].configure(state="disabled")

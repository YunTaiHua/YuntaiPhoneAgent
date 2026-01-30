"""
DynamicBuilder - 动态功能页面构建器
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

        content_frame = ctk.CTkFrame(self.view.content_pages[4], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="🎨 动态功能",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            content_frame,
            text="图像生成与视频合成",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 30))

        # 创建选项卡
        self.components["dynamic_tabview"] = ctk.CTkTabview(content_frame)
        self.components["dynamic_tabview"].pack(fill="both", expand=True)

        # 添加选项卡
        self.components["dynamic_tabview"].add("图像生成")
        self.components["dynamic_tabview"].add("视频生成")

        # 确保组件字典中有这两个选项卡的引用
        self.components["image_tab"] = self.components["dynamic_tabview"].tab("图像生成")
        self.components["video_tab"] = self.components["dynamic_tabview"].tab("视频生成")

        # 创建图像生成选项卡内容
        self._create_image_generation_tab(self.components["image_tab"])

        # 创建视频生成选项卡内容
        self._create_video_generation_tab(self.components["video_tab"])

    def _create_image_generation_tab(self, parent):
        """创建图像生成选项卡"""
        # 主框架
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 提示词输入
        ctk.CTkLabel(
            main_frame,
            text="图像描述:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.components["image_prompt_text"] = ctk.CTkTextbox(
            main_frame,
            font=("Microsoft YaHei", 13),
            height=180
        )
        self.components["image_prompt_text"].pack(fill="x", pady=(0, 20))

        # 参数设置框架
        params_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        params_frame.pack(fill="x", pady=(0, 20))

        # 尺寸选择
        size_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        size_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            size_frame,
            text="图像尺寸:",
            font=("Microsoft YaHei", 13)
        ).pack(side="left", padx=(0, 10))

        self.components["image_size_var"] = ctk.StringVar(value="1280x1280")
        self.components["image_size_menu"] = ctk.CTkOptionMenu(
            size_frame,
            variable=self.components["image_size_var"],
            values=["1280x1280", "1024x1024", "1024x768", "768x1024", "1920x1080", "1080x1920"],
            font=("Microsoft YaHei", 12),
            width=150
        )
        self.components["image_size_menu"].pack(side="left")

        # 质量选择
        quality_frame = ctk.CTkFrame(params_frame, fg_color="transparent")
        quality_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            quality_frame,
            text="图像质量:",
            font=("Microsoft YaHei", 13)
        ).pack(side="left", padx=(0, 10))

        self.components["image_quality_var"] = ctk.StringVar(value="standard")
        self.components["image_quality_menu"] = ctk.CTkOptionMenu(
            quality_frame,
            variable=self.components["image_quality_var"],
            values=["standard", "hd"],
            font=("Microsoft YaHei", 12),
            width=150
        )
        self.components["image_quality_menu"].pack(side="left")

        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        self.components["generate_image_btn"] = ctk.CTkButton(
            button_frame,
            text="🖼️ 生成图像",
            font=("Microsoft YaHei", 14),
            height=45,
            fg_color=ThemeColors.PRIMARY
        )
        self.components["generate_image_btn"].pack(side="left", padx=(0, 10))

        self.components["preview_image_btn"] = ctk.CTkButton(
            button_frame,
            text="👁️ 预览图像",
            font=("Microsoft YaHei", 14),
            height=45,
            fg_color=ThemeColors.SECONDARY
        )
        self.components["preview_image_btn"].pack(side="left", padx=(0, 10))

        # 输出区域
        output_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        output_frame.pack(fill="both", expand=True, pady=(20, 0))

        ctk.CTkLabel(
            output_frame,
            text="生成日志:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        self.components["image_log_text"] = ctk.CTkTextbox(
            output_frame,
            font=("Consolas", 11),
            height=80
        )
        self.components["image_log_text"].pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.components["image_log_text"].configure(state="disabled")

    def _create_video_generation_tab(self, parent):
        """创建视频生成选项卡"""
        # 主框架
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 提示词输入
        ctk.CTkLabel(
            main_frame,
            text="视频描述:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.components["video_prompt_text"] = ctk.CTkTextbox(
            main_frame,
            font=("Microsoft YaHei", 13),
            height=150
        )
        self.components["video_prompt_text"].pack(fill="x", pady=(0, 20))

        # 图片URL输入区域
        ctk.CTkLabel(
            main_frame,
            text="参考图片URL (可选，最多2个):",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # URL输入框1
        url_frame1 = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_frame1.pack(fill="x", pady=(0, 10))

        self.components["image_url1_entry"] = ctk.CTkEntry(
            url_frame1,
            placeholder_text="💡 图片URL要求：1.必须是公开可访问的HTTP/HTTPS链接  2.支持格式：JPG, PNG, WebP等",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["image_url1_entry"].pack(fill="x", side="left", expand=True, padx=(0, 10))

        # URL输入框2
        url_frame2 = ctk.CTkFrame(main_frame, fg_color="transparent")
        url_frame2.pack(fill="x", pady=(0, 20))

        self.components["image_url2_entry"] = ctk.CTkEntry(
            url_frame2,
            placeholder_text="💡 双图URL要求：1.双图生成时，建议图片尺寸一致  2.首尾帧生成时，建议图片内容相关，否则生成结果有偏差",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["image_url2_entry"].pack(fill="x", side="left", expand=True, padx=(0, 10))

        # 参数设置框架
        params_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        params_frame.pack(fill="x", pady=(0, 20))

        # 参数行
        row1 = ctk.CTkFrame(params_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))

        # 尺寸选择
        size_label = ctk.CTkLabel(
            row1,
            text="视频尺寸:",
            font=("Microsoft YaHei", 13),
            width=80
        )
        size_label.pack(side="left", padx=(0, 10))

        self.components["video_size_var"] = ctk.StringVar(value="1920x1080")
        self.components["video_size_menu"] = ctk.CTkOptionMenu(
            row1,
            variable=self.components["video_size_var"],
            values=["1920x1080", "1080x1920", "1280x720", "720x1280", "1024x1024"],
            font=("Microsoft YaHei", 12),
            width=150
        )
        self.components["video_size_menu"].pack(side="left", padx=(0, 20))

        # 帧率选择
        fps_label = ctk.CTkLabel(
            row1,
            text="帧率:",
            font=("Microsoft YaHei", 13),
            width=50
        )
        fps_label.pack(side="left", padx=(0, 10))

        self.components["video_fps_var"] = ctk.StringVar(value="30")
        self.components["video_fps_menu"] = ctk.CTkOptionMenu(
            row1,
            variable=self.components["video_fps_var"],
            values=["30", "60"],
            font=("Microsoft YaHei", 12),
            width=100
        )
        self.components["video_fps_menu"].pack(side="left", padx=(0, 20))

        # 质量选择
        quality_label = ctk.CTkLabel(
            row1,
            text="生成质量:",
            font=("Microsoft YaHei", 13),
            width=80
        )
        quality_label.pack(side="left", padx=(0, 10))

        self.components["video_quality_var"] = ctk.StringVar(value="quality")
        self.components["video_quality_menu"] = ctk.CTkOptionMenu(
            row1,
            variable=self.components["video_quality_var"],
            values=["quality", "speed"],
            font=("Microsoft YaHei", 12),
            width=150
        )
        self.components["video_quality_menu"].pack(side="left", padx=(0, 20))

        # 音效开关
        self.components["video_audio_var"] = ctk.BooleanVar(value=True)
        self.components["video_audio_check"] = ctk.CTkCheckBox(
            row1,
            text="生成音效",
            variable=self.components["video_audio_var"],
            font=("Microsoft YaHei", 13)
        )
        self.components["video_audio_check"].pack(side="left")

        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        self.components["generate_video_btn"] = ctk.CTkButton(
            button_frame,
            text="🎬 生成视频",
            font=("Microsoft YaHei", 14),
            height=45,
            fg_color=ThemeColors.ACCENT
        )
        self.components["generate_video_btn"].pack(side="left", padx=(0, 20))

        self.components["preview_video_btn"] = ctk.CTkButton(
            button_frame,
            text="👁️ 预览视频",
            font=("Microsoft YaHei", 14),
            height=45,
            fg_color=ThemeColors.WARNING
        )
        self.components["preview_video_btn"].pack(side="left")

        # 输出区域
        output_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        output_frame.pack(fill="both", expand=True, pady=(10, 0))

        ctk.CTkLabel(
            output_frame,
            text="生成日志:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        self.components["video_log_text"] = ctk.CTkTextbox(
            output_frame,
            font=("Consolas", 11),
            height=350
        )
        self.components["video_log_text"].pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.components["video_log_text"].configure(state="disabled")

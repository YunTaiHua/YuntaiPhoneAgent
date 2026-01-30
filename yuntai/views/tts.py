"""
TTSBuilder - TTS语音合成页面构建器
"""
import tkinter as tk
import customtkinter as ctk
from tkinter import Listbox, END
import tkinter.scrolledtext as scrolledtext
from .theme import ThemeColors


class TTSBuilder:
    """TTS语音合成页面构建器"""

    def __init__(self, view_instance):
        self.view = view_instance
        self.components = view_instance.components

    def create_page(self, tts_manager):
        """创建TTS语音合成页面"""
        self.view._highlight_nav_button(1)

        content_frame = ctk.CTkFrame(self.view.content_pages[1], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="🎤 TTS语音合成",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            content_frame,
            text="配置本地语音合成与播报",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 30))

        # 创建主内容区域
        main_content = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_content.pack(fill="both", expand=True)
        main_content.grid_columnconfigure(0, weight=3)
        main_content.grid_columnconfigure(1, weight=1)
        main_content.grid_rowconfigure(0, weight=1)

        # 左侧：模型配置和合成区域
        left_frame = ctk.CTkFrame(main_content, corner_radius=15)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)

        # 模型配置部分
        config_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        config_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            config_frame,
            text="模型与音频配置",
            font=("Microsoft YaHei", 16, "bold")
        ).pack(anchor="w", pady=(0, 20))

        # 模型选择表单
        self._create_tts_form(config_frame, tts_manager)

        # 合成文本区域
        synth_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        synth_frame.pack(fill="x", pady=(20, 10))

        ctk.CTkLabel(
            synth_frame,
            text="合成文本:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.components["tts_text_input"] = ctk.CTkTextbox(
            synth_frame,
            font=("Microsoft YaHei", 13),
            height=100
        )
        self.components["tts_text_input"].pack(fill="x", pady=(0, 10))

        # 功能按钮区域
        button_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        self.components["tts_synth_btn"] = ctk.CTkButton(
            button_frame,
            text="执行合成",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.PRIMARY
        )
        self.components["tts_synth_btn"].pack(side="left", padx=(0, 10))

        self.components["tts_load_btn"] = ctk.CTkButton(
            button_frame,
            text="加载模型",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.SUCCESS
        )
        self.components["tts_load_btn"].pack(side="left", padx=(0, 10))

        self.components["tts_stop_btn"] = ctk.CTkButton(
            button_frame,
            text="停止播放",
            font=("Microsoft YaHei", 14),
            height=40,
            fg_color=ThemeColors.DANGER
        )
        self.components["tts_stop_btn"].pack(side="left")

        # 右侧：执行输出和历史音频
        right_frame = ctk.CTkFrame(main_content, corner_radius=15)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)

        # 执行输出区域
        log_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            log_frame,
            text="执行输出:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # 创建日志文本框
        self.components["tts_log_text"] = scrolledtext.ScrolledText(
            log_frame,
            wrap="word",
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="white",
            height=15,
            width=40,
            undo=True
        )
        self.components["tts_log_text"].pack(fill="both", expand=True, pady=(0, 10))
        self.components["tts_log_text"].config(state="disabled")

        # 历史音频列表
        audio_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
        audio_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            audio_frame,
            text="历史合成音频:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # 创建音频列表
        self.components["tts_audio_listbox"] = Listbox(
            audio_frame,
            font=("Microsoft YaHei", 12),
            bg="#1e1e1e",
            fg="white",
            height=8
        )
        self.components["tts_audio_listbox"].pack(fill="x", pady=(0, 10))

        # 音频列表按钮
        audio_btn_frame = ctk.CTkFrame(audio_frame, fg_color="transparent")
        audio_btn_frame.pack(fill="x")

        self.components["tts_play_btn"] = ctk.CTkButton(
            audio_btn_frame,
            text="播放选中",
            font=("Microsoft YaHei", 12),
            height=35
        )
        self.components["tts_play_btn"].pack(side="left", padx=(0, 10))

        self.components["tts_refresh_btn"] = ctk.CTkButton(
            audio_btn_frame,
            text="刷新列表",
            font=("Microsoft YaHei", 12),
            height=35
        )
        self.components["tts_refresh_btn"].pack(side="left", padx=(0, 10))

        self.components["tts_delete_btn"] = ctk.CTkButton(
            audio_btn_frame,
            text="删除历史音频",
            font=("Microsoft YaHei", 12),
            height=35,
            fg_color=ThemeColors.DANGER,
            hover_color="#c62828"
        )
        self.components["tts_delete_btn"].pack(side="left")

    def _create_tts_form(self, parent, tts_manager):
        """创建TTS配置表单"""
        # GPT模型选择
        gpt_frame = ctk.CTkFrame(parent, fg_color="transparent")
        gpt_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            gpt_frame,
            text="GPT模型:",
            font=("Microsoft YaHei", 13)
        ).pack(side="left", padx=(0, 10))

        self.components["tts_gpt_var"] = ctk.StringVar(value="未选择")
        self.components["tts_gpt_label"] = ctk.CTkLabel(
            gpt_frame,
            textvariable=self.components["tts_gpt_var"],
            font=("Microsoft YaHei", 13),
            width=180,
            anchor="w"
        )
        self.components["tts_gpt_label"].pack(side="left", padx=(0, 10))

        self.components["tts_select_gpt_btn"] = ctk.CTkButton(
            gpt_frame,
            text="选择",
            font=("Microsoft YaHei", 13),
            width=80,
            height=35
        )
        self.components["tts_select_gpt_btn"].pack(side="left")

        # SoVITS模型选择
        sovits_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sovits_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            sovits_frame,
            text="SoVITS模型:",
            font=("Microsoft YaHei", 13)
        ).pack(side="left", padx=(0, 10))

        self.components["tts_sovits_var"] = ctk.StringVar(value="未选择")
        self.components["tts_sovits_label"] = ctk.CTkLabel(
            sovits_frame,
            textvariable=self.components["tts_sovits_var"],
            font=("Microsoft YaHei", 13),
            width=160,
            anchor="w"
        )
        self.components["tts_sovits_label"].pack(side="left", padx=(0, 10))

        self.components["tts_select_sovits_btn"] = ctk.CTkButton(
            sovits_frame,
            text="选择",
            font=("Microsoft YaHei", 13),
            width=80,
            height=35
        )
        self.components["tts_select_sovits_btn"].pack(side="left")

        # 参考音频选择
        audio_frame = ctk.CTkFrame(parent, fg_color="transparent")
        audio_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            audio_frame,
            text="参考音频:",
            font=("Microsoft YaHei", 13)
        ).pack(side="left", padx=(0, 10))

        self.components["tts_audio_var"] = ctk.StringVar(value="未选择")
        self.components["tts_audio_label"] = ctk.CTkLabel(
            audio_frame,
            textvariable=self.components["tts_audio_var"],
            font=("Microsoft YaHei", 13),
            width=180,
            anchor="w"
        )
        self.components["tts_audio_label"].pack(side="left", padx=(0, 10))

        self.components["tts_select_audio_btn"] = ctk.CTkButton(
            audio_frame,
            text="选择",
            font=("Microsoft YaHei", 13),
            width=80,
            height=35
        )
        self.components["tts_select_audio_btn"].pack(side="left")

        # 参考文本选择
        text_frame = ctk.CTkFrame(parent, fg_color="transparent")
        text_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            text_frame,
            text="参考文本:",
            font=("Microsoft YaHei", 13)
        ).pack(side="left", padx=(0, 10))

        self.components["tts_text_var"] = ctk.StringVar(value="未选择")
        self.components["tts_text_label"] = ctk.CTkLabel(
            text_frame,
            textvariable=self.components["tts_text_var"],
            font=("Microsoft YaHei", 13),
            width=180,
            anchor="w"
        )
        self.components["tts_text_label"].pack(side="left", padx=(0, 10))

        self.components["tts_select_text_btn"] = ctk.CTkButton(
            text_frame,
            text="选择",
            font=("Microsoft YaHei", 13),
            width=80,
            height=35
        )
        self.components["tts_select_text_btn"].pack(side="left")

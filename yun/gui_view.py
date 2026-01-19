"""
GUIView - 纯界面构建模块
负责所有UI组件的创建和布局，不包含业务逻辑
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import scrolledtext, Listbox, END
import os


class ThemeColors:
    """现代化UI主题颜色类"""
    PRIMARY = "#4361ee"
    SECONDARY = "#7209b7"
    ACCENT = "#f72585"
    SUCCESS = "#4cc9f0"
    WARNING = "#f8961e"
    DANGER = "#e63946"
    BG_DARK = "#121212"
    BG_CARD = "#1e1e1e"
    BG_HOVER = "#2d2d2d"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_DISABLED = "#666666"


class GUIView:
    """纯界面构建类，只负责UI创建"""

    def __init__(self, root):
        self.root = root
        self.root.title("Phone Agent - 智能移动助手 v1.2.4")
        self.root.geometry("1400x900")

        # 存储UI组件引用
        self.components = {}

        # 设置外观
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 创建界面
        self._setup_main_layout()

    def _setup_main_layout(self):
        """设置主布局"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # 创建导航栏
        self._create_navigation_frame()

        # 创建主内容区
        self._create_main_content_frame()

        # 创建状态栏
        self._create_status_bar()

    def _create_navigation_frame(self):
        """创建左侧导航栏"""
        self.nav_frame = ctk.CTkFrame(self.root, width=240, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_propagate(False)

        # 应用标题
        title_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent", height=100)
        title_frame.pack(fill="x", padx=20, pady=(30, 20))

        ctk.CTkLabel(
            title_frame,
            text="📱",
            font=("Segoe UI Emoji", 40),
            text_color=ThemeColors.PRIMARY
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            title_frame,
            text="Phone Agent",
            font=("Microsoft YaHei", 24, "bold")
        ).pack()

        ctk.CTkLabel(
            title_frame,
            text="智能移动助手",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack()

        # 导航项目
        nav_items = [
            ("🏠 控制中心", "show_dashboard"),
            ("📱 设备管理", "show_connection_panel"),
            ("🎤 TTS语音", "show_tts_panel"),
            ("📊 历史记录", "show_history_panel"),
            ("🎨 动态功能", "show_dynamic_panel"),  # 新增
            ("⚙️ 系统设置", "show_settings_panel"),
        ]

        self.components["nav_buttons"] = []
        for text, _ in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=("Microsoft YaHei", 14),
                height=45,
                corner_radius=8,
                fg_color="transparent",
                hover_color=ThemeColors.BG_HOVER,
                anchor="w"
            )
            btn.pack(fill="x", padx=15, pady=5)
            self.components["nav_buttons"].append(btn)

        # 底部信息
        info_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        info_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        # 连接状态指示器
        self.components["connection_indicator"] = ctk.CTkLabel(
            info_frame,
            text="● 未连接",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.DANGER
        )
        self.components["connection_indicator"].pack(anchor="w")

        # TTS状态指示器
        self.components["tts_indicator"] = ctk.CTkLabel(
            info_frame,
            text="● TTS: 关闭",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.WARNING
        )
        self.components["tts_indicator"].pack(anchor="w", pady=(5, 0))

        # 版本信息
        ctk.CTkLabel(
            info_frame,
            text="Version 1.2.4",
            font=("Microsoft YaHei", 10),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(5, 0))

    def _create_main_content_frame(self):
        """创建主内容容器"""
        self.components["main_container"] = ctk.CTkFrame(self.root, fg_color="transparent")
        self.components["main_container"].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.components["main_container"].grid_rowconfigure(0, weight=1)
        self.components["main_container"].grid_columnconfigure(0, weight=1)

        # 创建卡片容器
        self.components["content_card"] = ctk.CTkFrame(
            self.components["main_container"],
            corner_radius=15,
            fg_color=ThemeColors.BG_CARD
        )
        self.components["content_card"].grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _create_status_bar(self):
        """创建底部状态栏"""
        self.components["status_bar"] = ctk.CTkFrame(self.root, height=30)
        self.components["status_bar"].grid(row=1, column=0, columnspan=2, sticky="ew")

        # 系统状态
        self.components["status_label"] = ctk.CTkLabel(
            self.components["status_bar"],
            text="系统已就绪",
            font=("Microsoft YaHei", 11)
        )
        self.components["status_label"].pack(side="left", padx=20)

    # ========== 页面创建方法 ==========

    def create_dashboard_page(self):
        """创建控制中心页面"""
        self._clear_content_card()
        self._highlight_nav_button(0)

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
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

        ctk.CTkLabel(
            output_frame,
            text="执行输出:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        # 输出文本框
        self.components["output_text"] = ctk.CTkTextbox(
            output_frame,
            font=("Consolas", 13),
            activate_scrollbars=True,
            height=400,
            wrap="none"
        )
        self.components["output_text"].pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.components["output_text"].configure(state="disabled")

        # 命令输入区域（修改现有代码）
        input_frame = ctk.CTkFrame(content_frame, corner_radius=10)
        input_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            input_frame,
            text="命令输入:",
            font=("Microsoft YaHei", 14, "bold")
        ).pack(anchor="w", padx=15, pady=10)

        # 命令输入框和"+"号按钮在同一行
        input_button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_button_frame.pack(fill="x", padx=15, pady=(0, 10))

        # "+"号按钮 - 用于上传文件
        self.components["attach_button"] = ctk.CTkButton(
            input_button_frame,
            text="+",
            font=("Microsoft YaHei", 16, "bold"),
            width=45,
            height=45,
            fg_color=ThemeColors.SECONDARY,
            hover_color="#5e35b1",
            corner_radius=8
        )
        self.components["attach_button"].pack(side="left", padx=(0, 10))

        # 命令输入框
        self.components["command_input"] = ctk.CTkEntry(
            input_button_frame,
            placeholder_text="输入命令或聊天内容，可点击'+'号添加图片/视频/文件...",
            font=("Microsoft YaHei", 13),
            height=45
        )
        self.components["command_input"].pack(side="left", fill="x", expand=True)

        # 已选文件显示区域
        self.components["attached_files_frame"] = ctk.CTkFrame(input_frame, fg_color="transparent")
        self.components["attached_files_frame"].pack(fill="x", padx=15, pady=(0, 10))

        # 默认隐藏已选文件区域
        self.components["attached_files_frame"].pack_forget()

        # 按钮区域
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

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
            hover_color="#c62828",  # 更深的红色作为悬停色
            state="disabled"  # 初始状态为禁用
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

    # 添加新方法：创建文件上传对话框
    def show_file_upload_dialog(self) -> list[str]:
        """显示文件上传对话框并返回选择的文件路径列表"""
        import tkinter.filedialog as fd

        filetypes = [
            ("所有支持的文件",
             "*.jpg *.jpeg *.png *.bmp *.webp "  # 图片
             "*.mp4 *.avi *.mov *.mkv *.wmv "  # 视频
             "*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma" #音频
             "*.txt *.py *.csv *.xls *.xlsx *.docx *.pdf *.ppt *.pptx *.html *.js "),  # 文件
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"),
            ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv"),
            ("音频文件","*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma"),
            ("文档文件", "*.txt *.py *.csv *.xls *.xlsx *.docx *.pdf *.ppt *.pptx *.html *.js "),
            ("所有文件", "*.*")
        ]

        files = fd.askopenfilenames(
            title="选择要上传的文件",
            filetypes=filetypes
        )

        return list(files)

    # 添加新方法：显示已选文件
    def show_attached_files(self, file_paths: list[str], controller=None):
        """在UI中显示已选择的文件"""
        # 获取组件
        attached_files_frame = self.get_component("attached_files_frame")
        if not attached_files_frame:
            print("⚠️  未找到attached_files_frame组件")
            return

        # 清空现有文件显示
        for widget in attached_files_frame.winfo_children():
            widget.destroy()

        if not file_paths:
            # 如果没有文件，隐藏该区域
            attached_files_frame.pack_forget()
            return

        # 显示文件区域
        attached_files_frame.pack(fill="x", padx=15, pady=(0, 10))

        # 标题
        ctk.CTkLabel(
            attached_files_frame,
            text="📎 已选文件:",
            font=("Microsoft YaHei", 12, "bold"),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 5))

        # 显示每个文件
        for i, file_path in enumerate(file_paths):
            file_frame = ctk.CTkFrame(attached_files_frame,
                                      fg_color=ThemeColors.BG_HOVER,
                                      height=35)
            file_frame.pack(fill="x", pady=2)

            # 文件名（带图标）
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower()

            # 根据文件类型选择图标
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                icon = "🖼️"
            elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
                icon = "🎬"
            elif ext in ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma']:
                icon = "🎵"
            elif ext == '.txt':
                icon = "📄"
            else:
                icon = "📎"

            file_label = ctk.CTkLabel(
                file_frame,
                text=f"{icon} {file_name}",
                font=("Microsoft YaHei", 11),
                anchor="w"
            )
            file_label.pack(side="left", fill="x", expand=True, padx=10)

            # 删除按钮（仅在controller存在时显示）
            if controller:
                delete_btn = ctk.CTkButton(
                    file_frame,
                    text="×",
                    font=("Microsoft YaHei", 12, "bold"),
                    width=30,
                    height=30,
                    fg_color=ThemeColors.DANGER,
                    hover_color="#c62828",
                    text_color="white"
                )
                delete_btn.pack(side="right", padx=5)

                # 绑定删除事件
                delete_btn.configure(
                    command=lambda f=file_path, c=controller: c.remove_attached_file(f)
                )

        # 清空所有按钮（仅在controller存在时显示）
        if controller:
            clear_all_btn = ctk.CTkButton(
                attached_files_frame,
                text="清空所有",
                font=("Microsoft YaHei", 11),
                height=30,
                fg_color=ThemeColors.WARNING,
                hover_color="#e67e22"
            )
            clear_all_btn.pack(anchor="e", pady=(5, 0))

            # 绑定清空所有事件
            clear_all_btn.configure(command=controller.clear_attached_files)
        else:
            # 如果没有controller，至少显示文件列表
            print("⚠️  show_attached_files未收到controller参数，文件操作为只读模式")

    # 添加新方法：移除单个文件
    def _remove_file(self, file_path: str, index: int):
        """从已选文件列表中移除文件"""
        # 这个方法需要在GUIController中实现
        pass

    # 在GUIView类中添加删除文件的方法
    def remove_attached_file(self, file_path: str, controller):
        """从UI中移除单个文件"""
        try:
            # 通知控制器移除文件
            controller.remove_attached_file(file_path)

            # 刷新显示
            controller.view.show_attached_files(controller.attached_files)
        except Exception as e:
            print(f"❌ 移除文件失败: {e}")

    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面"""
        self._clear_content_card()
        self._highlight_nav_button(2)

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="🎤 TTS语音合成",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # 检查TTS可用性
        if not hasattr(tts_manager, 'tts_available') or not tts_manager.tts_available:
            warning_frame = ctk.CTkFrame(content_frame, corner_radius=15, fg_color="#f39c12")
            warning_frame.pack(fill="x", pady=(0, 20))

            ctk.CTkLabel(
                warning_frame,
                text="⚠️ TTS功能可能不可用",
                font=("Microsoft YaHei", 16, "bold"),
                text_color="white"
            ).pack(padx=20, pady=10)

            ctk.CTkLabel(
                warning_frame,
                text="请确保GPT-SoVITS已正确安装并配置",
                font=("Microsoft YaHei", 12),
                text_color="white"
            ).pack(padx=20, pady=(0, 10))

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
        self.components["tts_stop_btn"].pack(side="left", padx=(0, 10))

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
        self.components["tts_log_text"] = scrolledtext.Text(
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

    def create_connection_page(self):
        """创建设备管理页面"""
        self._clear_content_card()
        self._highlight_nav_button(1)

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # 页面标题
        ctk.CTkLabel(
            content_frame,
            text="📱 设备管理",
            font=("Microsoft YaHei", 24, "bold")
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            content_frame,
            text="管理您的手机设备连接",
            font=("Microsoft YaHei", 14),
            text_color=ThemeColors.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 30))

        # 连接状态卡片
        self.components["status_card"] = ctk.CTkFrame(content_frame, corner_radius=15, height=100)
        self.components["status_card"].pack(fill="x", pady=(0, 30))

        status_inner = ctk.CTkFrame(self.components["status_card"], fg_color="transparent")
        status_inner.pack(expand=True, padx=30, pady=20)


        self.components["connection_status_label"] = ctk.CTkLabel(
            status_inner,
            text="● 未连接",
            font=("Microsoft YaHei", 24, "bold"),
            text_color=ThemeColors.DANGER
        )
        self.components["connection_status_label"].pack(anchor="w", pady=(0, 10))


        # 连接设置表单
        self._create_connection_form(content_frame)

    def create_history_page(self):
        """创建历史记录页面"""
        self._clear_content_card()
        self._highlight_nav_button(3)

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

    def create_settings_page(self):
        """创建系统设置页面"""
        self._clear_content_card()
        self._highlight_nav_button(4)

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


    # ========== 动态页面组件 ==========
    def create_dynamic_page(self):
        """创建动态功能页面"""
        self._clear_content_card()
        self._highlight_nav_button(5)  # 假设这是第6个按钮

        content_frame = ctk.CTkFrame(self.components["content_card"], fg_color="transparent")
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
            height=100
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
            height=150
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
            height=80
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

        # 第一行参数
        param_row1 = ctk.CTkFrame(params_frame, fg_color="transparent")
        param_row1.pack(fill="x", pady=(0, 15))

        # 尺寸选择
        size_label = ctk.CTkLabel(
            param_row1,
            text="视频尺寸:",
            font=("Microsoft YaHei", 13),
            width=80
        )
        size_label.pack(side="left", padx=(0, 10))

        self.components["video_size_var"] = ctk.StringVar(value="1920x1080")
        self.components["video_size_menu"] = ctk.CTkOptionMenu(
            param_row1,
            variable=self.components["video_size_var"],
            values=["1920x1080", "1080x1920", "1280x720", "720x1280", "1024x1024"],
            font=("Microsoft YaHei", 12),
            width=150
        )
        self.components["video_size_menu"].pack(side="left", padx=(0, 20))

        # 帧率选择
        fps_label = ctk.CTkLabel(
            param_row1,
            text="帧率:",
            font=("Microsoft YaHei", 13),
            width=50
        )
        fps_label.pack(side="left", padx=(0, 10))

        self.components["video_fps_var"] = ctk.StringVar(value="30")
        self.components["video_fps_menu"] = ctk.CTkOptionMenu(
            param_row1,
            variable=self.components["video_fps_var"],
            values=["30", "60"],
            font=("Microsoft YaHei", 12),
            width=100
        )
        self.components["video_fps_menu"].pack(side="left")

        # 第二行参数
        param_row2 = ctk.CTkFrame(params_frame, fg_color="transparent")
        param_row2.pack(fill="x", pady=(0, 15))

        # 质量选择
        quality_label = ctk.CTkLabel(
            param_row2,
            text="生成质量:",
            font=("Microsoft YaHei", 13),
            width=80
        )
        quality_label.pack(side="left", padx=(0, 10))

        self.components["video_quality_var"] = ctk.StringVar(value="quality")
        self.components["video_quality_menu"] = ctk.CTkOptionMenu(
            param_row2,
            variable=self.components["video_quality_var"],
            values=["quality", "speed"],
            font=("Microsoft YaHei", 12),
            width=150
        )
        self.components["video_quality_menu"].pack(side="left", padx=(0, 20))

        # 音效开关
        self.components["video_audio_var"] = ctk.BooleanVar(value=True)
        self.components["video_audio_check"] = ctk.CTkCheckBox(
            param_row2,
            text="生成音效",
            variable=self.components["video_audio_var"],
            font=("Microsoft YaHei", 13)
        )
        self.components["video_audio_check"].pack(side="left")

        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        self.components["generate_video_btn"] = ctk.CTkButton(
            button_frame,
            text="🎬 生成视频",
            font=("Microsoft YaHei", 14),
            height=45,
            fg_color=ThemeColors.ACCENT
        )
        self.components["generate_video_btn"].pack(side="left", padx=(0, 10))

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
        output_frame.pack(fill="both", expand=True, pady=(20, 0))

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

    # ========== 辅助方法 ==========

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

    def _create_connection_form(self, parent):
        """创建设备连接表单"""
        form_frame = ctk.CTkFrame(parent, corner_radius=15)
        form_frame.pack(fill="x", pady=(0, 20))

        # 表单标题
        ctk.CTkLabel(
            form_frame,
            text="设备连接设置",
            font=("Microsoft YaHei", 16, "bold")
        ).pack(anchor="w", padx=20, pady=20)

        # 连接方式选择
        conn_type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        conn_type_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            conn_type_frame,
            text="连接方式:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", pady=(0, 10))

        self.components["conn_var"] = ctk.StringVar(value="wireless")

        usb_option = ctk.CTkRadioButton(
            conn_type_frame,
            text="USB调试连接",
            variable=self.components["conn_var"],
            value="usb",
            font=("Microsoft YaHei", 13)
        )
        usb_option.pack(anchor="w", pady=5)

        wireless_option = ctk.CTkRadioButton(
            conn_type_frame,
            text="无线调试连接",
            variable=self.components["conn_var"],
            value="wireless",
            font=("Microsoft YaHei", 13)
        )
        wireless_option.pack(anchor="w", pady=5)

        # USB设置
        self.components["usb_frame"] = ctk.CTkFrame(form_frame, fg_color="transparent")

        ctk.CTkLabel(
            self.components["usb_frame"],
            text="USB设备ID:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.components["usb_entry"] = ctk.CTkEntry(
            self.components["usb_frame"],
            placeholder_text="通过 adb devices 查看",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["usb_entry"].pack(fill="x", padx=20, pady=(0, 10))

        # 无线设置
        self.components["wireless_frame"] = ctk.CTkFrame(form_frame, fg_color="transparent")

        # IP地址
        ctk.CTkLabel(
            self.components["wireless_frame"],
            text="IP地址:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.components["ip_entry"] = ctk.CTkEntry(
            self.components["wireless_frame"],
            placeholder_text="例如: 192.168.1.100",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["ip_entry"].pack(fill="x", padx=20, pady=(0, 10))

        # 端口
        ctk.CTkLabel(
            self.components["wireless_frame"],
            text="端口:",
            font=("Microsoft YaHei", 13)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.components["port_entry"] = ctk.CTkEntry(
            self.components["wireless_frame"],
            placeholder_text="默认: 5555",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["port_entry"].insert(0, "5555")
        self.components["port_entry"].pack(fill="x", padx=20)

        # 按钮区域
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        self.components["detect_devices_btn"] = ctk.CTkButton(
            button_frame,
            text="🔍 检测设备",
            font=("Microsoft YaHei", 13),
            height=40
        )
        self.components["detect_devices_btn"].pack(side="left", padx=(0, 10))

        self.components["connect_device_btn"] = ctk.CTkButton(
            button_frame,
            text="🔗 连接设备",
            font=("Microsoft YaHei", 13),
            height=40,
            fg_color=ThemeColors.PRIMARY,
            hover_color="#3a56d4"
        )
        self.components["connect_device_btn"].pack(side="left", padx=(0, 10))

        self.components["disconnect_device_btn"] = ctk.CTkButton(
            button_frame,
            text="断开连接",
            font=("Microsoft YaHei", 13),
            height=40,
            fg_color=ThemeColors.DANGER,
            hover_color="#c62828"
        )
        self.components["disconnect_device_btn"].pack(side="left")

    def _clear_content_card(self):
        """清空内容卡片"""
        if "content_card" in self.components:
            for widget in self.components["content_card"].winfo_children():
                widget.destroy()

    def _highlight_nav_button(self, index):
        """高亮导航按钮"""
        if "nav_buttons" in self.components:
            for i, btn in enumerate(self.components["nav_buttons"]):
                if i == index:
                    btn.configure(fg_color=ThemeColors.BG_HOVER)
                else:
                    btn.configure(fg_color="transparent")

    def get_component(self, name):
        """获取UI组件"""
        return self.components.get(name)

    def update_component(self, name, **kwargs):
        """更新UI组件属性"""
        if name in self.components:
            component = self.components[name]
            for key, value in kwargs.items():
                if hasattr(component, key):
                    try:
                        setattr(component, key, value)
                    except:
                        # 对于某些属性需要使用configure方法
                        if hasattr(component, 'configure'):
                            component.configure(**{key: value})
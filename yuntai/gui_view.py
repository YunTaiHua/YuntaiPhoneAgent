"""
GUIView - 纯界面构建模块（重构版）
负责所有UI组件的创建和布局，不包含业务逻辑
"""

import tkinter as tk
import customtkinter as ctk
import os

# 从 yuntai.config 导入配置
from yuntai.config import APP_VERSION

# 从 yuntai.views 导入构建器和主题
from yuntai.views import ThemeColors, PageBuilder


class GUIView:
    """纯界面构建类，只负责UI创建"""

    def __init__(self, root):
        self.root = root
        self.root.title(f"Phone Agent - 智能移动助手 v{APP_VERSION}")
        self.root.geometry("1400x900")

        # 存储UI组件引用
        self.components = {}

        # 设置外观 - 浅色米白色主题
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # 创建页面构建器
        self.page_builder = PageBuilder(self)

        # 当前页面索引
        self.current_page_index = -1  # 初始无页面

        # 创建界面
        self._setup_main_layout()

        # Frame字典
        self.content_frames = {}

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
        """创建左侧导航栏 - 现代化米白色风格"""
        self.nav_frame = ctk.CTkFrame(
            self.root, 
            width=240, 
            corner_radius=0,
            fg_color=ThemeColors.BG_NAV,
            border_width=0
        )
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_propagate(False)

        # 应用标题
        title_frame = ctk.CTkFrame(
            self.nav_frame, 
            fg_color="transparent", 
            height=100
        )
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
            font=("Microsoft YaHei", 24, "bold"),
            text_color=ThemeColors.TEXT_PRIMARY
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
            ("🎨 动态功能", "show_dynamic_panel"),
            ("⚙️ 系统设置", "show_settings_panel"),
        ]

        self.components["nav_buttons"] = []
        for text, _ in nav_items:
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                font=("Microsoft YaHei", 14),
                height=44,
                corner_radius=12,
                fg_color="transparent",
                hover_color=ThemeColors.BG_HOVER,
                text_color=ThemeColors.TEXT_PRIMARY,
                anchor="w",
                border_width=0
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.components["nav_buttons"].append(btn)

        # 底部信息
        info_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        info_frame.pack(side="bottom", fill="x", padx=20, pady=20)

        # 连接状态指示器
        status_icons_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_icons_frame.pack(anchor="w")

        self.components["connection_icon"] = ctk.CTkLabel(
            status_icons_frame,
            text="📶",
            font=("Segoe UI Emoji", 14)
        )
        self.components["connection_icon"].pack(side="left", padx=(0, 8))

        self.components["connection_indicator"] = ctk.CTkLabel(
            status_icons_frame,
            text="未连接",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.DANGER
        )
        self.components["connection_indicator"].pack(side="left")

        # TTS状态指示器
        tts_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        tts_frame.pack(anchor="w", pady=(8, 0))

        self.components["tts_icon"] = ctk.CTkLabel(
            tts_frame,
            text="🔊",
            font=("Segoe UI Emoji", 14)
        )
        self.components["tts_icon"].pack(side="left", padx=(0, 8))

        self.components["tts_indicator"] = ctk.CTkLabel(
            tts_frame,
            text="TTS: 关闭",
            font=("Microsoft YaHei", 12),
            text_color=ThemeColors.WARNING
        )
        self.components["tts_indicator"].pack(side="left")

        # 版本信息
        ctk.CTkLabel(
            info_frame,
            text=f"Version {APP_VERSION}",
            font=("Microsoft YaHei", 10),
            text_color=ThemeColors.TEXT_DISABLED
        ).pack(anchor="w", pady=(15, 0))

    def _create_main_content_frame(self):
        """创建主内容容器 - 现代化米白色风格"""
        self.components["main_container"] = ctk.CTkFrame(
            self.root, 
            fg_color=ThemeColors.BG_MAIN
        )
        self.components["main_container"].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.components["main_container"].grid_rowconfigure(0, weight=1)
        self.components["main_container"].grid_columnconfigure(0, weight=1)

        # 创建卡片容器 - 带阴影效果的圆角卡片
        self.components["content_card"] = ctk.CTkFrame(
            self.components["main_container"],
            corner_radius=12,
            fg_color=ThemeColors.BG_CARD,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        self.components["content_card"].grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 创建6个页面容器，按顺序排列（所有页面内容）
        self.content_pages = []
        for i in range(6):
            page_frame = ctk.CTkFrame(
                self.components["content_card"], 
                fg_color="transparent",
                corner_radius=20
            )
            page_frame.pack(fill="both", expand=True)
            page_frame.grid_propagate(False)
            self.content_pages.append(page_frame)
            page_frame.pack_forget()  # 初始隐藏

    def _create_status_bar(self):
        """创建底部状态栏 - 现代化样式"""
        self.components["status_bar"] = ctk.CTkFrame(
            self.root, 
            height=30,
            fg_color=ThemeColors.BG_NAV,
            border_width=1,
            border_color=ThemeColors.BORDER_LIGHT
        )
        self.components["status_bar"].grid(row=1, column=0, columnspan=2, sticky="ew")

        # 系统状态
        self.components["status_label"] = ctk.CTkLabel(
            self.components["status_bar"],
            text="系统已就绪",
            font=("Microsoft YaHei", 11),
            text_color=ThemeColors.TEXT_SECONDARY
        )
        self.components["status_label"].pack(side="left", padx=20)

    # ========== 页面创建方法（委托给PageBuilder）==========

    def show_page(self, page_index: int):
        """显示指定页面（使用独立Frame容器）"""
        # 1. 隐藏当前页面（如果有）
        if 0 <= self.current_page_index < 6:
            current_frame = self.content_pages[self.current_page_index]
            if current_frame:
                current_frame.pack_forget()

        # 2. 显示目标页面（如果需要）
        if 0 <= page_index < 6:
            target_frame = self.content_pages[page_index]
            if target_frame:
                target_frame.pack(fill="both", expand=True)

        # 3. 更新当前页面索引
        self.current_page_index = page_index

        # 4. 高亮导航按钮
        self._highlight_nav_button(page_index)

        # 5. 调用页面的初始化回调（只执行一次）
        self._call_page_init_callback(page_index)

    def _call_page_init_callback(self, page_index: int):
        """调用页面的初始化回调（只执行一次）"""
        if page_index == 0:
            self.page_builder.create_dashboard_page()
        elif page_index == 1:
            self.page_builder.create_connection_page()
        elif page_index == 2:
            self.page_builder.create_tts_page(self.page_builder.tts_manager)
        elif page_index == 3:
            self.page_builder.create_history_page()
        elif page_index == 4:
            self.page_builder.create_dynamic_page()
        elif page_index == 5:
            self.page_builder.create_settings_page()

    def create_dashboard_page(self):
        """创建控制中心页面（委托给show_page）"""
        self.show_page(0)

    def create_connection_page(self):
        """创建设备管理页面（委托给show_page）"""
        self.show_page(1)

    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面（委托给show_page）"""
        self.show_page(2)

    def create_history_page(self):
        """创建历史记录页面（委托给show_page）"""
        self.show_page(3)

    def create_dynamic_page(self):
        """创建动态功能页面（委托给show_page）"""
        self.show_page(4)

    def create_settings_page(self):
        """创建系统设置页面（委托给show_page）"""
        self.show_page(5)

    # ========== 辅助方法 ==========

    def show_file_upload_dialog(self) -> list[str]:
        """显示文件上传对话框并返回选择的文件路径列表"""
        import tkinter.filedialog as fd

        filetypes = [
            ("所有支持的文件",
              "*.jpg *.jpeg *.png *.bmp *.webp "  # 图片
              "*.mp4 *.avi *.mov *.mkv *.wmv "  # 视频
              "*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma "  # 音频
              "*.txt *.py *.csv *.xls *.xlsx *.docx *.pdf *.ppt *.pptx *.html *.js *.htm *.rss *.atom *.json *.xml *.java *.ipynb"),  # 文件
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"),
            ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv"),
            ("音频文件","*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma"),
            ("文档文件", "*.txt *.py *.csv *.xls *.xlsx *.docx *.pdf *.ppt *.pptx *.html *.js *.htm *.rss *.atom *.json *.xml *.java *.ipynb"),
            ("所有文件", "*.*")
        ]

        files = fd.askopenfilenames(
            title="选择要上传的文件",
            filetypes=filetypes
        )

        return list(files)

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
        attached_files_frame.pack(fill="x", padx=15, pady=(5, 0))

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
                                      height=40)
            file_frame.pack(fill="x", pady=2)
            file_frame.pack_propagate(False)

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

        # 强制更新布局，确保父容器正确扩展
        try:
            if attached_files_frame.master:
                attached_files_frame.master.update_idletasks()
        except Exception:
            pass

    def remove_attached_file(self, file_path: str, controller):
        """从UI中移除单个文件"""
        try:
            # 通知控制器移除文件
            controller.remove_attached_file(file_path)

            # 刷新显示
            controller.view.show_attached_files(controller.attached_files)
        except Exception as e:
            print(f"❌ 移除文件失败: {e}")

    def _clear_content_card(self):
        """清空内容卡片"""
        if "content_card" in self.components:
            for widget in self.components["content_card"].winfo_children():
                widget.destroy()

    def _highlight_nav_button(self, index):
        """高亮导航按钮 - 现代化样式"""
        if "nav_buttons" in self.components:
            for i, btn in enumerate(self.components["nav_buttons"]):
                if i == index:
                    btn.configure(
                        fg_color="#EFF3FF",
                        text_color=ThemeColors.PRIMARY,
                        hover_color="#E0E7FF"
                    )
                else:
                    btn.configure(
                        fg_color="transparent",
                        text_color=ThemeColors.TEXT_PRIMARY,
                        hover_color=ThemeColors.BG_HOVER
                    )

    def _on_device_type_change(self, device_type: str):
        """设备类型改变时的回调"""
        if hasattr(self, '_device_type_callback'):
            self._device_type_callback(device_type)

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

    def show_enter_button(self):
        """显示模拟回车按钮"""
        enter_btn = self.components.get("enter_button")
        if enter_btn:
            enter_btn.pack(side="right")

    def hide_enter_button(self):
        """隐藏模拟回车按钮"""
        enter_btn = self.components.get("enter_button")
        if enter_btn:
            enter_btn.pack_forget()

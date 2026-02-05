"""
PageBuilder - 页面构建聚合器
负责聚合各个具体页面的构建器
"""

from .theme import ThemeColors
# 导入各个具体的 Builder
from .dashboard import DashboardBuilder
from .connection import ConnectionBuilder
from .tts import TTSBuilder
from .history import HistoryBuilder
from .settings import SettingsBuilder
from .dynamic import DynamicBuilder


class PageBuilder:
    """页面构建聚合器 - 负责调用各个具体页面的构建器"""

    def __init__(self, view_instance):
        """
        Args:
            view_instance: GUIView 实例，用于访问 components 字典等
        """
        self.view = view_instance
        self.components = view_instance.components

        # 初始化各个具体的 Builder
        self.dashboard = DashboardBuilder(view_instance)
        self.connection = ConnectionBuilder(view_instance)
        self.tts = TTSBuilder(view_instance)
        self.history = HistoryBuilder(view_instance)
        self.settings = SettingsBuilder(view_instance)
        self.dynamic = DynamicBuilder(view_instance)

        # 页面初始化标志（6个页面）
        self.page_initialized = [False] * 6

        # TTS manager（用于页面创建时传递）
        self.tts_manager = None

    def _apply_current_theme_to_page(self, page_index):
        """应用当前主题到指定页面"""
        import customtkinter as ctk
        import tkinter as tk
        from .theme import DarkThemeColors, ThemeColors
        
        try:
            current_mode = ctk.get_appearance_mode().lower()
            new_colors = DarkThemeColors if current_mode == "dark" else ThemeColors
            
            def update_widget(widget, depth=0):
                """递归更新所有部件的颜色"""
                if depth > 10:
                    return
                
                try:
                    widget_type = type(widget).__name__
                    
                    if isinstance(widget, ctk.CTkFrame):
                        try:
                            current_fg = widget.cget("fg_color")
                            current_border = widget.cget("border_width")
                            
                            if current_fg and current_fg != "transparent":
                                # 根据当前颜色类型保持颜色类型一致
                                if current_fg in [ThemeColors.BG_CARD, DarkThemeColors.BG_CARD]:
                                    if current_border > 0:
                                        widget.configure(fg_color=new_colors.BG_CARD, border_color=new_colors.BORDER_LIGHT)
                                    else:
                                        widget.configure(fg_color=new_colors.BG_CARD)
                                elif current_fg in [ThemeColors.BG_CARD_ALT, DarkThemeColors.BG_CARD_ALT]:
                                    if current_border > 0:
                                        widget.configure(fg_color=new_colors.BG_CARD_ALT, border_color=new_colors.BORDER_LIGHT)
                                    else:
                                        widget.configure(fg_color=new_colors.BG_CARD_ALT)
                                elif current_fg in [ThemeColors.BG_HOVER, DarkThemeColors.BG_HOVER]:
                                    widget.configure(fg_color=new_colors.BG_HOVER)
                                elif current_fg in [ThemeColors.BG_INPUT, DarkThemeColors.BG_INPUT]:
                                    widget.configure(fg_color=new_colors.BG_INPUT)
                        except:
                            pass
                    
                    elif isinstance(widget, ctk.CTkButton):
                        try:
                            current_fg = widget.cget("fg_color")
                            if current_fg in [ThemeColors.PRIMARY, DarkThemeColors.PRIMARY]:
                                widget.configure(fg_color=new_colors.PRIMARY, hover_color=new_colors.PRIMARY_HOVER)
                            elif current_fg in [ThemeColors.SECONDARY, DarkThemeColors.SECONDARY]:
                                widget.configure(fg_color=new_colors.SECONDARY, hover_color=new_colors.SECONDARY_HOVER)
                            elif current_fg in [ThemeColors.DANGER, DarkThemeColors.DANGER]:
                                widget.configure(fg_color=new_colors.DANGER, hover_color=new_colors.DANGER_HOVER)
                            elif current_fg in [ThemeColors.SUCCESS, DarkThemeColors.SUCCESS]:
                                widget.configure(fg_color=new_colors.SUCCESS, hover_color=new_colors.SUCCESS_HOVER)
                            elif current_fg in [ThemeColors.WARNING, DarkThemeColors.WARNING]:
                                widget.configure(fg_color=new_colors.WARNING, hover_color=new_colors.WARNING_HOVER)
                            elif current_fg in [ThemeColors.ACCENT, DarkThemeColors.ACCENT]:
                                widget.configure(fg_color=new_colors.ACCENT, hover_color=new_colors.ACCENT_HOVER)
                            widget.configure(text_color=new_colors.TEXT_PRIMARY)
                        except:
                            pass
                    
                    elif isinstance(widget, ctk.CTkLabel):
                        widget.configure(text_color=new_colors.TEXT_PRIMARY)
                    
                    elif isinstance(widget, ctk.CTkEntry):
                        widget.configure(fg_color=new_colors.BG_INPUT, text_color=new_colors.TEXT_PRIMARY, border_color=new_colors.BORDER_MEDIUM)
                    
                    elif isinstance(widget, ctk.CTkTextbox):
                        widget.configure(fg_color=new_colors.BG_CARD_ALT, text_color=new_colors.TEXT_PRIMARY, border_color=new_colors.BORDER_LIGHT)
                    
                    elif isinstance(widget, ctk.CTkOptionMenu):
                        widget.configure(fg_color=new_colors.BG_INPUT, button_color=new_colors.OPTION_BUTTON_COLOR, 
                                       button_hover_color=new_colors.OPTION_BUTTON_HOVER, text_color=new_colors.TEXT_PRIMARY)
                    
                    elif isinstance(widget, ctk.CTkScrollableFrame):
                        widget.configure(fg_color="transparent", scrollbar_button_color=new_colors.BG_HOVER, 
                                       scrollbar_button_hover_color=new_colors.PRIMARY)
                    
                    elif isinstance(widget, ctk.CTkTabview):
                        widget.configure(fg_color=new_colors.BG_CARD, segmented_button_fg_color=new_colors.BG_CARD_ALT,
                                       segmented_button_selected_color=new_colors.PRIMARY, 
                                       segmented_button_selected_hover_color=new_colors.PRIMARY_HOVER)
                    
                    # tkinter 原生 Listbox 控件（如TTS历史音频列表）
                    elif widget_type == "Listbox":
                        widget.configure(
                            bg=new_colors.BG_CARD_ALT,
                            fg=new_colors.TEXT_PRIMARY,
                            selectbackground=new_colors.PRIMARY,
                            selectforeground=new_colors.TEXT_LIGHT,
                            highlightcolor=new_colors.BORDER_MEDIUM,
                            highlightbackground=new_colors.BORDER_MEDIUM
                        )
                except:
                    pass
                
                try:
                    for child in widget.winfo_children():
                        update_widget(child, depth + 1)
                except:
                    pass
            
            # 应用主题到页面
            if hasattr(self.view, 'content_pages') and 0 <= page_index < len(self.view.content_pages):
                page = self.view.content_pages[page_index]
                if page and page.winfo_exists():
                    update_widget(page)
                    
        except Exception as e:
            print(f"页面主题应用警告: {e}")

    def create_dashboard_page(self):
        """创建控制中心页面（只执行一次）"""
        if not self.page_initialized[0]:
            self.dashboard.create_page()
            self._apply_current_theme_to_page(0)
            self.page_initialized[0] = True

    def create_connection_page(self):
        """创建设备管理页面（只执行一次）"""
        if not self.page_initialized[1]:
            self.connection.create_page()
            self._apply_current_theme_to_page(1)
            self.page_initialized[1] = True

    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面（每次都创建，支持自动刷新）"""
        if not self.page_initialized[2]:
            self.tts.create_page(tts_manager)
            self._apply_current_theme_to_page(2)
            self.page_initialized[2] = True

    def create_history_page(self):
        """创建历史记录页面（只执行一次）"""
        if not self.page_initialized[3]:
            self.history.create_page()
            self._apply_current_theme_to_page(3)
            self.page_initialized[3] = True

    def create_settings_page(self):
        """创建系统设置页面（只执行一次）"""
        if not self.page_initialized[5]:
            self.settings.create_page()
            self._apply_current_theme_to_page(5)
            self.page_initialized[5] = True

    def create_dynamic_page(self):
        """创建动态功能页面（只执行一次）"""
        if not self.page_initialized[4]:
            self.dynamic.create_page()
            self._apply_current_theme_to_page(4)
            self.page_initialized[4] = True

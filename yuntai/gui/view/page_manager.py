"""
PageManagerMixin - 页面管理混入类
===================================

提供页面切换、页面创建委托和Toast消息显示功能。
"""

import logging

from yuntai.gui.view.toast_widget import ToastWidget

# 初始化模块日志记录器
logger = logging.getLogger(__name__)


class PageManagerMixin:
    """
    页面管理混入类

    提供页面切换、页面创建委托和Toast消息显示功能。

    要求宿主类具有以下属性:
        - page_stack: QStackedWidget
        - current_page_index: int
        - page_builder: PageBuilder实例
        - is_dark_theme: bool
    """

    def _create_toast_widget(self):
        """创建Toast提示组件"""
        self.toast_widget = ToastWidget(self)
        self.toast_widget.update_theme(self.is_dark_theme)

    def show_toast(self, message: str, msg_type: str = "info", duration: int = 2000):
        """
        显示Toast消息

        Args:
            message: 要显示的消息文本
            msg_type: 消息类型，可选值: "info", "success", "warning", "error"
            duration: 显示持续时间（毫秒），默认2000ms
        """
        self.toast_widget.show_toast(message, msg_type, duration)

    def show_page(self, page_index: int):
        """
        显示指定页面

        使用堆栈容器切换到指定索引的页面，并更新导航按钮高亮状态。

        Args:
            page_index: 页面索引 (0-5)
                0: 控制中心
                1: 设备管理
                2: TTS语音
                3: 历史记录
                4: 动态功能
                5: 系统设置
        """
        # 1. 显示目标页面
        if 0 <= page_index < 6:
            self.page_stack.setCurrentIndex(page_index)

        # 2. 更新当前页面索引
        self.current_page_index = page_index

        # 3. 高亮导航按钮
        self._highlight_nav_button(page_index)

        # 4. 调用页面的初始化回调（只执行一次）
        self._call_page_init_callback(page_index)

    def _call_page_init_callback(self, page_index: int):
        """调用页面的初始化回调（只执行一次）"""
        # 使用 page_builder 的 page_initialized 统一管理
        if self.page_builder.page_initialized[page_index]:
            return

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

        # page_builder 内部会设置 page_initialized，这里不需要重复设置

    def create_dashboard_page(self):
        """创建控制中心页面（委托给show_page）"""
        self.show_page(0)

    def create_connection_page(self):
        """创建设备管理页面（委托给show_page）"""
        self.show_page(1)

    def create_tts_page(self, tts_manager):
        """创建TTS语音合成页面（委托给show_page）"""
        # 保存 tts_manager 供 page_builder 使用
        self.page_builder.tts_manager = tts_manager
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

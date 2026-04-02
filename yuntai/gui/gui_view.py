"""
GUIView - 纯界面构建模块（PyQt6 重构版）
========================================

负责所有UI组件的创建和布局，不包含业务逻辑。

主要组件:
    - ToastWidget: Toast提示组件，底部居中弹出的圆角矩形卡片
    - GUIView: 主界面窗口类，负责整体UI布局和页面管理

功能特性:
    - 支持浅色/深色主题切换
    - 页面堆栈管理（控制中心、设备管理、TTS语音等）
    - TTS加载遮罩层
    - Toast消息提示
    - 文件上传对话框

使用示例:
    >>> view = GUIView()
    >>> view.show_page(0)  # 显示控制中心页面
    >>> view.show_toast("操作成功", "success")
"""

import logging

from PyQt6.QtWidgets import QMainWindow

# 从 yuntai.config 导入配置
from yuntai.core.config import APP_VERSION

# 从 yuntai.gui.view 导入混入类
from yuntai.gui.view.toast_widget import ToastWidget
from yuntai.gui.view.theme_manager import ThemeManagerMixin
from yuntai.gui.view.navigation import NavigationMixin
from yuntai.gui.view.loading_overlay import LoadingOverlayMixin
from yuntai.gui.view.page_manager import PageManagerMixin
from yuntai.gui.view.dialogs import DialogsMixin

# 初始化模块日志记录器
logger = logging.getLogger(__name__)


class GUIView(
    QMainWindow,
    ThemeManagerMixin,
    NavigationMixin,
    LoadingOverlayMixin,
    PageManagerMixin,
    DialogsMixin,
):
    """
    主界面窗口类 - 纯界面构建

    负责所有UI组件的创建和布局管理，不包含业务逻辑。
    业务逻辑由Controller和Handler处理。

    主要功能:
        - 创建和管理导航栏、主内容区、状态栏
        - 页面堆栈管理（6个页面）
        - 主题切换（浅色/深色）
        - Toast消息提示
        - TTS加载遮罩层
        - 文件上传对话框

    Attributes:
        components: UI组件字典，存储所有可复用的组件引用
        is_dark_theme: 当前是否使用深色主题
        current_page_index: 当前显示的页面索引
        page_initialized: 页面初始化标志列表
        colors: 当前主题颜色对象
        page_builder: 页面构建器实例
    """

    def __init__(self):
        """初始化主界面窗口"""
        super().__init__()

        # 窗口设置
        self.setWindowTitle(f"Phone Agent - 智能移动助手 v{APP_VERSION}")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)

        # 存储UI组件引用
        self.components = {}

        # 当前主题（False=浅色，True=深色）
        self.is_dark_theme = False

        # 当前页面索引
        self.current_page_index = -1  # 初始无页面

        # 页面初始化标志
        self.page_initialized = [False] * 6

        # 应用主题
        self._apply_theme()

        # 先创建遮罩层，确保在主窗口显示前就准备好
        self._create_tts_loading_overlay()

        # 创建界面
        self._setup_main_layout()

        # 创建Toast组件（在主布局之后创建，确保能正确显示）
        self._create_toast_widget()

        # 创建页面构建器（延迟导入避免循环依赖）
        from yuntai.views.pages import PageBuilder
        self.page_builder = PageBuilder(self)
        logger.debug("GUIView初始化完成")

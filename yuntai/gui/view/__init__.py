"""
视图模块 - GUI组件的混入类拆分
================================

将GUIView拆分为多个独立的混入类，便于维护和测试。

组件:
    - ToastWidget: Toast提示组件（独立QFrame子类）
    - ThemeManagerMixin: 主题管理
    - NavigationMixin: 导航面板
    - LoadingOverlayMixin: 加载遮罩层
    - PageManagerMixin: 页面管理
    - DialogsMixin: 对话框和工具方法
"""

from yuntai.gui.view.toast_widget import ToastWidget
from yuntai.gui.view.theme_manager import ThemeManagerMixin
from yuntai.gui.view.navigation import NavigationMixin
from yuntai.gui.view.loading_overlay import LoadingOverlayMixin
from yuntai.gui.view.page_manager import PageManagerMixin
from yuntai.gui.view.dialogs import DialogsMixin

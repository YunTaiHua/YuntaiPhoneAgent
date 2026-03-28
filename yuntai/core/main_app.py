"""
主应用程序模块
==============

本模块实现主应用程序，协调所有组件，管理程序生命周期。

主要功能：
    - 初始化 QApplication
    - 创建 GUI 控制器
    - 管理程序启动和退出
    - 检查初始连接状态

类说明：
    - MainApp: 主应用程序类

使用示例：
    >>> from yuntai.core import MainApp
    >>> 
    >>> # 创建并运行应用
    >>> app = MainApp()
    >>> exit_code = app.run()
"""
import sys
import atexit
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# 导入 GUI 控制器
from yuntai.gui.gui_controller import GUIController

# 导入统一配置
from yuntai.core.config import (
    PROJECT_ROOT,
    SCRCPY_PATH,
    validate_config,
    print_config_summary,
    APP_VERSION
)


class MainApp:
    """
    主应用程序
    
    协调所有组件，管理程序生命周期。
    使用 PyQt6 作为 GUI 框架。
    
    Attributes:
        app: QApplication 实例
        project_root: 项目根目录
        scrcpy_path: Scrcpy 工具路径
        controller: GUI 控制器实例
    
    使用示例：
        >>> app = MainApp()
        >>> exit_code = app.run()
        >>> sys.exit(exit_code)
    """

    def __init__(self) -> None:
        """
        初始化主应用程序
        
        执行以下初始化步骤：
        1. 验证配置
        2. 打印配置摘要
        3. 创建 QApplication
        4. 初始化 GUI 控制器
        5. 显示主窗口
        6. 注册退出清理函数
        """
        # 验证配置
        if not validate_config():
            logger.warning("配置验证失败，程序可能无法正常运行")

        # 打印配置摘要
        print_config_summary()

        # 创建 QApplication 实例
        # 检查是否已存在实例（避免重复创建）
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
        
        # 设置应用程序属性
        self.app.setApplicationName("Phone Agent")
        self.app.setApplicationVersion(APP_VERSION)
        logger.debug("QApplication 创建完成，版本: %s", APP_VERSION)

        # 使用统一配置的路径
        self.project_root = PROJECT_ROOT
        self.scrcpy_path = SCRCPY_PATH

        # 初始化 GUI 控制器
        logger.debug("初始化 GUI 控制器")
        self.controller = GUIController(self.project_root, self.scrcpy_path)

        # 注册退出清理函数
        atexit.register(self.cleanup)
        logger.debug("已注册退出清理函数")

        # 显示主窗口
        self.controller.view.show()
        logger.info("主窗口已显示")

        # 默认显示控制台（Dashboard）
        self.controller.show_dashboard()
        logger.debug("已显示控制台")

        # 延迟检查初始连接
        # 使用 QTimer 确保窗口完全加载后再检查
        QTimer.singleShot(500, self.check_initial_connection)
        logger.debug("已安排初始连接检查")

    def check_initial_connection(self) -> None:
        """
        检查初始连接
        
        延迟调用的方法，在窗口加载完成后检查设备连接状态。
        """
        logger.debug("开始检查初始连接")
        self.controller.check_initial_connection()

    def run(self) -> int:
        """
        运行应用程序
        
        启动 Qt 事件循环，阻塞直到应用程序退出。
        
        Returns:
            int: 退出代码，0 表示正常退出
        
        使用示例：
            >>> app = MainApp()
            >>> exit_code = app.run()
            >>> sys.exit(exit_code)
        """
        try:
            logger.info("应用程序启动")
            return self.app.exec()
        except Exception as e:
            # 记录错误日志
            logger.error("GUI 运行错误: %s", str(e), exc_info=True)
            import traceback
            traceback.print_exc()
            return 1

    def cleanup(self) -> None:
        """
        清理资源
        
        在应用程序退出时调用，清理所有资源。
        """
        logger.info("正在清理应用程序资源...")

        # 清理控制器资源
        if hasattr(self.controller, 'cleanup_on_exit'):
            self.controller.cleanup_on_exit()
            logger.debug("控制器资源已清理")

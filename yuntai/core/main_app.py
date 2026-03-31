"""
主应用程序模块
==============

启动编排器：创建注册表 → 注册服务 → 创建 GUI。
"""
import sys
import atexit
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

logger = logging.getLogger(__name__)

from yuntai.core.config import (
    PROJECT_ROOT, SCRCPY_PATH,
    validate_config, print_config_summary, APP_VERSION,
)
from yuntai.core.registry import get_registry


class MainApp:
    """主应用程序 - 启动编排器

    按层依次注册服务，最后创建 GUI。
    """

    def __init__(self) -> None:
        # 验证配置
        if not validate_config():
            logger.warning("配置验证失败，程序可能无法正常运行")
        print_config_summary()

        # 创建 QApplication
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
        self.app.setApplicationName("Phone Agent")
        self.app.setApplicationVersion(APP_VERSION)

        self.project_root = PROJECT_ROOT
        self.scrcpy_path = SCRCPY_PATH

        # 获取注册表
        registry = get_registry()

        # === Layer 0: 注册基础层服务 ===
        self._register_foundation_services(registry)

        # === Layer 1-2: 注册处理层和业务逻辑层服务 ===
        self._register_business_services(registry)

        # === Layer 3-4: 创建 Handler 和 GUI ===
        from yuntai.gui.gui_controller import GUIController
        self.controller = GUIController(self.project_root, self.scrcpy_path)

        # 注册 GUI 控制器供 Web 层使用
        registry.register("gui_controller", self.controller)

        # 注册退出清理
        atexit.register(self.cleanup)

        # 显示主窗口
        self.controller.view.show()
        self.controller.show_dashboard()

        # 延迟检查初始连接
        QTimer.singleShot(500, self.check_initial_connection)

    def _register_foundation_services(self, registry):
        """注册 Layer 0 基础层服务"""
        from yuntai.services.connection_manager import ConnectionManager
        from yuntai.services.file_manager import FileManager

        registry.register("connection_manager", ConnectionManager())
        registry.register("file_manager", FileManager())
        logger.debug("基础层服务已注册")

    def _register_business_services(self, registry):
        """注册 Layer 1-2 处理层和业务逻辑层服务"""
        from yuntai.callbacks import get_callback_manager
        from yuntai.models import get_chat_model, get_judgement_model

        callback_manager = get_callback_manager()
        registry.register("callback_manager", callback_manager)

        # 注册模型工厂
        registry.register_factory("chat_model", lambda: get_chat_model())
        registry.register_factory("judgement_model", lambda: get_judgement_model())
        logger.debug("业务逻辑层服务已注册")

    def check_initial_connection(self) -> None:
        """检查初始连接"""
        self.controller.check_initial_connection()

    def run(self) -> int:
        """运行应用程序"""
        try:
            logger.info("应用程序启动")
            return self.app.exec()
        except Exception as e:
            logger.error("GUI 运行错误: %s", str(e), exc_info=True)
            import traceback
            traceback.print_exc()
            return 1

    def cleanup(self) -> None:
        """清理资源"""
        logger.info("正在清理应用程序资源...")
        if hasattr(self.controller, 'cleanup_on_exit'):
            self.controller.cleanup_on_exit()

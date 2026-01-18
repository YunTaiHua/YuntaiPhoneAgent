"""
MainApp - 主应用程序模块
协调所有组件，管理程序生命周期
"""


import os
import sys
import tkinter as tk
import customtkinter as ctk
import threading
import time
import atexit
from typing import Optional

# 重构模块
from .gui_controller import GUIController

# 使用新的统一配置
from .config import PROJECT_ROOT, SCRCPY_PATH, validate_config, print_config_summary



class MainApp:
    """主应用程序 - 协调所有组件"""

    def __init__(self):
        # 验证配置
        if not validate_config():
            print("⚠️ 配置验证失败，程序可能无法正常运行")

        # 打印配置摘要
        print_config_summary()

        # 创建主窗口
        self.root = ctk.CTk()

        # 使用统一配置的路径
        self.project_root = PROJECT_ROOT
        self.scrcpy_path = SCRCPY_PATH

        # 初始化控制器
        self.controller = GUIController(self.root, self.project_root, self.scrcpy_path)

        # 注册退出清理函数
        atexit.register(self.cleanup)

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 默认显示控制台
        self.controller.show_dashboard()

        # 延迟检查初始连接
        self.root.after(500, self.check_initial_connection)


    def check_initial_connection(self):
        """检查初始连接"""
        self.controller.check_initial_connection()

    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI运行错误: {e}")
            import traceback
            traceback.print_exc()

    def cleanup(self):
        """清理资源"""
        print("🧹 正在清理应用程序资源...")

        # 清理控制器资源
        self.controller.cleanup_on_exit()

    def on_closing(self):
        """窗口关闭事件"""
        self.cleanup()
        self.root.quit()
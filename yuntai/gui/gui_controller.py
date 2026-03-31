"""
GUI 控制器模块
==============

本模块实现 GUI 控制器，负责处理用户操作，连接 UI 和后台任务，并协调各个 Handler。
支持 LangChain Callbacks 实现流式输出。

主要功能：
    - 用户事件处理：处理按钮点击、输入提交等事件
    - 任务执行：执行用户命令，支持多模态输入
    - 流式输出：支持实时流式输出响应内容
    - 设备管理：管理设备连接和状态
    - TTS 集成：支持语音播报回复内容
    - 主题切换：支持深色/浅色主题切换

类说明：
    - GUIController: GUI 控制器类

使用示例：
    >>> from yuntai.gui import GUIController
    >>>
    >>> # 创建控制器
    >>> controller = GUIController(project_root, scrcpy_path)
    >>>
    >>> # 运行应用
    >>> exit_code = controller.run()
"""
import sys

from yuntai.gui.controller import (
    ControllerCore,
    CommandMixin,
    UIStateMixin,
    FileOpsMixin,
    TTSIntegrationMixin,
    DeviceMixin,
)


class GUIController(
    ControllerCore,
    CommandMixin,
    UIStateMixin,
    FileOpsMixin,
    TTSIntegrationMixin,
    DeviceMixin,
):
    """
    GUI 控制器 - 组合所有功能模块

    处理所有用户事件和业务逻辑，支持流式输出。
    使用 PyQt6 信号机制实现线程安全的 UI 更新。

    Attributes:
        project_root: 项目根目录
        scrcpy_path: Scrcpy 工具路径
        app: QApplication 实例
        view: GUI 视图实例
        task_manager: 任务管理器实例
        callback_manager: 回调管理器实例
        task_chain: 任务处理链实例
        judgement_agent: 任务判断 Agent
        output_capture: 输出捕获器
        message_queue: 消息队列
        is_executing: 是否正在执行任务
        is_continuous_mode: 是否处于持续回复模式
        terminate_flag: 终止标志
        device_type: 设备类型

    使用示例：
        >>> controller = GUIController(project_root, scrcpy_path)
        >>> controller.run()
    """
    pass


def main():
    """主函数"""
    from yuntai.core.config import PROJECT_ROOT, SCRCPY_PATH

    controller = GUIController(PROJECT_ROOT, SCRCPY_PATH)
    sys.exit(controller.run())


if __name__ == "__main__":
    main()

"""
命令执行 Mixin
=============

CommandMixin 包含命令执行、持续回复、终止操作等命令相关功能。
"""
import sys
import logging
import threading
import queue
import time
import datetime
import traceback
from typing import Any
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

# 第三方库
from zhipuai import ZhipuAI

# 项目模块
from yuntai.core.config import (
    SHORTCUTS, ZHIPU_API_KEY,
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR, FOREVER_MEMORY_FILE,
    CONNECTION_CONFIG_FILE, SCRCPY_PATH, validate_config, print_config_summary,
    ZHIPU_CHAT_MODEL, ZHIPU_MODEL, ZHIPU_API_BASE_URL
)

# 引用 TaskManager（保留用于连接管理和TTS）
from yuntai.services.task_manager import TaskManager
# 引用新的 TaskChain
from yuntai.chains import TaskChain, ReplyChain
from yuntai.agents import JudgementAgent
# 引用 Handlers
from yuntai.handlers import ConnectionHandler, TTSHandler, DynamicHandler, SystemHandler

# PyQt6 GUI
from yuntai.gui.gui_view import GUIView
from yuntai.gui.styles import ThemeColors
from yuntai.gui.output_capture import SimpleOutputCapture


class CommandMixin:
    """
    命令执行 Mixin

    包含命令执行、多模态聊天处理、持续回复、终止操作等功能。
    通过 self 属性访问 ControllerCore 中初始化的实例变量。
    """

    def execute_command(self):
        """执行命令"""
        if self.is_executing:
            self.show_toast("请等待当前任务完成", "warning")
            return

        command_input = self.view.get_component("command_input")
        if not command_input:
            return
        command = command_input.toPlainText().strip()
        has_attachments = len(self.attached_files) > 0

        if not command and not has_attachments:
            self.show_toast("请输入命令或选择文件", "warning")
            return

        logger.info("执行命令: %s", command[:50] if len(command) > 50 else command)

        command_input.clear()
        command_input.setFixedHeight(42)
        if self.terminate_flag.is_set():
            self.terminate_flag.clear()

        output_text = self.view.get_component("output_text")
        if output_text:
            if not self.output_capture:
                self.output_capture = SimpleOutputCapture(output_text, self.view.is_dark_theme)
            elif self.output_capture.text_widget != output_text:
                self.output_capture.set_text_widget(output_text)

        self.is_executing = True
        self._disable_execute_button()
        self._enable_terminate_button()

        def run_command():
            try:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'═' * 9} [{timestamp} 对话开始] {'═' * 9}\n")
                if has_attachments:
                    print(f"💭 多模态指令: {command if command else '[无文本]'}")
                    print(f"📌 附件数量: {len(self.attached_files)} 个文件")
                else:
                    print(f"💭 指令: {command}")

                if not has_attachments and not self.task_manager.is_connected:
                    task_result = self.judgement_agent.judge(command)
                    task_type = task_result.task_type
                    if task_type != "free_chat":
                        print(f"❌ 设备未连接，请先连接设备")
                        return

                result = None
                if has_attachments:
                    result = self._handle_multimodal_chat(command, self.attached_files)
                else:
                    self._sync_device_to_task_chain()
                    result, task_info = self.task_chain.process(command)

                # 持续回复处理
                if result and isinstance(result, str) and "🔄CONTINUOUS_REPLY:" in result:
                    try:
                        parts = result.replace("🔄CONTINUOUS_REPLY:", "").split(":")
                        if len(parts) == 2:
                            target_app, target_object = parts
                            if not self.task_manager.is_connected:
                                print(f"❌ 设备未连接，无法启动持续回复")
                                return
                            self.start_continuous_reply_thread(
                                self.task_manager.task_args, target_app, target_object, self.task_manager.device_id
                            )
                            return
                    except Exception as e:
                        logger.error("解析持续回复标记失败: %s", str(e))
                        print(f"❌ 解析持续回复标记失败: {e}")
                        result = f"❌ 解析持续回复参数失败: {str(e)}"

                if result:
                    print(f"🎉 结果：{result}")

                if "持续回复模式" in str(result) or "continuous_reply" in str(result).lower():
                    print(f"🔄 检测到持续回复模式，保持按钮状态")
                    return

            except Exception as e:
                logger.error("命令执行错误: %s", str(e), exc_info=True)
                print(f"❌ 错误：{str(e)}")
                traceback.print_exc()
            finally:
                # 使用信号槽清理附件文件
                QTimer.singleShot(100, self._clear_attached_files_signal.emit)

                if not self.is_continuous_mode:
                    self.message_queue.put(("success", "命令执行完成"))
                    self._enable_execute_button_signal.emit()
                    self._disable_terminate_button_signal.emit()
                    self.is_executing = False

        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    def _handle_multimodal_chat(self, text: str, file_paths: list[str]) -> str:
        """
        处理多模态聊天

        Args:
            text: 文本内容
            file_paths: 文件路径列表

        Returns:
            处理结果
        """
        logger.info("处理多模态聊天，文件数: %d", len(file_paths))
        print(f"📋 文本: {text}")
        print(f"📌 附件: {len(file_paths)} 个文件")

        try:
            if not file_paths or len(file_paths) == 0:
                return "没有可处理的文件"

            valid_files = []
            for file_path in file_paths:
                if Path(file_path).exists():
                    valid_files.append(file_path)
                else:
                    print(f"⚠️  文件不存在: {file_path}")

            if len(valid_files) == 0:
                return "没有有效的文件"

            if not self.multimodal_processor:
                from yuntai.processors.multimodal_processor import MultimodalProcessor
                self.multimodal_processor = MultimodalProcessor()

            history = self._get_chat_history_for_multimodal()

            success, response, audio_result = self.multimodal_processor.process_with_files(
                text=text, file_paths=valid_files, history=history,
                temperature=0.7, max_tokens=2000
            )

            if success:
                print(f"✅ 多模态分析完成")
                if audio_result:
                    audio_transcription = audio_result.get("audio_transcription", "")
                    if audio_transcription:
                        pass

                self._save_multimodal_chat_history(text, valid_files, response)

                if self.task_manager.tts_manager.tts_enabled and len(response) > 5:
                    def speak_reply():
                        try:
                            self.task_manager.tts_manager.speak_text_intelligently(response)
                        except Exception as e:
                            logger.warning("语音播报失败: %s", str(e))
                            print(f"❌ 语音播报失败: {e}")

                    threading.Timer(0.5, speak_reply).start()

                return ""
            else:
                error_msg = f"❌ 多模态分析失败: {response}"
                print(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f"❌ 多模态处理失败: {str(e)}"
            logger.error("多模态处理失败: %s", str(e), exc_info=True)
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def _sync_device_to_task_chain(self):
        """同步设备信息到TaskChain"""
        if self.task_manager.is_connected:
            self.task_chain.device_id = self.task_manager.device_id
            self.task_chain.task_args = self.task_manager.task_args
            logger.debug("同步设备信息到 TaskChain: %s", self.task_manager.device_id)

    # ============ 持续回复线程 ============

    def start_continuous_reply_thread(self, task_args, target_app, target_object, device_id):
        """
        启动持续回复线程

        Args:
            task_args: 任务参数
            target_app: 目标 APP
            target_object: 聊天对象
            device_id: 设备 ID
        """
        logger.info("启动持续回复线程: %s -> %s", target_app, target_object)

        if self.is_continuous_mode:
            print("⚠️  已经有持续回复在运行")
            return

        self.is_continuous_mode = True
        self.terminate_flag.clear()
        self._disable_execute_button()
        self._enable_terminate_button()
        print(f"🔄 启动持续回复模式: {target_app} -> {target_object}")

        def continuous_reply_loop():
            try:
                print(f"🚀 持续回复线程启动: {target_app} -> {target_object}")

                self._current_reply_chain = ReplyChain(
                    device_id=device_id,
                    file_manager=self.task_manager.file_manager,
                    tts_manager=self.task_manager.tts_manager
                )

                success, result = self._current_reply_chain.continuous_reply(
                    target_app, target_object
                )

                if success:
                    print(f"✅ {result}")
                else:
                    print(f"⏹️  {result}")

            except Exception as e:
                logger.error("持续回复错误: %s", str(e), exc_info=True)
                print(f"❌ 持续回复错误：{str(e)}")
            finally:
                self.is_continuous_mode = False
                self.terminate_flag.clear()
                self._current_reply_chain = None
                self._reset_button_states_signal.emit()

        thread = threading.Thread(target=continuous_reply_loop)
        thread.daemon = True
        thread.start()
        self.active_threads.append(thread)

    # ============ 终止操作 ============

    def terminate_operation(self):
        """终止当前操作"""
        if not self.is_executing:
            return

        logger.info("终止当前操作")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'═' * 9} [{timestamp} 操作终止] {'═' * 9}")
        print("🛑 正在发送终止信号...\n")

        self._cleanup_active_threads()

        # 停止持续回复
        if hasattr(self, '_current_reply_chain') and self._current_reply_chain:
            self._current_reply_chain.stop()

        # 停止 TaskChain 中的持续回复
        if hasattr(self, 'task_chain') and self.task_chain:
            self.task_chain.stop_continuous_reply()

        if not self.active_threads and not self.is_continuous_mode:
            self.show_toast("没有正在执行的操作", "info")
            return

        self.terminate_flag.set()
        self.terminating.set()
        self._disable_terminate_button()

        if self.is_continuous_mode:
            print(f"\n🛑 正在终止持续回复模式...")
        else:
            print(f"\n🛑 正在终止当前任务...")
        self.show_toast("已发送终止信号", "warning")

    def simulate_enter(self):
        """模拟回车键效果"""
        logger.debug("模拟回车键")
        print("[用户点击模拟回车按钮]")
        try:
            from yuntai.core.agent_executor import AgentExecutor
            AgentExecutor.user_confirm()
        except Exception as e:
            logger.warning("发送确认信号失败: %s", str(e))
            print(f"⚠️  发送确认信号失败: {e}")

        print("[用户已确认]")

    def clear_output(self):
        """清空输出区域"""
        logger.debug("清空输出区域")
        output_text = self.view.get_component("output_text")
        if output_text:
            output_text.setReadOnly(False)
            output_text.clear()
            output_text.setReadOnly(True)
            self.show_toast("输出已清空", "info")

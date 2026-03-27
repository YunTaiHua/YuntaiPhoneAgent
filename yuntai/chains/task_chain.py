"""
任务处理链
整合判断 → 分发 → 执行流程
支持 LangChain Callbacks 追踪链执行
"""

from __future__ import annotations

import threading
from typing import Any, TYPE_CHECKING

from langchain_core.callbacks import BaseCallbackHandler

from yuntai.agents import JudgementAgent, ChatAgent, PhoneAgent
from yuntai.chains.reply_chain import ReplyChain
from yuntai.prompts import (
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)
from yuntai.core.config import SHORTCUTS, TTS_SPEAK_DELAY_TASK
from yuntai.callbacks import get_callback_manager

if TYPE_CHECKING:
    from yuntai.services.file_manager import FileManager
    from yuntai.services.task_manager import TTSManager
    from yuntai.callbacks import CallbackManager


class TaskChain:
    """任务处理链 - 支持 Callbacks 追踪"""

    def __init__(
        self,
        device_id: str = "",
        file_manager: FileManager | None = None,
        tts_manager: TTSManager | None = None
    ) -> None:
        self.device_id: str = device_id
        self.file_manager: FileManager | None = file_manager
        self.tts_manager: TTSManager | None = tts_manager

        self.callback_manager: CallbackManager = get_callback_manager()

        self.judgement_agent: JudgementAgent = JudgementAgent()
        self.chat_agent: ChatAgent = ChatAgent(file_manager=file_manager, tts_manager=tts_manager)
        self.phone_agent: PhoneAgent = PhoneAgent(device_id=device_id)
        self.reply_chain: ReplyChain = ReplyChain(
            device_id=device_id,
            file_manager=file_manager,
            tts_manager=tts_manager
        )

        self._continuous_reply_thread: threading.Thread | None = None

    def set_device_id(self, device_id: str) -> None:
        """设置设备 ID"""
        self.device_id = device_id
        self.phone_agent.set_device_id(device_id)
        self.reply_chain.set_device_id(device_id)

    def set_tts_manager(self, tts_manager: TTSManager | None) -> None:
        """设置 TTS 管理器"""
        self.tts_manager = tts_manager
        self.chat_agent.tts_manager = tts_manager

    def process(
        self,
        user_input: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        处理用户输入（支持 Callbacks）

        流程：
        1. JudgementAgent 判断任务类型
        2. 根据任务类型分发到对应的处理逻辑

        Args:
            user_input: 用户输入
            callbacks: 自定义回调处理器列表

        Returns:
            (处理结果, 任务信息)
        """
        if not user_input or not user_input.strip():
            return "输入为空", {}

        all_callbacks = self._prepare_callbacks(callbacks)

        if len(user_input.strip()) == 1:
            letter = user_input.strip().lower()
            if letter in SHORTCUTS:
                task = SHORTCUTS[letter]
                return self._handle_basic_operation(task), {}

        judgement_result = self.judgement_agent.judge(
            user_input,
            callbacks=all_callbacks
        )
        task_info = judgement_result.to_dict()

        print(f"📋 任务类型: {judgement_result.task_type}")

        if judgement_result.task_type == TASK_TYPE_FREE_CHAT:
            result = self._handle_free_chat(user_input, all_callbacks)

        elif judgement_result.task_type == TASK_TYPE_BASIC_OPERATION:
            result = self._handle_basic_operation(
                f"打开{judgement_result.target_app}"
            )

        elif judgement_result.task_type == TASK_TYPE_SINGLE_REPLY:
            if not judgement_result.target_app or not judgement_result.target_object:
                result = "无法识别 APP 或聊天对象"
            else:
                result = self._handle_single_reply(
                    judgement_result.target_app,
                    judgement_result.target_object,
                    all_callbacks
                )

        elif judgement_result.task_type == TASK_TYPE_CONTINUOUS_REPLY:
            if not judgement_result.target_app or not judgement_result.target_object:
                result = "无法识别 APP 或聊天对象"
            else:
                result = self._handle_continuous_reply(
                    judgement_result.target_app,
                    judgement_result.target_object
                )

        elif judgement_result.task_type == TASK_TYPE_COMPLEX_OPERATION:
            result = self._handle_complex_operation(user_input)

        else:
            result = self._handle_free_chat(user_input, all_callbacks)

        return result, task_info

    def _prepare_callbacks(
        self,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> list[BaseCallbackHandler]:
        """
        准备回调处理器列表

        Args:
            callbacks: 用户提供的回调列表

        Returns:
            合并后的回调处理器列表
        """
        all_callbacks: list[BaseCallbackHandler] = []

        global_callbacks = self.callback_manager.get_callbacks(include_global=True)
        all_callbacks.extend(global_callbacks)

        if callbacks:
            all_callbacks.extend(callbacks)

        return all_callbacks

    def _handle_free_chat(
        self,
        user_input: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> str:
        """处理自由聊天"""
        return self.chat_agent.chat(user_input, callbacks=callbacks)

    def _handle_basic_operation(self, task: str) -> str:
        """处理基础操作"""
        print(f"📱 执行：{task}")
        success, result = self.phone_agent.execute_operation(task)

        if success:
            if self.tts_manager and getattr(self.tts_manager, 'tts_enabled', False) and result:
                threading.Timer(TTS_SPEAK_DELAY_TASK, lambda: self.tts_manager.speak_text_intelligently(result)).start()
            return "✅ 操作完成"
        else:
            return f"❌ 操作失败: {result}"

    def _handle_single_reply(
        self,
        app_name: str,
        chat_object: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> str:
        """处理单次回复"""
        success, result = self.reply_chain.single_reply(
            app_name,
            chat_object,
            callbacks=callbacks
        )
        return result

    def _handle_continuous_reply(self, app_name: str, chat_object: str) -> str:
        """处理持续回复 - 只返回标记，由 gui_controller 统一启动线程"""
        if not self.device_id:
            return "❌ 设备未连接"
        return f"🔄CONTINUOUS_REPLY:{app_name}:{chat_object}"

    def _handle_complex_operation(self, task: str) -> str:
        """处理复杂操作"""
        print(f"⚙️ 执行复杂操作：{task}")
        success, result = self.phone_agent.execute_operation(task)

        if success:
            if self.tts_manager and getattr(self.tts_manager, 'tts_enabled', False) and result:
                threading.Timer(TTS_SPEAK_DELAY_TASK, lambda: self.tts_manager.speak_text_intelligently(result)).start()
            return "✅ 操作完成"
        else:
            return f"❌ 操作失败: {result}"

    def stop_continuous_reply(self) -> None:
        """停止持续回复"""
        if self.reply_chain:
            self.reply_chain.stop()

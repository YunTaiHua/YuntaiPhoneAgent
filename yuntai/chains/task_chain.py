"""
任务处理链模块
==============

本模块实现任务处理链，整合判断、分发、执行流程，支持 LangChain Callbacks 追踪链执行。

主要功能：
    - 任务判断：使用 JudgementAgent 判断任务类型
    - 任务分发：根据任务类型分发到对应的处理逻辑
    - 任务执行：执行自由聊天、基础操作、回复等任务
    - 持续回复：支持启动持续回复流程

类说明：
    - TaskChain: 任务处理链类

使用示例：
    >>> from yuntai.chains import TaskChain
    >>> 
    >>> # 创建任务链
    >>> chain = TaskChain(device_id="your_device")
    >>> 
    >>> # 处理用户输入
    >>> result, info = chain.process("打开微信")
    >>> print(result)
"""
from __future__ import annotations

import logging
import threading
from typing import Any, TYPE_CHECKING

from langchain_core.callbacks import BaseCallbackHandler

from yuntai.agents import JudgementAgent, ChatAgent, PhoneAgent
from yuntai.chains.reply_chain import ReplyChain
from yuntai.tools.callback_utils import prepare_callbacks_with_manager
from yuntai.prompts import (
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)
from yuntai.core.config import SHORTCUTS, TTS_SPEAK_DELAY_TASK
from yuntai.callbacks import get_callback_manager

# 类型检查时导入，避免运行时循环导入
if TYPE_CHECKING:
    from yuntai.services.file_manager import FileManager
    from yuntai.services.task_manager import TTSManager
    from yuntai.callbacks import CallbackManager

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class TaskChain:
    """
    任务处理链
    
    整合判断、分发、执行流程，支持 LangChain Callbacks 追踪链执行。
    根据任务类型将用户输入分发到对应的处理逻辑。
    
    Attributes:
        device_id: 设备 ID
        file_manager: 文件管理器实例
        tts_manager: TTS 管理器实例
        callback_manager: 回调管理器实例
        judgement_agent: 任务判断 Agent
        chat_agent: 聊天 Agent
        phone_agent: 手机操作 Agent
        reply_chain: 回复处理链
        _continuous_reply_thread: 持续回复线程
    
    使用示例：
        >>> chain = TaskChain(device_id="device_123")
        >>> result, info = chain.process("打开微信给张三发消息")
    """

    def __init__(
        self,
        device_id: str = "",
        file_manager: FileManager | None = None,
        tts_manager: TTSManager | None = None,
        judgement_agent: JudgementAgent | None = None,
        chat_agent: ChatAgent | None = None,
        phone_agent: PhoneAgent | None = None,
        reply_chain: ReplyChain | None = None,
        callback_manager=None
    ) -> None:
        """
        初始化任务处理链

        Args:
            device_id: 设备 ID，用于标识要操作的手机设备
            file_manager: 文件管理器实例，用于保存对话历史
            tts_manager: TTS 管理器实例，用于语音播报
            judgement_agent: 任务判断 Agent，为 None 时自动创建
            chat_agent: 聊天 Agent，为 None 时自动创建
            phone_agent: 手机操作 Agent，为 None 时自动创建
            reply_chain: 回复处理链，为 None 时自动创建
            callback_manager: 回调管理器实例，为 None 时自动获取单例
        """
        # 设备 ID
        self.device_id: str = device_id
        # 文件管理器
        self.file_manager: FileManager | None = file_manager
        # TTS 管理器
        self.tts_manager: TTSManager | None = tts_manager

        # 获取回调管理器单例
        self.callback_manager = callback_manager or get_callback_manager()

        # 初始化各个 Agent
        self.judgement_agent = judgement_agent or JudgementAgent(callback_manager=self.callback_manager)
        self.chat_agent = chat_agent or ChatAgent(
            file_manager=file_manager, tts_manager=tts_manager,
            callback_manager=self.callback_manager
        )
        self.phone_agent = phone_agent or PhoneAgent(device_id=device_id)

        # 初始化回复链
        self.reply_chain = reply_chain or ReplyChain(
            device_id=device_id, file_manager=file_manager,
            tts_manager=tts_manager, callback_manager=self.callback_manager
        )

        # 持续回复线程
        self._continuous_reply_thread: threading.Thread | None = None
        
        logger.debug("TaskChain 初始化完成，设备: %s", device_id if device_id else "未设置")

    def set_device_id(self, device_id: str) -> None:
        """
        设置设备 ID
        
        更新设备 ID 并同步更新相关组件。
        
        Args:
            device_id: 新的设备 ID
        """
        logger.info("设置设备 ID: %s", device_id)
        self.device_id = device_id
        self.phone_agent.set_device_id(device_id)
        self.reply_chain.set_device_id(device_id)

    def set_tts_manager(self, tts_manager: TTSManager | None) -> None:
        """
        设置 TTS 管理器
        
        更新 TTS 管理器并同步更新相关组件。
        
        Args:
            tts_manager: 新的 TTS 管理器实例
        """
        logger.info("设置 TTS 管理器")
        self.tts_manager = tts_manager
        self.chat_agent.tts_manager = tts_manager

    def process(
        self,
        user_input: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """
        处理用户输入（支持 Callbacks）
        
        主要的处理入口方法，执行以下流程：
        1. 检查输入有效性
        2. 检查快捷指令
        3. JudgementAgent 判断任务类型
        4. 根据任务类型分发到对应的处理逻辑
        
        Args:
            user_input: 用户输入的文本
            callbacks: 自定义回调处理器列表
        
        Returns:
            tuple[str, dict]: (处理结果, 任务信息字典)
        
        使用示例：
            >>> result, info = chain.process("打开微信")
            >>> print(f"结果: {result}, 类型: {info['task_type']}")
        """
        # 检查输入是否为空
        if not user_input or not user_input.strip():
            logger.warning("用户输入为空")
            return "输入为空", {}

        logger.info("处理用户输入: %s", user_input[:50] if len(user_input) > 50 else user_input)
        
        # 准备回调处理器
        all_callbacks = prepare_callbacks_with_manager(self.callback_manager, callbacks=callbacks)

        # 检查是否为单字母快捷指令
        if len(user_input.strip()) == 1:
            letter = user_input.strip().lower()
            if letter in SHORTCUTS:
                # 获取快捷指令对应的任务
                task = SHORTCUTS[letter]
                logger.info("匹配到快捷指令: %s -> %s", letter, task)
                return self._handle_basic_operation(task), {}

        # 使用 JudgementAgent 判断任务类型
        logger.debug("开始判断任务类型")
        judgement_result = self.judgement_agent.judge(
            user_input,
            callbacks=all_callbacks
        )
        task_info = judgement_result.to_dict()

        print(f"📋 任务类型: {judgement_result.task_type}")

        # 根据任务类型分发处理
        if judgement_result.task_type == TASK_TYPE_FREE_CHAT:
            # 自由聊天
            logger.debug("分发到自由聊天处理")
            result = self._handle_free_chat(user_input, all_callbacks)

        elif judgement_result.task_type == TASK_TYPE_BASIC_OPERATION:
            # 基础操作（如打开 APP）
            logger.debug("分发到基础操作处理")
            result = self._handle_basic_operation(
                f"打开{judgement_result.target_app}"
            )

        elif judgement_result.task_type == TASK_TYPE_SINGLE_REPLY:
            # 单次回复
            logger.debug("分发到单次回复处理")
            if not judgement_result.target_app or not judgement_result.target_object:
                result = "无法识别 APP 或聊天对象"
            else:
                result = self._handle_single_reply(
                    judgement_result.target_app,
                    judgement_result.target_object,
                    all_callbacks
                )

        elif judgement_result.task_type == TASK_TYPE_CONTINUOUS_REPLY:
            # 持续回复
            logger.debug("分发到持续回复处理")
            if not judgement_result.target_app or not judgement_result.target_object:
                result = "无法识别 APP 或聊天对象"
            else:
                result = self._handle_continuous_reply(
                    judgement_result.target_app,
                    judgement_result.target_object
                )

        elif judgement_result.task_type == TASK_TYPE_COMPLEX_OPERATION:
            # 复杂操作
            logger.debug("分发到复杂操作处理")
            result = self._handle_complex_operation(user_input)

        else:
            # 未知类型，默认为自由聊天
            logger.debug("未知任务类型，默认为自由聊天")
            result = self._handle_free_chat(user_input, all_callbacks)

        return result, task_info

    def _handle_free_chat(
        self,
        user_input: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> str:
        """
        处理自由聊天
        
        调用 ChatAgent 进行自由对话。
        
        Args:
            user_input: 用户输入的文本
            callbacks: 回调处理器列表
        
        Returns:
            聊天回复内容
        """
        logger.info("处理自由聊天")
        return self.chat_agent.chat(user_input, callbacks=callbacks)

    def _handle_basic_operation(self, task: str) -> str:
        """
        处理基础操作
        
        执行简单的手机操作，如打开 APP。
        
        Args:
            task: 操作指令
        
        Returns:
            操作结果消息
        """
        logger.info("处理基础操作: %s", task)
        print(f"📱 执行：{task}")
        
        # 执行操作
        success, result = self.phone_agent.execute_operation(task)

        if success:
            # TTS 语音播报
            if self.tts_manager and getattr(self.tts_manager, 'tts_enabled', False) and result:
                threading.Timer(TTS_SPEAK_DELAY_TASK, lambda: self.tts_manager.speak_text_intelligently(result)).start()
                logger.debug("已安排 TTS 播报")
            return "✅ 操作完成"
        else:
            logger.error("操作失败: %s", result)
            return f"❌ 操作失败: {result}"

    def _handle_single_reply(
        self,
        app_name: str,
        chat_object: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> str:
        """
        处理单次回复
        
        调用 ReplyChain 执行单次回复流程。
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象名称
            callbacks: 回调处理器列表
        
        Returns:
            回复结果消息
        """
        logger.info("处理单次回复: APP=%s, 对象=%s", app_name, chat_object)
        success, result = self.reply_chain.single_reply(
            app_name,
            chat_object,
            callbacks=callbacks
        )
        return result

    def _handle_continuous_reply(self, app_name: str, chat_object: str) -> str:
        """
        处理持续回复
        
        返回标记字符串，由 gui_controller 统一启动线程。
        这种设计可以避免在链内部创建线程，便于统一管理。
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象名称
        
        Returns:
            标记字符串，格式为 "🔄CONTINUOUS_REPLY:APP:对象"
        """
        logger.info("处理持续回复: APP=%s, 对象=%s", app_name, chat_object)
        
        # 检查设备是否已连接
        if not self.device_id:
            logger.warning("设备未连接")
            return "❌ 设备未连接"
        
        # 返回标记字符串，由上层统一启动线程
        return f"🔄CONTINUOUS_REPLY:{app_name}:{chat_object}"

    def _handle_complex_operation(self, task: str) -> str:
        """
        处理复杂操作
        
        执行复杂的手机操作，如打开 APP 并发送消息。
        
        Args:
            task: 操作指令
        
        Returns:
            操作结果消息
        """
        logger.info("处理复杂操作: %s", task)
        print(f"⚙️ 执行复杂操作：{task}")
        
        # 执行操作
        success, result = self.phone_agent.execute_operation(task)

        if success:
            # TTS 语音播报
            if self.tts_manager and getattr(self.tts_manager, 'tts_enabled', False) and result:
                threading.Timer(TTS_SPEAK_DELAY_TASK, lambda: self.tts_manager.speak_text_intelligently(result)).start()
                logger.debug("已安排 TTS 播报")
            return "✅ 操作完成"
        else:
            logger.error("操作失败: %s", result)
            return f"❌ 操作失败: {result}"

    def stop_continuous_reply(self) -> None:
        """
        停止持续回复
        
        停止正在运行的持续回复流程。
        """
        logger.info("停止持续回复")
        if self.reply_chain:
            self.reply_chain.stop()

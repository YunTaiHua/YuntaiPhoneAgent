"""
回复处理链模块
==============

本模块实现回复处理链，使用 LangGraph 工作流处理回复，支持 LangChain Callbacks 追踪链执行。

主要功能：
    - 单次回复：执行一次完整的回复流程
    - 持续回复：使用 LangGraph 工作流持续监控和回复
    - 异步执行：支持异步启动持续回复
    - TTS 集成：支持语音播报回复内容

类说明：
    - ReplyChain: 回复处理链类

使用示例：
    >>> from yuntai.chains import ReplyChain
    >>> 
    >>> # 创建回复链
    >>> chain = ReplyChain(device_id="your_device")
    >>> 
    >>> # 单次回复
    >>> success, result = chain.single_reply("微信", "张三")
    >>> 
    >>> # 持续回复
    >>> success, result = chain.continuous_reply("微信", "张三", max_cycles=30)
"""
from __future__ import annotations

import logging
import threading
import datetime
from typing import Any, Callable, TYPE_CHECKING

from langchain_core.callbacks import BaseCallbackHandler

from yuntai.graphs import ReplyGraph
from yuntai.agents.phone_agent import PhoneAgent
from yuntai.tools.message_tools import parse_messages, generate_reply
from yuntai.models import get_zhipu_client
from yuntai.tools.callback_utils import prepare_callbacks_with_manager
from yuntai.callbacks import get_callback_manager
from yuntai.core.config import (
    MIN_MESSAGE_LENGTH,
    TTS_SPEAK_DELAY_REPLY,
)

# 类型检查时导入，避免运行时循环导入
if TYPE_CHECKING:
    from yuntai.services.file_manager import FileManager
    from yuntai.services.task_manager import TTSManager
    from yuntai.callbacks import CallbackManager
    from zhipuai import ZhipuAI

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class ReplyChain:
    """
    回复处理链
    
    使用 LangGraph 工作流处理回复，支持 LangChain Callbacks 追踪链执行。
    提供单次回复和持续回复两种模式。
    
    Attributes:
        device_id: 设备 ID
        file_manager: 文件管理器实例
        tts_manager: TTS 管理器实例
        callback_manager: 回调管理器实例
        _reply_graph: ReplyGraph 实例（延迟创建）
        _continuous_thread: 持续回复线程
    
    使用示例：
        >>> chain = ReplyChain(device_id="device_123")
        >>> success, result = chain.single_reply("微信", "张三")
    """

    def __init__(
        self,
        device_id: str = "",
        file_manager: FileManager | None = None,
        tts_manager: TTSManager | None = None,
        callback_manager=None
    ) -> None:
        """
        初始化回复处理链

        Args:
            device_id: 设备 ID，用于标识要操作的手机设备
            file_manager: 文件管理器实例，用于保存对话历史
            tts_manager: TTS 管理器实例，用于语音播报
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

        # ReplyGraph 实例（延迟创建）
        self._reply_graph: ReplyGraph | None = None
        # 持续回复线程
        self._continuous_thread: threading.Thread | None = None
        
        logger.debug("ReplyChain 初始化完成，设备: %s", device_id if device_id else "未设置")

    def set_device_id(self, device_id: str) -> None:
        """
        设置设备 ID
        
        更新设备 ID 并重置 ReplyGraph 实例。
        
        Args:
            device_id: 新的设备 ID
        """
        logger.info("设置设备 ID: %s", device_id)
        self.device_id = device_id
        # 重置 ReplyGraph，下次使用时会重新创建
        self._reply_graph = None

    def _get_graph(self) -> ReplyGraph:
        """
        获取或创建 ReplyGraph
        
        如果 ReplyGraph 实例不存在则创建，否则返回现有实例。
        
        Returns:
            ReplyGraph 实例
        """
        if self._reply_graph is None:
            logger.debug("创建 ReplyGraph 实例")
            self._reply_graph = ReplyGraph(
                file_manager=self.file_manager,
                tts_manager=self.tts_manager
            )
        return self._reply_graph

    def single_reply(
        self,
        app_name: str,
        chat_object: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> tuple[bool, str]:
        """
        单次回复（支持 Callbacks）
        
        执行一次完整的回复流程：
        1. PhoneAgent 提取聊天记录
        2. 解析聊天记录，识别消息归属
        3. ChatAgent 生成回复
        4. PhoneAgent 发送回复
        
        Args:
            app_name: APP 名称，如 "微信"、"QQ" 等
            chat_object: 聊天对象名称
            callbacks: 自定义回调处理器列表
        
        Returns:
            tuple[bool, str]: (是否成功, 结果消息)
        
        使用示例：
            >>> success, result = chain.single_reply("微信", "张三")
        """
        logger.info("启动单次回复流程: APP=%s, 对象=%s", app_name, chat_object)
        logger.info("单次回复流程开始")

        # 准备回调处理器
        all_callbacks = prepare_callbacks_with_manager(self.callback_manager, callbacks=callbacks)

        # 创建 PhoneAgent
        phone_agent = PhoneAgent(self.device_id)

        # 步骤 1: 提取聊天记录
        logger.debug("提取聊天记录")
        success, records = phone_agent.extract_chat_records(app_name, chat_object)
        if not success:
            logger.error("提取聊天记录失败: %s", records)
            return False, f"提取聊天记录失败: {records}"

        # 保存聊天记录到日志文件
        if self.file_manager:
            self.file_manager.save_record_to_log(1, records, app_name, chat_object)
            logger.debug("已保存聊天记录到日志")

        # 步骤 2: 解析聊天记录
        logger.debug("解析聊天记录")
        client: ZhipuAI = get_zhipu_client()
        messages = parse_messages(records, client)
        if not messages:
            logger.warning("未能解析到聊天记录")
            return False, "未能解析到聊天记录"

        # 分类消息：区分对方消息和我方消息
        other_messages: list[str] = []
        my_messages: list[str] = []
        for msg in messages:
            content = msg.get("content", "").strip()
            # 过滤过短的消息
            if len(content) < MIN_MESSAGE_LENGTH:
                continue
            # 根据头像位置判断消息归属
            if msg.get("position") == "左侧有头像":
                other_messages.append(content)
            elif msg.get("position") == "右侧有头像":
                my_messages.append(content)

        # 检查是否有对方消息
        if not other_messages:
            logger.warning("没有发现对方消息")
            return False, "没有发现对方消息"

        # 获取最新消息和历史消息
        latest_message = other_messages[-1]
        history_messages = other_messages[:-1] if len(other_messages) > 1 else []
        
        logger.debug("对方消息数: %d, 我方消息数: %d", len(other_messages), len(my_messages))

        # 步骤 3: 生成回复
        logger.debug("生成回复")
        reply = generate_reply(latest_message, history_messages, client)

        # 检查回复有效性
        if not reply or len(reply) < MIN_MESSAGE_LENGTH:
            logger.warning("未能生成有效回复")
            return False, "未能生成有效回复"

        logger.info("生成回复成功，预览: %s...", reply[:50])

        # 步骤 4: 发送回复
        logger.debug("发送回复")
        send_success, send_result = phone_agent.send_message(app_name, chat_object, reply)

        if send_success:
            # 保存对话历史
            if self.file_manager:
                session_data: dict[str, Any] = {
                    "type": "chat_session",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "target_app": app_name,
                    "target_object": chat_object,
                    "cycle": 1,
                    "reply_generated": reply,
                    "other_messages": [latest_message],
                    "sent_success": True
                }
                self.file_manager.save_conversation_history(session_data)
                logger.debug("已保存对话历史")

            # TTS 语音播报
            if self.tts_manager and getattr(self.tts_manager, 'tts_enabled', False):
                threading.Timer(TTS_SPEAK_DELAY_REPLY, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
                logger.debug("已安排 TTS 播报")

            logger.info("单次回复成功")
            return True, f"回复已发送: {reply[:50]}..."
        else:
            logger.error("回复发送失败: %s", send_result)
            return False, f"回复发送失败: {send_result}"

    def continuous_reply(
        self,
        app_name: str,
        chat_object: str,
        max_cycles: int = 30
    ) -> tuple[bool, str]:
        """
        持续回复 - 使用 LangGraph 工作流
        
        启动持续回复流程，使用 LangGraph 状态图管理工作流。
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象名称
            max_cycles: 最大循环次数，默认为 30
        
        Returns:
            tuple[bool, str]: (是否成功, 结果消息)
        
        使用示例：
            >>> success, result = chain.continuous_reply("微信", "张三", max_cycles=20)
        """
        logger.info("启动持续回复: APP=%s, 对象=%s, 最大循环=%d", app_name, chat_object, max_cycles)
        
        # 获取或创建 ReplyGraph
        graph = self._get_graph()
        return graph.run(
            app_name=app_name,
            chat_object=chat_object,
            device_id=self.device_id,
            max_cycles=max_cycles
        )

    def start_continuous_reply_async(
        self,
        app_name: str,
        chat_object: str,
        callback: Callable[[bool, str], None] | None = None,
        max_cycles: int = 30
    ) -> None:
        """
        异步启动持续回复
        
        在后台线程中启动持续回复流程。
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象名称
            callback: 完成回调函数，接收 (是否成功, 结果消息)
            max_cycles: 最大循环次数
        
        使用示例：
            >>> def on_complete(success, result):
            ...     print(f"完成: {success}, {result}")
            >>> chain.start_continuous_reply_async("微信", "张三", callback=on_complete)
        """
        logger.info("异步启动持续回复: APP=%s, 对象=%s", app_name, chat_object)
        
        def run() -> None:
            """线程执行函数"""
            success, result = self.continuous_reply(app_name, chat_object, max_cycles)
            if callback:
                callback(success, result)

        # 创建并启动后台线程
        self._continuous_thread = threading.Thread(target=run, daemon=True)
        self._continuous_thread.start()

    def stop(self) -> None:
        """
        停止持续回复
        
        停止正在运行的持续回复流程。
        """
        logger.info("停止持续回复")
        if self._reply_graph:
            self._reply_graph.stop()

    def clear_messages(self) -> None:
        """
        清空消息列表
        
        LangGraph 版本自动管理状态，此方法保留为空实现以保持接口兼容。
        """
        logger.debug("清空消息列表（LangGraph 版本自动管理）")
        pass

    def is_running(self) -> bool:
        """
        检查是否正在运行
        
        Returns:
            bool: 是否正在运行持续回复
        """
        if self._reply_graph:
            return self._reply_graph.is_running()
        return False

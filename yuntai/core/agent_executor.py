#!/usr/bin/env python3
"""
Agent执行器模块
仅支持Android (PhoneAgent)
"""
import re
import sys
import os
import logging
import threading
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig
from yuntai.core.config import DEVICE_TYPE_ANDROID
from yuntai.prompts.agent_executor_prompt import CHAT_MESSAGE_PROMPT

logger = logging.getLogger(__name__)


class AgentExecutor:
    _stdin_read = None
    _stdin_write = None
    _original_stdin = None
    _user_confirmation_event = threading.Event()
    _is_waiting_for_confirmation = threading.Event()
    _lock = threading.Lock()

    def __init__(self, device_type: str = DEVICE_TYPE_ANDROID) -> None:
        """
        初始化Agent执行器

        Args:
            device_type: 设备类型 (android)
        """
        self.device_type = device_type
        AgentExecutor._user_confirmation_event.clear()
        AgentExecutor._is_waiting_for_confirmation.clear()

    def set_device_type(self, device_type: str) -> None:
        """设置设备类型"""
        self.device_type = device_type

    @classmethod
    def _setup_stdin_pipe(cls) -> None:
        """设置stdin管道用于模拟用户输入"""
        with cls._lock:
            if cls._stdin_write is None:
                cls._original_stdin = sys.stdin
                r, w = os.pipe()
                cls._stdin_read = r
                cls._stdin_write = w
                sys.stdin = os.fdopen(r, 'r')

    @classmethod
    def _cleanup_stdin_pipe(cls) -> None:
        """清理stdin管道"""
        with cls._lock:
            if cls._stdin_write is not None:
                try:
                    os.close(cls._stdin_write)
                except OSError as e:
                    logger.debug(f"关闭stdin写入端失败: {e}")
                cls._stdin_write = None
            if cls._stdin_read is not None:
                try:
                    os.close(cls._stdin_read)
                except OSError as e:
                    logger.debug(f"关闭stdin读取端失败: {e}")
                cls._stdin_read = None
            if cls._original_stdin is not None:
                sys.stdin = cls._original_stdin
                cls._original_stdin = None

    @classmethod
    def user_confirm(cls) -> bool:
        """用户点击确认按钮时调用此方法"""
        with cls._lock:
            if cls._stdin_write is not None:
                try:
                    os.write(cls._stdin_write, b'\n')
                    logger.info("已发送确认信号到管道")
                    cls._user_confirmation_event.set()
                    cls._is_waiting_for_confirmation.clear()
                    return True
                except OSError as e:
                    logger.warning(f"发送确认信号失败: {e}")
                    return False
            else:
                logger.warning("stdin管道未初始化，无法发送确认信号")
                cls._user_confirmation_event.set()
                cls._is_waiting_for_confirmation.clear()
                return False

    @classmethod
    def is_pipe_ready(cls) -> bool:
        """检查管道是否就绪"""
        return cls._stdin_write is not None

    def phone_agent_exec(self, task: str, args, task_type: str, device_id: str) -> tuple[str, list[str]]:
        """phone_agent执行 - 仅支持Android设备"""
        AgentExecutor._user_confirmation_event.clear()
        AgentExecutor._is_waiting_for_confirmation.clear()

        AgentExecutor._setup_stdin_pipe()
        try:
            model_config = ModelConfig(
                base_url=args.base_url,
                model_name=args.model,
                api_key=args.apikey,
                lang=args.lang,
            )

            return self._exec_android_agent(task, model_config, device_id, args)

        except Exception as e:
            return f"任务执行失败：{str(e)}", [str(e)]
        finally:
            AgentExecutor._cleanup_stdin_pipe()

    def _exec_android_agent(self, task: str, model_config: ModelConfig, device_id: str, args) -> tuple[str, list[str]]:
        """执行Android Agent"""
        agent_config = AgentConfig(
            max_steps=args.max_steps,
            device_id=device_id,
            verbose=False,
            lang=args.lang,
        )
        phone_agent = PhoneAgent(model_config=model_config, agent_config=agent_config)
        return self._execute_agent(task, phone_agent)

    def _execute_agent(self, task: str, agent) -> tuple[str, list[str]]:
        """通用Agent执行逻辑"""
        task = task.strip()
        if not task:
            return "指令为空", ["指令为空"]

        if "聊天" in task or "发消息" in task or "提取" in task:
            task = task + "\n\n" + CHAT_MESSAGE_PROMPT

        raw_result = agent.run(task)
        agent.reset()

        filtered_result = raw_result
        filtered_result = re.sub(
            r"\n==================================================\n💭 思考过程:\n--------------------------------------------------\n.+?\n==================================================\n",
            "", filtered_result, flags=re.DOTALL)
        filtered_result = re.sub(
            r"\n==================================================\n⏱️  性能指标:\n--------------------------------------------------\n.+?\n==================================================\n",
            "", filtered_result, flags=re.DOTALL)
        filtered_result = re.sub(r"\n{3,}", "\n\n", filtered_result).strip()

        return filtered_result, [raw_result, filtered_result]

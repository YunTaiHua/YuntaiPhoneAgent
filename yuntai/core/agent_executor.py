"""
Agent 执行器模块
================

本模块实现 Agent 执行器，仅支持 Android 设备（通过 PhoneAgent）。

主要功能：
    - 执行手机操作任务
    - 管理标准输入管道
    - 支持用户确认机制
    - 过滤和清理执行结果

类说明：
    - AgentExecutor: Agent 执行器类

使用示例：
    >>> from yuntai.core import AgentExecutor
    >>> 
    >>> # 创建执行器
    >>> executor = AgentExecutor()
    >>> 
    >>> # 执行任务
    >>> result, logs = executor.phone_agent_exec(task, args, "chat", device_id)
"""
from __future__ import annotations

import re
import sys
import os
import logging
import threading
from typing import Any

from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

from yuntai.core.config import DEVICE_TYPE_ANDROID
from yuntai.prompts.agent_executor_prompt import CHAT_MESSAGE_PROMPT

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Agent 执行器
    
    仅支持 Android 设备，通过 PhoneAgent 执行手机操作任务。
    使用类变量管理标准输入管道，支持用户确认机制。
    
    Attributes:
        device_type: 设备类型（android）
        _stdin_read: 标准输入读取端文件描述符（类变量）
        _stdin_write: 标准输入写入端文件描述符（类变量）
        _original_stdin: 原始标准输入（类变量）
        _user_confirmation_event: 用户确认事件（类变量）
        _is_waiting_for_confirmation: 等待确认状态（类变量）
        _lock: 线程锁（类变量）
    
    使用示例：
        >>> executor = AgentExecutor()
        >>> result, logs = executor.phone_agent_exec(task, args, "chat", device_id)
    """

    # 类变量：标准输入管道相关
    _stdin_read: int | None = None
    _stdin_write: int | None = None
    _original_stdin = None
    
    # 类变量：用户确认相关
    _user_confirmation_event: threading.Event = threading.Event()
    _is_waiting_for_confirmation: threading.Event = threading.Event()
    
    # 类变量：线程锁
    _lock: threading.Lock = threading.Lock()

    def __init__(self, device_type: str = DEVICE_TYPE_ANDROID) -> None:
        """
        初始化 Agent 执行器
        
        Args:
            device_type: 设备类型，默认为 Android
        """
        # 存储设备类型
        self.device_type = device_type
        
        # 清除用户确认事件状态
        AgentExecutor._user_confirmation_event.clear()
        AgentExecutor._is_waiting_for_confirmation.clear()
        
        logger.debug("AgentExecutor 初始化完成，设备类型: %s", device_type)

    def set_device_type(self, device_type: str) -> None:
        """
        设置设备类型
        
        Args:
            device_type: 新的设备类型
        """
        logger.debug("设置设备类型: %s", device_type)
        self.device_type = device_type

    @classmethod
    def _setup_stdin_pipe(cls) -> None:
        """
        设置标准输入管道
        
        创建管道用于模拟用户输入，解决 PhoneAgent 需要用户确认的问题。
        使用线程锁确保线程安全。
        """
        with cls._lock:
            # 检查管道是否已创建
            if cls._stdin_write is None:
                # 保存原始标准输入
                cls._original_stdin = sys.stdin
                
                # 创建管道
                r, w = os.pipe()
                cls._stdin_read = r
                cls._stdin_write = w
                
                # 替换标准输入为管道读取端
                sys.stdin = os.fdopen(r, 'r')
                
                logger.debug("标准输入管道已创建")

    @classmethod
    def _cleanup_stdin_pipe(cls) -> None:
        """
        清理标准输入管道
        
        关闭管道文件描述符，恢复原始标准输入。
        使用线程锁确保线程安全。
        """
        with cls._lock:
            # 关闭写入端
            if cls._stdin_write is not None:
                try:
                    os.close(cls._stdin_write)
                except OSError as e:
                    logger.debug("关闭 stdin 写入端失败: %s", str(e))
                cls._stdin_write = None
            
            # 关闭读取端
            if cls._stdin_read is not None:
                try:
                    os.close(cls._stdin_read)
                except OSError as e:
                    logger.debug("关闭 stdin 读取端失败: %s", str(e))
                cls._stdin_read = None
            
            # 恢复原始标准输入
            if cls._original_stdin is not None:
                sys.stdin = cls._original_stdin
                cls._original_stdin = None
                
            logger.debug("标准输入管道已清理")

    @classmethod
    def user_confirm(cls) -> bool:
        """
        用户确认
        
        当用户点击确认按钮时调用此方法，向管道发送确认信号。
        
        Returns:
            bool: 是否成功发送确认信号
        
        使用示例：
            >>> AgentExecutor.user_confirm()
        """
        with cls._lock:
            # 检查管道是否就绪
            if cls._stdin_write is not None:
                try:
                    # 向管道发送换行符作为确认信号
                    os.write(cls._stdin_write, b'\n')
                    logger.info("已发送确认信号到管道")
                    
                    # 设置确认事件
                    cls._user_confirmation_event.set()
                    cls._is_waiting_for_confirmation.clear()
                    return True
                except OSError as e:
                    logger.warning("发送确认信号失败: %s", str(e))
                    return False
            else:
                # 管道未初始化，直接设置事件
                logger.warning("stdin 管道未初始化，无法发送确认信号")
                cls._user_confirmation_event.set()
                cls._is_waiting_for_confirmation.clear()
                return False

    @classmethod
    def is_pipe_ready(cls) -> bool:
        """
        检查管道是否就绪
        
        Returns:
            bool: 管道是否已创建并就绪
        """
        return cls._stdin_write is not None

    def phone_agent_exec(
        self,
        task: str,
        args: Any,
        task_type: str,
        device_id: str
    ) -> tuple[str, list[str]]:
        """
        执行 PhoneAgent 任务
        
        仅支持 Android 设备，执行指定的手机操作任务。
        
        Args:
            task: 任务描述
            args: 参数对象，包含 base_url, model, apikey, lang, max_steps 等属性
            task_type: 任务类型，如 "chat"、"operation" 等
            device_id: 设备 ID
        
        Returns:
            tuple[str, list[str]]: (过滤后的结果, [原始结果, 过滤后的结果])
        
        使用示例：
            >>> result, logs = executor.phone_agent_exec("打开微信", args, "operation", "device_123")
        """
        logger.info("执行 PhoneAgent 任务: %s, 设备: %s", task[:50] if len(task) > 50 else task, device_id)
        
        # 清除确认事件状态
        AgentExecutor._user_confirmation_event.clear()
        AgentExecutor._is_waiting_for_confirmation.clear()

        # 设置标准输入管道
        AgentExecutor._setup_stdin_pipe()
        
        try:
            # 创建模型配置
            model_config = ModelConfig(
                base_url=args.base_url,
                model_name=args.model,
                api_key=args.apikey,
                lang=args.lang,
            )

            # 执行 Android Agent
            return self._exec_android_agent(task, model_config, device_id, args)

        except Exception as e:
            # 记录错误日志
            logger.error("任务执行失败: %s", str(e), exc_info=True)
            return f"任务执行失败：{str(e)}", [str(e)]
        finally:
            # 确保清理管道
            AgentExecutor._cleanup_stdin_pipe()

    def _exec_android_agent(
        self,
        task: str,
        model_config: ModelConfig,
        device_id: str,
        args: Any
    ) -> tuple[str, list[str]]:
        """
        执行 Android Agent
        
        创建并配置 PhoneAgent，执行任务。
        
        Args:
            task: 任务描述
            model_config: 模型配置
            device_id: 设备 ID
            args: 参数对象
        
        Returns:
            tuple[str, list[str]]: (过滤后的结果, [原始结果, 过滤后的结果])
        """
        logger.debug("创建 Android Agent 配置")
        
        # 创建 Agent 配置
        agent_config = AgentConfig(
            max_steps=args.max_steps,
            device_id=device_id,
            verbose=False,  # 禁用详细输出
            lang=args.lang,
        )
        
        # 创建 PhoneAgent 实例
        phone_agent = PhoneAgent(model_config=model_config, agent_config=agent_config)
        
        # 执行任务
        return self._execute_agent(task, phone_agent)

    def _execute_agent(
        self,
        task: str,
        agent: PhoneAgent
    ) -> tuple[str, list[str]]:
        """
        通用 Agent 执行逻辑
        
        执行任务并过滤结果，移除思考过程和性能指标。
        
        Args:
            task: 任务描述
            agent: PhoneAgent 实例
        
        Returns:
            tuple[str, list[str]]: (过滤后的结果, [原始结果, 过滤后的结果])
        """
        # 清理任务字符串
        task = task.strip()
        if not task:
            logger.warning("任务为空")
            return "指令为空", ["指令为空"]

        # 如果是聊天相关任务，添加额外的提示词
        if "聊天" in task or "发消息" in task or "提取" in task:
            task = task + "\n\n" + CHAT_MESSAGE_PROMPT
            logger.debug("已添加聊天消息提示词")

        # 执行任务
        logger.debug("开始执行任务")
        raw_result = agent.run(task)
        
        # 重置 Agent 状态
        agent.reset()

        # 过滤结果：移除思考过程
        filtered_result = raw_result
        filtered_result = re.sub(
            r"\n==================================================\n💭 思考过程:\n--------------------------------------------------\n.+?\n==================================================\n",
            "", filtered_result, flags=re.DOTALL)
        
        # 过滤结果：移除性能指标
        filtered_result = re.sub(
            r"\n==================================================\n⏱️  性能指标:\n--------------------------------------------------\n.+?\n==================================================\n",
            "", filtered_result, flags=re.DOTALL)
        
        # 清理多余空行
        filtered_result = re.sub(r"\n{3,}", "\n\n", filtered_result).strip()

        logger.debug("任务执行完成，结果长度: %d", len(filtered_result))
        return filtered_result, [raw_result, filtered_result]

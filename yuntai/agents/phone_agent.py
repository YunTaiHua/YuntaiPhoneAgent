"""
手机操作 Agent 模块
===================

本模块实现手机操作 Agent，使用 ZHIPU_MODEL 执行手机操作。

主要功能：
    - 手机操作执行：通过 PhoneAgent 执行各种手机操作
    - APP 管理：打开、关闭应用程序
    - 消息处理：提取聊天记录、发送消息
    - 管道管理：管理标准输入输出管道

类说明：
    - PhoneAgentWrapper: PhoneAgent 包装器，封装底层操作
    - PhoneAgent: 手机操作 Agent 类，提供高级接口

使用示例：
    >>> from yuntai.agents import PhoneAgent
    >>> 
    >>> agent = PhoneAgent(device_id="your_device_id")
    >>> success, result = agent.open_app("微信")
    >>> print(f"操作结果: {result}")
"""
from __future__ import annotations

import logging

from phone_agent import PhoneAgent as ExternalPhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

from yuntai.core.config import (
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_MODEL,
    ZHIPU_CHAT_MODEL,
    PHONE_AGENT_MAX_STEPS,
    PHONE_AGENT_LANG,
    PHONE_SUCCESS_KEYWORDS,
)
from yuntai.prompts import (
    PHONE_OPERATION_PROMPT,
    PHONE_EXTRACT_CHAT_PROMPT,
    PHONE_SEND_MESSAGE_PROMPT,
    PHONE_EXTRACT_TASK_PROMPT,
    PHONE_SEND_TASK_QQ,
    PHONE_SEND_TASK_WECHAT,
    PHONE_SEND_TASK_DEFAULT,
)
from yuntai.core.agent_executor import AgentExecutor

# 导入聊天消息提示词
from yuntai.prompts.agent_executor_prompt import CHAT_MESSAGE_PROMPT

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class PhoneAgentWrapper:
    """
    手机操作 Agent 包装器
    
    封装外部 PhoneAgent 库的操作，提供统一的接口。
    管理 Agent 实例的创建、重置和管道配置。
    
    Attributes:
        device_id: 设备 ID
        max_steps: 最大执行步数
        _agent: 内部 PhoneAgent 实例
    
    使用示例：
        >>> wrapper = PhoneAgentWrapper("device_123")
        >>> success, result = wrapper.execute("打开微信")
    """

    def __init__(self, device_id: str, max_steps: int = PHONE_AGENT_MAX_STEPS) -> None:
        """
        初始化手机操作 Agent 包装器
        
        Args:
            device_id: 设备 ID，用于标识要操作的手机设备
            max_steps: 最大执行步数，防止无限循环，默认使用配置值
        """
        # 存储设备 ID
        self.device_id = device_id
        # 存储最大执行步数
        self.max_steps = max_steps
        # 内部 PhoneAgent 实例，延迟创建
        self._agent: ExternalPhoneAgent | None = None
        
        logger.debug("PhoneAgentWrapper 初始化完成，设备: %s", device_id)
    
    def _create_agent(self) -> ExternalPhoneAgent:
        """
        创建 PhoneAgent 实例
        
        配置模型和 Agent 参数，创建外部 PhoneAgent 实例。
        
        Returns:
            ExternalPhoneAgent: 配置好的 PhoneAgent 实例
        """
        logger.info("创建 PhoneAgent 实例，设备: %s", self.device_id)
        
        # 配置模型参数
        model_config = ModelConfig(
            base_url=ZHIPU_API_BASE_URL,
            model_name=ZHIPU_MODEL,
            api_key=ZHIPU_API_KEY,
            lang=PHONE_AGENT_LANG,
        )
        
        # 配置 Agent 参数
        agent_config = AgentConfig(
            max_steps=self.max_steps,
            device_id=self.device_id,
            verbose=False,  # 禁用详细输出
            lang=PHONE_AGENT_LANG,
        )
        
        # 创建并返回 Agent 实例
        return ExternalPhoneAgent(model_config=model_config, agent_config=agent_config)
    
    def _get_agent(self) -> ExternalPhoneAgent:
        """
        获取 PhoneAgent 实例（延迟创建）
        
        如果实例不存在则创建，否则返回现有实例。
        
        Returns:
            ExternalPhoneAgent: PhoneAgent 实例
        """
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent
    
    def _reset_agent(self) -> None:
        """
        重置 Agent 实例
        
        清理当前 Agent 实例的状态并置空，
        下次使用时会重新创建。
        """
        if self._agent:
            logger.debug("重置 PhoneAgent 实例")
            self._agent.reset()
            self._agent = None

    def _setup_pipe(self) -> None:
        """
        设置标准输入管道
        
        配置用于与外部 Agent 通信的管道。
        """
        logger.debug("设置标准输入管道")
        AgentExecutor._setup_stdin_pipe()

    def _cleanup_pipe(self) -> None:
        """
        清理标准输入管道
        
        清理管道资源，避免资源泄漏。
        """
        logger.debug("清理标准输入管道")
        AgentExecutor._cleanup_stdin_pipe()

    def execute(self, task: str) -> tuple[bool, str]:
        """
        执行手机操作
        
        执行指定的手机操作任务，返回执行结果。
        
        Args:
            task: 操作指令，描述要执行的任务
        
        Returns:
            tuple[bool, str]: (是否成功, 执行结果描述)
        
        使用示例：
            >>> success, result = wrapper.execute("打开微信")
            >>> print(f"成功: {success}, 结果: {result}")
        """
        logger.info("执行手机操作: %s", task[:50] if len(task) > 50 else task)
        
        # 设置管道
        self._setup_pipe()
        try:
            # 获取 Agent 实例
            agent = self._get_agent()
            # 构建带提示词的任务
            task_with_prompt = task + "\n\n" + PHONE_OPERATION_PROMPT
            # 执行任务
            result = agent.run(task_with_prompt)
            # 重置 Agent
            self._reset_agent()
            
            # 判断是否成功
            success = "失败" not in result and "错误" not in result
            logger.info("手机操作完成，成功: %s", success)
            return success, result
        except Exception as e:
            # 记录错误日志
            logger.error("执行手机操作失败: %s", str(e), exc_info=True)
            return False, f"执行失败: {str(e)}"
        finally:
            # 确保清理管道
            self._cleanup_pipe()
    
    def open_app(self, app_name: str) -> tuple[bool, str]:
        """
        打开 APP
        
        快捷方法，用于打开指定的应用程序。
        
        Args:
            app_name: APP 名称，如 "微信"、"QQ" 等
        
        Returns:
            tuple[bool, str]: (是否成功, 执行结果描述)
        
        使用示例：
            >>> success, result = wrapper.open_app("微信")
        """
        logger.info("打开 APP: %s", app_name)
        return self.execute(f"打开{app_name}")

    def extract_chat_records(
        self,
        app_name: str,
        chat_object: str
    ) -> tuple[bool, str]:
        """
        提取聊天记录
        
        从指定的 APP 和聊天对象中提取聊天记录。
        
        Args:
            app_name: APP 名称，如 "微信"、"QQ" 等
            chat_object: 聊天对象名称
        
        Returns:
            tuple[bool, str]: (是否成功, 聊天记录内容)
        
        使用示例：
            >>> success, records = wrapper.extract_chat_records("微信", "张三")
            >>> print(records)
        """
        logger.info("提取聊天记录: APP=%s, 对象=%s", app_name, chat_object)
        
        # 构建提取任务
        task = PHONE_EXTRACT_TASK_PROMPT.format(
            app_name=app_name,
            chat_object=chat_object,
            extra_prompt=""
        )
        task_with_prompt = task + "\n\n" + PHONE_EXTRACT_CHAT_PROMPT
        
        # 设置管道
        self._setup_pipe()
        try:
            # 获取 Agent 并执行
            agent = self._get_agent()
            result = agent.run(task_with_prompt)
            # 重置 Agent
            self._reset_agent()
            logger.info("聊天记录提取完成，长度: %d", len(result))
            return True, result
        except Exception as e:
            # 记录错误日志
            logger.error("提取聊天记录失败: %s", str(e), exc_info=True)
            return False, f"提取失败: {str(e)}"
        finally:
            # 确保清理管道
            self._cleanup_pipe()
    
    def send_message(
        self,
        app_name: str,
        chat_object: str,
        message: str
    ) -> tuple[bool, str]:
        """
        发送消息
        
        向指定的 APP 和聊天对象发送消息。
        
        Args:
            app_name: APP 名称，如 "微信"、"QQ" 等
            chat_object: 聊天对象名称
            message: 要发送的消息内容
        
        Returns:
            tuple[bool, str]: (是否成功, 执行结果描述)
        
        使用示例：
            >>> success, result = wrapper.send_message("微信", "张三", "你好")
        """
        logger.info("发送消息: APP=%s, 对象=%s, 消息长度=%d", app_name, chat_object, len(message))
        
        # 根据不同的 APP 选择不同的任务模板
        if app_name == "QQ":
            task = PHONE_SEND_TASK_QQ.format(
                app_name=app_name,
                chat_object=chat_object,
                message=message
            )
        elif app_name == "微信":
            task = PHONE_SEND_TASK_WECHAT.format(
                app_name=app_name,
                chat_object=chat_object,
                message=message
            )
        else:
            task = PHONE_SEND_TASK_DEFAULT.format(
                app_name=app_name,
                chat_object=chat_object,
                message=message
            )
        
        # 设置管道
        self._setup_pipe()
        try:
            # 获取 Agent 并执行
            agent = self._get_agent()
            result = agent.run(task)
            # 重置 Agent
            self._reset_agent()
            
            # 检查是否成功（通过关键词判断）
            success_keywords = PHONE_SUCCESS_KEYWORDS
            success = any(keyword in result for keyword in success_keywords)
            logger.info("消息发送完成，成功: %s", success)
            return success, result
        except Exception as e:
            # 记录错误日志
            logger.error("发送消息失败: %s", str(e), exc_info=True)
            return False, f"发送失败: {str(e)}"
        finally:
            # 确保清理管道
            self._cleanup_pipe()


class PhoneAgent:
    """
    手机操作 Agent 类
    
    提供高级的手机操作接口，封装 PhoneAgentWrapper。
    支持设备切换和操作执行。
    
    Attributes:
        device_id: 设备 ID
        _wrapper: 内部 PhoneAgentWrapper 实例
        _last_extract_result: 上次提取结果缓存
    
    使用示例：
        >>> agent = PhoneAgent("device_123")
        >>> success, result = agent.open_app("微信")
        >>> success, records = agent.extract_chat_records("微信", "张三")
    """

    def __init__(self, device_id: str = "") -> None:
        """
        初始化手机操作 Agent
        
        Args:
            device_id: 设备 ID，可选，后续可通过 set_device_id 设置
        """
        # 存储设备 ID
        self.device_id = device_id
        # 内部包装器实例，延迟创建
        self._wrapper: PhoneAgentWrapper | None = None

        # 缓存上次提取结果
        self._last_extract_result: tuple[bool, str] = (False, "")
        
        logger.debug("PhoneAgent 初始化完成，设备: %s", device_id if device_id else "未设置")

    def set_device_id(self, device_id: str) -> None:
        """
        设置设备 ID
        
        更新设备 ID 并重置内部包装器。
        
        Args:
            device_id: 新的设备 ID
        """
        logger.info("设置设备 ID: %s", device_id)
        self.device_id = device_id
        # 重置包装器，下次使用时会重新创建
        self._wrapper = None

    def _get_wrapper(self) -> PhoneAgentWrapper:
        """
        获取包装器实例（延迟创建）
        
        如果包装器不存在则创建，否则返回现有实例。
        
        Returns:
            PhoneAgentWrapper: 包装器实例
        """
        if self._wrapper is None:
            self._wrapper = PhoneAgentWrapper(self.device_id)
        return self._wrapper

    def execute_operation(self, task: str) -> tuple[bool, str]:
        """
        执行复杂操作
        
        执行指定的手机操作任务。
        
        Args:
            task: 操作指令
        
        Returns:
            tuple[bool, str]: (是否成功, 执行结果)
        
        使用示例：
            >>> success, result = agent.execute_operation("在微信中找到张三并发送你好")
        """
        logger.info("执行复杂操作: %s", task[:50] if len(task) > 50 else task)
        return self._get_wrapper().execute(task)

    
    def open_app(self, app_name: str) -> tuple[bool, str]:
        """
        打开 APP
        
        快捷方法，打开指定的应用程序。
        
        Args:
            app_name: APP 名称
        
        Returns:
            tuple[bool, str]: (是否成功, 执行结果)
        """
        logger.info("打开 APP: %s", app_name)
        return self._get_wrapper().open_app(app_name)

    
    def extract_chat_records(self, app_name: str, chat_object: str) -> tuple[bool, str]:
        """
        提取聊天记录
        
        从指定的 APP 和聊天对象中提取聊天记录。
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象名称
        
        Returns:
            tuple[bool, str]: (是否成功, 聊天记录)
        """
        logger.info("提取聊天记录: APP=%s, 对象=%s", app_name, chat_object)
        result = self._get_wrapper().extract_chat_records(app_name, chat_object)
        # 缓存结果
        self._last_extract_result = result
        return result
    
    def send_message(self, app_name: str, chat_object: str, message: str) -> tuple[bool, str]:
        """
        发送消息
        
        向指定的 APP 和聊天对象发送消息。
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象名称
            message: 消息内容
        
        Returns:
            tuple[bool, str]: (是否成功, 执行结果)
        """
        logger.info("发送消息: APP=%s, 对象=%s", app_name, chat_object)
        return self._get_wrapper().send_message(app_name, chat_object, message)

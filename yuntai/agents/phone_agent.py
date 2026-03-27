"""手机操作 Agent，使用 ZHIPU_MODEL 执行手机操作"""
from __future__ import annotations

import re

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


from yuntai.prompts.agent_executor_prompt import CHAT_MESSAGE_PROMPT


class PhoneAgentWrapper:
    """手机操作 Agent 包装器"""

    def __init__(self, device_id: str, max_steps: int = PHONE_AGENT_MAX_STEPS) -> None:
        self.device_id = device_id
        self.max_steps = max_steps
        self._agent: ExternalPhoneAgent | None = None
    
    def _create_agent(self) -> ExternalPhoneAgent:
        """创建 PhoneAgent 实例"""
        model_config = ModelConfig(
            base_url=ZHIPU_API_BASE_URL,
            model_name=ZHIPU_MODEL,
            api_key=ZHIPU_API_KEY,
            lang=PHONE_AGENT_LANG,
        )
        agent_config = AgentConfig(
            max_steps=self.max_steps,
            device_id=self.device_id,
            verbose=False,
            lang=PHONE_AGENT_LANG,
        )
        return ExternalPhoneAgent(model_config=model_config, agent_config=agent_config)
    
    def _get_agent(self) -> ExternalPhoneAgent:
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent
    
    def _reset_agent(self) -> None:
        if self._agent:
            self._agent.reset()
            self._agent = None

    def _setup_pipe(self) -> None:
        """设置管道"""
        AgentExecutor._setup_stdin_pipe()

    def _cleanup_pipe(self) -> None:
        """清理管道"""
        AgentExecutor._cleanup_stdin_pipe()

    def execute(self, task: str) -> tuple[bool, str]:
        """
        执行手机操作
        
        Args:
            task: 操作指令
        
        Returns:
            (是否成功, 执行结果)
        """
        self._setup_pipe()
        try:
            agent = self._get_agent()
            task_with_prompt = task + "\n\n" + PHONE_OPERATION_PROMPT
            result = agent.run(task_with_prompt)
            self._reset_agent()
            
            success = "失败" not in result and "错误" not in result
            return success, result
        except Exception as e:
            return False, f"执行失败: {str(e)}"
        finally:
            self._cleanup_pipe()
    
    def open_app(self, app_name: str) -> tuple[bool, str]:
        """打开 APP"""
        return self.execute(f"打开{app_name}")

    def extract_chat_records(
        self,
        app_name: str,
        chat_object: str
    ) -> tuple[bool, str]:
        """
        提取聊天记录
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
        
        Returns:
            (是否成功, 聊天记录)
        """
        task = PHONE_EXTRACT_TASK_PROMPT.format(
            app_name=app_name,
            chat_object=chat_object,
            extra_prompt=""
        )
        task_with_prompt = task + "\n\n" + PHONE_EXTRACT_CHAT_PROMPT
        
        self._setup_pipe()
        try:
            agent = self._get_agent()
            result = agent.run(task_with_prompt)
            self._reset_agent()
            return True, result
        except Exception as e:
            return False, f"提取失败: {str(e)}"
        finally:
            self._cleanup_pipe()
    
    def send_message(
        self,
        app_name: str,
        chat_object: str,
        message: str
    ) -> tuple[bool, str]:
        """
        发送消息
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            message: 消息内容
        
        Returns:
            (是否成功, 执行结果)
        """
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
        
        self._setup_pipe()
        try:
            agent = self._get_agent()
            result = agent.run(task)
            self._reset_agent()
            
            success_keywords = PHONE_SUCCESS_KEYWORDS
            success = any(keyword in result for keyword in success_keywords)
            return success, result
        except Exception as e:
            return False, f"发送失败: {str(e)}"
        finally:
            self._cleanup_pipe()


class PhoneAgent:
    """手机操作 Agent 类"""

    def __init__(self, device_id: str = "") -> None:
        self.device_id = device_id
        self._wrapper: PhoneAgentWrapper | None = None

        self._last_extract_result: tuple[bool, str] = (False, "")

    def set_device_id(self, device_id: str) -> None:
        """设置设备 ID"""
        self.device_id = device_id
        self._wrapper = None

    def _get_wrapper(self) -> PhoneAgentWrapper:
        if self._wrapper is None:
            self._wrapper = PhoneAgentWrapper(self.device_id)
        return self._wrapper

    def execute_operation(self, task: str) -> tuple[bool, str]:
        """执行复杂操作"""
        return self._get_wrapper().execute(task)

    
    def open_app(self, app_name: str) -> tuple[bool, str]:
        """打开 APP"""
        return self._get_wrapper().open_app(app_name)

    
    def extract_chat_records(self, app_name: str, chat_object: str) -> tuple[bool, str]:
        """提取聊天记录"""
        return self._get_wrapper().extract_chat_records(app_name, chat_object)
    
    def send_message(self, app_name: str, chat_object: str, message: str) -> tuple[bool, str]:
        """发送消息"""
        return self._get_wrapper().send_message(app_name, chat_object, message)

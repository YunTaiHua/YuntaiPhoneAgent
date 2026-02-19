"""
手机操作 Agent
使用 ZHIPU_MODEL 执行手机操作
"""
import re
from typing import Dict, Any, Optional, Tuple

from phone_agent import PhoneAgent as ExternalPhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig

from yuntai.core.config import (
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_MODEL,
    ZHIPU_CHAT_MODEL,
)
from yuntai.prompts import PHONE_OPERATION_PROMPT, PHONE_EXTRACT_CHAT_PROMPT
from yuntai.core.agent_executor import AgentExecutor


class PhoneAgentWrapper:
    """手机操作 Agent 包装器"""
    
    def __init__(self, device_id: str, max_steps: int = 100):
        self.device_id = device_id
        self.max_steps = max_steps
        self._agent: Optional[ExternalPhoneAgent] = None
    
    def _create_agent(self) -> ExternalPhoneAgent:
        """创建 PhoneAgent 实例"""
        model_config = ModelConfig(
            base_url=ZHIPU_API_BASE_URL,
            model_name=ZHIPU_MODEL,
            api_key=ZHIPU_API_KEY,
            lang="cn",
        )
        agent_config = AgentConfig(
            max_steps=self.max_steps,
            device_id=self.device_id,
            verbose=False,
            lang="cn",
        )
        return ExternalPhoneAgent(model_config=model_config, agent_config=agent_config)
    
    def _get_agent(self) -> "ExternalPhoneAgent":
        if self._agent is None:
            self._agent = self._create_agent()
        return self._agent
    
    def _reset_agent(self):
        if self._agent:
            self._agent.reset()
            self._agent = None
    
    def _setup_pipe(self):
        """设置管道"""
        AgentExecutor._setup_stdin_pipe()
    
    def _cleanup_pipe(self):
        """清理管道"""
        AgentExecutor._cleanup_stdin_pipe()
    
    def execute(self, task: str) -> Tuple[bool, str]:
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
    
    def open_app(self, app_name: str) -> Tuple[bool, str]:
        """打开 APP"""
        return self.execute(f"打开{app_name}")
    
    def extract_chat_records(
        self, 
        app_name: str, 
        chat_object: str
    ) -> Tuple[bool, str]:
        """
        提取聊天记录
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
        
        Returns:
            (是否成功, 聊天记录)
        """
        task = f"""在{app_name}中进入{chat_object}的聊天窗口，向下滑动1次，提取当前屏幕可见的聊天记录

重要说明：
1. 键盘已经关闭，不需要点击聊天区空白处关闭键盘
2. 直接向下滑动1次即可
3. 准确描述每条消息的气泡颜色（如白色、红色、蓝色、绿色等）
4. 准确描述每条消息的头像位置（左侧有头像/右侧有头像）
5. 不要判断发送方，只需描述客观信息
6. 不要简化描述，必须明确说明头像位置
7. 不要向上滑动
"""
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
    ) -> Tuple[bool, str]:
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
            task = f"在{app_name}中给{chat_object}发送消息：{message}，点击右下角的发送按钮，然后使用Back按钮关闭键盘"
        elif app_name == "微信":
            task = f"在{app_name}中给{chat_object}发送消息：{message}，点击右侧的发送按钮，然后使用Back按钮关闭键盘"
        else:
            task = f"在{app_name}中给{chat_object}发送消息：{message}，然后点击发送按钮，然后使用Back按钮关闭键盘"
        
        self._setup_pipe()
        try:
            agent = self._get_agent()
            result = agent.run(task)
            self._reset_agent()
            
            success_keywords = ["已成功发送消息", "消息已成功发送", "发送了消息", "发送成功", "发送了", "已发送"]
            success = any(keyword in result for keyword in success_keywords)
            return success, result
        except Exception as e:
            return False, f"发送失败: {str(e)}"
        finally:
            self._cleanup_pipe()


class PhoneAgent:
    """手机操作 Agent 类"""
    
    def __init__(self, device_id: str = ""):
        self.device_id = device_id
        self._wrapper: Optional[PhoneAgentWrapper] = None
    
    def set_device_id(self, device_id: str):
        """设置设备 ID"""
        self.device_id = device_id
        self._wrapper = None
    
    def _get_wrapper(self) -> PhoneAgentWrapper:
        if self._wrapper is None:
            self._wrapper = PhoneAgentWrapper(self.device_id)
        return self._wrapper
    
    def execute_operation(self, task: str) -> Tuple[bool, str]:
        """执行复杂操作"""
        return self._get_wrapper().execute(task)
    
    def open_app(self, app_name: str) -> Tuple[bool, str]:
        """打开 APP"""
        return self._get_wrapper().open_app(app_name)
    
    def extract_chat_records(self, app_name: str, chat_object: str) -> Tuple[bool, str]:
        """提取聊天记录"""
        return self._get_wrapper().extract_chat_records(app_name, chat_object)
    
    def send_message(self, app_name: str, chat_object: str, message: str) -> Tuple[bool, str]:
        """发送消息"""
        return self._get_wrapper().send_message(app_name, chat_object, message)

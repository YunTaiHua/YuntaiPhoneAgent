"""
任务判断 Agent 模块
===================

本模块实现任务判断 Agent，使用 ZHIPU_JUDGEMENT_MODEL 判断任务类型，支持 LangChain Callbacks 记录执行过程。

主要功能：
    - 任务类型判断：分析用户输入，判断任务类型
    - 目标提取：提取目标 APP、聊天对象等信息
    - 后备机制：当 AI 判断失败时使用规则匹配

类说明：
    - TaskJudgementResult: 任务判断结果数据类
    - JudgementAgent: 任务判断 Agent 类

任务类型常量：
    - TASK_TYPE_FREE_CHAT: 自由聊天
    - TASK_TYPE_BASIC_OPERATION: 基础操作（如打开 APP）
    - TASK_TYPE_SINGLE_REPLY: 单次回复
    - TASK_TYPE_CONTINUOUS_REPLY: 持续回复
    - TASK_TYPE_COMPLEX_OPERATION: 复杂操作

使用示例：
    >>> from yuntai.agents import JudgementAgent
    >>> 
    >>> agent = JudgementAgent()
    >>> result = agent.judge("打开微信给张三发消息")
    >>> print(result.task_type, result.target_app, result.target_object)
"""
import json
import logging
import re
from dataclasses import dataclass

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler

from yuntai.models import get_judgement_model
from yuntai.prompts import (
    TASK_JUDGEMENT_PROMPT,
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)
from yuntai.tools.callback_utils import prepare_callbacks_with_manager
from yuntai.callbacks import get_callback_manager

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


@dataclass
class TaskJudgementResult:
    """
    任务判断结果数据类
    
    用于存储任务判断的结果，包含任务类型、目标应用、目标对象等信息。
    
    Attributes:
        task_type: 任务类型，取值为 TASK_TYPE_* 常量之一
        target_app: 目标应用名称，如 "微信"、"QQ" 等
        target_object: 目标对象名称，如聊天对象的名称
        is_auto: 是否为自动任务（持续执行）
        specific_content: 具体内容，如要发送的消息内容
    
    使用示例：
        >>> result = TaskJudgementResult(
        ...     task_type=TASK_TYPE_SINGLE_REPLY,
        ...     target_app="微信",
        ...     target_object="张三",
        ...     is_auto=False,
        ...     specific_content="你好"
        ... )
    """

    task_type: str
    target_app: str
    target_object: str
    is_auto: bool
    specific_content: str

    def to_dict(self) -> dict[str, object]:
        """
        将结果转换为字典格式
        
        便于序列化和传递给其他组件。
        
        Returns:
            包含所有属性的字典
        
        使用示例：
            >>> result_dict = result.to_dict()
            >>> print(result_dict["task_type"])
        """
        return {
            "task_type": self.task_type,
            "target_app": self.target_app,
            "target_object": self.target_object,
            "is_auto": self.is_auto,
            "specific_content": self.specific_content,
        }


class JudgementAgent:
    """
    任务判断 Agent 类
    
    支持 Callbacks 记录执行过程，提供 AI 判断和规则后备两种机制。
    
    Attributes:
        model: LangChain 聊天模型实例
        system_prompt: 系统提示词
        callback_manager: 回调管理器实例
    
    使用示例：
        >>> agent = JudgementAgent()
        >>> result = agent.judge("打开微信发消息给张三")
        >>> if result.task_type == TASK_TYPE_SINGLE_REPLY:
        ...     print(f"需要给 {result.target_object} 发消息")
    """

    def __init__(self, model: BaseChatModel | None = None, callback_manager=None) -> None:
        """
        初始化任务判断 Agent
        
        Args:
            model: LangChain 聊天模型实例，如果为 None 则使用默认判断模型
        """
        # 初始化模型，使用默认判断模型或传入的模型
        self.model = model or get_judgement_model()
        # 系统提示词
        self.system_prompt = TASK_JUDGEMENT_PROMPT

        # 获取回调管理器单例
        self.callback_manager = callback_manager or get_callback_manager()
        
        logger.debug("JudgementAgent 初始化完成")

    def judge(
        self,
        user_input: str,
        callbacks: list[BaseCallbackHandler] | None = None
    ) -> TaskJudgementResult:
        """
        判断任务类型（支持 Callbacks）
        
        分析用户输入，判断任务类型并提取相关信息。
        如果 AI 判断失败，会自动使用后备规则匹配。
        
        Args:
            user_input: 用户输入的文本
            callbacks: 自定义回调处理器列表，可选
        
        Returns:
            TaskJudgementResult: 任务判断结果对象
        
        使用示例：
            >>> result = agent.judge("打开微信给张三发消息说你好")
            >>> print(result.task_type)  # TASK_TYPE_COMPLEX_OPERATION
            >>> print(result.target_app)  # 微信
            >>> print(result.target_object)  # 张三
        """
        # 检查输入是否为空
        if not user_input or not user_input.strip():
            logger.warning("用户输入为空，返回默认自由聊天类型")
            return TaskJudgementResult(
                task_type=TASK_TYPE_FREE_CHAT,
                target_app="",
                target_object="",
                is_auto=False,
                specific_content=""
            )
        
        logger.info("开始判断任务类型: %s", user_input[:50] if len(user_input) > 50 else user_input)
        
        # 构建消息列表
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"请分析以下用户指令并返回JSON格式的任务识别结果：\n\n用户指令：{user_input}")
        ]
        
        try:
            # 准备回调处理器
            all_callbacks = prepare_callbacks_with_manager(self.callback_manager, callbacks=callbacks)
            
            # 构建回调配置
            config = {"callbacks": all_callbacks} if all_callbacks else {}
            
            # 调用模型进行判断
            response = self.model.invoke(messages, config=config)
            
            # 提取响应文本
            result_text = response.content.strip()
            
            # 从响应中提取 JSON 部分
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            # 解析 JSON 响应
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                task_info = json.loads(json_str)
                
                # 构建并返回结果
                result = TaskJudgementResult(
                    task_type=task_info.get("task_type", TASK_TYPE_FREE_CHAT),
                    target_app=task_info.get("target_app", ""),
                    target_object=task_info.get("target_object", ""),
                    is_auto=task_info.get("is_auto", False),
                    specific_content=task_info.get("specific_content", "")
                )
                
                logger.info("任务判断完成: 类型=%s, APP=%s, 对象=%s", 
                           result.task_type, result.target_app, result.target_object)
                return result
                
        except json.JSONDecodeError as e:
            # JSON 解析失败，记录日志并使用后备判断
            logger.warning("JSON 解析失败: %s，使用后备判断", str(e))
        except Exception as e:
            # 其他异常，记录日志并使用后备判断
            logger.warning("AI 判断失败: %s，使用后备判断", str(e))
        
        # 使用后备判断逻辑
        if 'e' in dir():
            logger.warning("任务判断失败: %s", str(e))
        else:
            logger.warning("任务判断失败，使用后备判断")
        return self._fallback_judge(user_input)
    
    def _fallback_judge(self, user_input: str) -> TaskJudgementResult:
        """
        后备判断逻辑
        
        当 AI 判断失败时，使用规则匹配进行任务判断。
        基于关键词匹配和正则表达式提取信息。
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            TaskJudgementResult: 任务判断结果对象
        """
        logger.info("使用后备规则判断任务类型")
        
        # 转换为小写便于匹配
        user_input_lower = user_input.lower()
        
        # 检查是否为持续自动任务
        if "auto" in user_input_lower or "持续" in user_input_lower:
            # 检查是否包含打开 APP 和发消息
            if "打开" in user_input and "发消息" in user_input:
                target_app = self._extract_app(user_input)
                target_object = self._extract_object(user_input)
                return TaskJudgementResult(
                    task_type=TASK_TYPE_CONTINUOUS_REPLY,
                    target_app=target_app,
                    target_object=target_object,
                    is_auto=True,
                    specific_content=""
                )
        
        # 检查是否为发送消息任务
        if "打开" in user_input and "发消息" in user_input:
            target_app = self._extract_app(user_input)
            target_object = self._extract_object(user_input)
            specific_content = self._extract_content(user_input)
            
            # 如果有具体内容，则为复杂操作
            if specific_content:
                return TaskJudgementResult(
                    task_type=TASK_TYPE_COMPLEX_OPERATION,
                    target_app=target_app,
                    target_object=target_object,
                    is_auto=False,
                    specific_content=specific_content
                )
            else:
                # 否则为单次回复
                return TaskJudgementResult(
                    task_type=TASK_TYPE_SINGLE_REPLY,
                    target_app=target_app,
                    target_object=target_object,
                    is_auto=False,
                    specific_content=""
                )
        
        # 检查是否为打开 APP 操作
        if "打开" in user_input:
            target_app = self._extract_app(user_input)
            return TaskJudgementResult(
                task_type=TASK_TYPE_BASIC_OPERATION,
                target_app=target_app,
                target_object="",
                is_auto=False,
                specific_content=""
            )
        
        # 默认为自由聊天
        logger.debug("未匹配到特定任务类型，返回自由聊天")
        return TaskJudgementResult(
            task_type=TASK_TYPE_FREE_CHAT,
            target_app="",
            target_object="",
            is_auto=False,
            specific_content=""
        )
    
    def _extract_app(self, user_input: str) -> str:
        """
        提取目标 APP 名称
        
        从用户输入中提取目标应用的名称。
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            提取到的 APP 名称，如果未找到则返回空字符串
        """
        # 支持的应用列表
        supported_apps = ["qq", "微信", "抖音", "淘宝", "快手", "qq音乐", "支付宝", "微博", "小红书", "bilibili"]
        user_input_lower = user_input.lower()
        
        # 遍历查找匹配的应用
        for app in supported_apps:
            if app in user_input_lower:
                logger.debug("提取到目标 APP: %s", app)
                return app
        
        return ""
    
    def _extract_object(self, user_input: str) -> str:
        """
        提取聊天对象名称
        
        从用户输入中提取聊天对象的名称。
        使用正则表达式匹配常见的表达模式。
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            提取到的聊天对象名称，如果未找到则返回空字符串
        """
        # 定义匹配模式
        patterns = [
            r"给([^\s]+?)发消息",  # 给XXX发消息
            r"和([^\s]+?)聊天",    # 和XXX聊天
            r"向([^\s]+?)发送",    # 向XXX发送
        ]
        
        # 遍历模式进行匹配
        for pattern in patterns:
            match = re.search(pattern, user_input)
            if match and match.group(1):
                logger.debug("提取到聊天对象: %s", match.group(1).strip())
                return match.group(1).strip()
        
        return ""
    
    def _extract_content(self, user_input: str) -> str:
        """
        提取具体消息内容
        
        从用户输入中提取要发送的具体消息内容。
        
        Args:
            user_input: 用户输入的文本
        
        Returns:
            提取到的消息内容，如果未找到则返回空字符串
        """
        # 尝试匹配引号内的内容
        quote_patterns = [r'["\']([^"\']+)["\']']
        for pattern in quote_patterns:
            match = re.search(pattern, user_input)
            if match:
                logger.debug("提取到消息内容（引号）: %s", match.group(1).strip())
                return match.group(1).strip()
        
        # 尝试匹配冒号后的内容
        if "：" in user_input:
            parts = user_input.split("：")
            if len(parts) > 1:
                last_part = parts[-1].strip()
                # 排除时间格式
                if not re.match(r'\d{1,2}:\d{2}', last_part) and len(last_part) > 0:
                    logger.debug("提取到消息内容（冒号）: %s", last_part)
                    return last_part
        
        return ""

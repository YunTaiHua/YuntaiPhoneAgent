"""
智谱模型初始化模块
==================

使用 langchain_community 集成智谱 AI 模型，提供统一的模型获取接口。

主要功能:
    - get_zhipu_client: 获取智谱 AI 客户端（单例模式）
    - get_judgement_model: 获取任务判断模型
    - get_chat_model: 获取聊天模型
    - get_phone_model: 获取手机操作模型

模型配置:
    - ZHIPU_API_KEY: 智谱 API 密钥
    - ZHIPU_API_BASE_URL: API 基础 URL
    - ZHIPU_MODEL: 默认模型
    - ZHIPU_CHAT_MODEL: 聊天模型
    - ZHIPU_JUDGEMENT_MODEL: 判断模型

使用示例:
    >>> from yuntai.models import get_chat_model
    >>> model = get_chat_model()
    >>> response = model.invoke("你好")
"""
import logging

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from zhipuai import ZhipuAI

from yuntai.core.config import (
    ZHIPU_API_KEY,
    ZHIPU_API_BASE_URL,
    ZHIPU_MODEL,
    ZHIPU_CHAT_MODEL,
    ZHIPU_JUDGEMENT_MODEL,
)

logger = logging.getLogger(__name__)

_zhipu_client: ZhipuAI | None = None


def get_zhipu_client() -> ZhipuAI:
    """
    获取智谱 AI 客户端（单例）
    
    返回全局唯一的智谱 AI 客户端实例。
    
    Returns:
        ZhipuAI 客户端实例
        
    使用示例:
        >>> client = get_zhipu_client()
        >>> response = client.chat.completions.create(
        ...     model="glm-4",
        ...     messages=[{"role": "user", "content": "你好"}]
        ... )
    """
    global _zhipu_client
    if _zhipu_client is None:
        _zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
        logger.debug("智谱 AI 客户端初始化完成")
    return _zhipu_client


def get_judgement_model() -> BaseChatModel:
    """
    获取任务判断模型
    
    用于判断用户意图和任务类型，使用较低温度以获得更稳定的结果。
    
    Returns:
        配置好的 ChatOpenAI 模型实例
    """
    logger.debug("创建判断模型: %s", ZHIPU_JUDGEMENT_MODEL)
    return ChatOpenAI(
        model=ZHIPU_JUDGEMENT_MODEL,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_API_BASE_URL,
        temperature=0.1,
    )


def get_chat_model() -> BaseChatModel:
    """
    获取聊天模型
    
    用于日常对话交互，使用较高温度以获得更自然的回复。
    
    Returns:
        配置好的 ChatOpenAI 模型实例
    """
    logger.debug("创建聊天模型: %s", ZHIPU_CHAT_MODEL)
    return ChatOpenAI(
        model=ZHIPU_CHAT_MODEL,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_API_BASE_URL,
        temperature=0.7,
    )


def get_phone_model() -> BaseChatModel:
    """
    获取手机操作模型
    
    用于手机自动化操作任务，使用中等温度平衡稳定性和灵活性。
    
    Returns:
        配置好的 ChatOpenAI 模型实例
    """
    logger.debug("创建手机操作模型: %s", ZHIPU_MODEL)
    return ChatOpenAI(
        model=ZHIPU_MODEL,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_API_BASE_URL,
        temperature=0.3,
    )


class ZhipuModelConfig:
    """
    智谱模型配置类
    
    提供模型配置的集中管理。
    
    Attributes:
        JUDGEMENT_MODEL: 判断模型名称
        CHAT_MODEL: 聊天模型名称
        PHONE_MODEL: 手机操作模型名称
    """
    
    JUDGEMENT_MODEL = ZHIPU_JUDGEMENT_MODEL
    CHAT_MODEL = ZHIPU_CHAT_MODEL
    PHONE_MODEL = ZHIPU_MODEL
    
    @classmethod
    def get_model_info(cls) -> dict[str, str]:
        """
        获取模型信息
        
        Returns:
            包含所有模型配置的字典
        """
        return {
            "judgement_model": cls.JUDGEMENT_MODEL,
            "chat_model": cls.CHAT_MODEL,
            "phone_model": cls.PHONE_MODEL,
        }

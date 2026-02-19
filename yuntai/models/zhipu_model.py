"""
智谱模型初始化模块
使用 langchain_community 集成智谱模型
"""
from typing import Optional
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

_zhipu_client: Optional[ZhipuAI] = None


def get_zhipu_client() -> ZhipuAI:
    """获取智谱AI客户端（单例）"""
    global _zhipu_client
    if _zhipu_client is None:
        _zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
    return _zhipu_client


def get_judgement_model() -> BaseChatModel:
    """获取任务判断模型"""
    return ChatOpenAI(
        model=ZHIPU_JUDGEMENT_MODEL,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_API_BASE_URL,
        temperature=0.1,
    )


def get_chat_model() -> BaseChatModel:
    """获取聊天模型"""
    return ChatOpenAI(
        model=ZHIPU_CHAT_MODEL,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_API_BASE_URL,
        temperature=0.7,
    )


def get_phone_model() -> BaseChatModel:
    """获取手机操作模型"""
    return ChatOpenAI(
        model=ZHIPU_MODEL,
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_API_BASE_URL,
        temperature=0.3,
    )


class ZhipuModelConfig:
    """智谱模型配置类"""
    
    JUDGEMENT_MODEL = ZHIPU_JUDGEMENT_MODEL
    CHAT_MODEL = ZHIPU_CHAT_MODEL
    PHONE_MODEL = ZHIPU_MODEL
    
    @classmethod
    def get_model_info(cls) -> dict:
        """获取模型信息"""
        return {
            "judgement_model": cls.JUDGEMENT_MODEL,
            "chat_model": cls.CHAT_MODEL,
            "phone_model": cls.PHONE_MODEL,
        }

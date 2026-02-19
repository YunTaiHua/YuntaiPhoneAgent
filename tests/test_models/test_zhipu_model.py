"""
智谱模型模块测试
测试 yuntai.models.zhipu_model 模块
"""
from unittest.mock import patch, MagicMock

import pytest


class TestGetZhipuClient:
    """测试获取智谱AI客户端"""
    
    def test_get_zhipu_client_singleton(self, mock_env_vars):
        """测试单例模式"""
        import yuntai.models.zhipu_model as model_module
        model_module._zhipu_client = None
        
        with patch('yuntai.models.zhipu_model.ZhipuAI') as mock_zhipu:
            mock_instance = MagicMock()
            mock_zhipu.return_value = mock_instance
            
            client1 = model_module.get_zhipu_client()
            client2 = model_module.get_zhipu_client()
            
            assert client1 is client2
            mock_zhipu.assert_called_once()
    
    def test_get_zhipu_client_with_api_key(self, mock_env_vars):
        """测试使用API key初始化"""
        import yuntai.models.zhipu_model as model_module
        model_module._zhipu_client = None
        
        with patch('yuntai.models.zhipu_model.ZhipuAI') as mock_zhipu:
            mock_instance = MagicMock()
            mock_zhipu.return_value = mock_instance
            
            model_module.get_zhipu_client()
            
            mock_zhipu.assert_called_once()


class TestGetJudgementModel:
    """测试获取任务判断模型"""
    
    def test_get_judgement_model(self, mock_env_vars):
        """测试获取判断模型"""
        with patch('yuntai.models.zhipu_model.ChatOpenAI') as mock_chat:
            mock_model = MagicMock()
            mock_chat.return_value = mock_model
            
            from yuntai.models.zhipu_model import get_judgement_model
            
            result = get_judgement_model()
            
            assert result == mock_model
            mock_chat.assert_called_once()
    
    def test_judgement_model_temperature(self, mock_env_vars):
        """测试判断模型温度参数"""
        with patch('yuntai.models.zhipu_model.ChatOpenAI') as mock_chat:
            from yuntai.models.zhipu_model import get_judgement_model
            
            get_judgement_model()
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['temperature'] == 0.1


class TestGetChatModel:
    """测试获取聊天模型"""
    
    def test_get_chat_model(self, mock_env_vars):
        """测试获取聊天模型"""
        with patch('yuntai.models.zhipu_model.ChatOpenAI') as mock_chat:
            mock_model = MagicMock()
            mock_chat.return_value = mock_model
            
            from yuntai.models.zhipu_model import get_chat_model
            
            result = get_chat_model()
            
            assert result == mock_model
    
    def test_chat_model_temperature(self, mock_env_vars):
        """测试聊天模型温度参数"""
        with patch('yuntai.models.zhipu_model.ChatOpenAI') as mock_chat:
            from yuntai.models.zhipu_model import get_chat_model
            
            get_chat_model()
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['temperature'] == 0.7


class TestGetPhoneModel:
    """测试获取手机操作模型"""
    
    def test_get_phone_model(self, mock_env_vars):
        """测试获取手机模型"""
        with patch('yuntai.models.zhipu_model.ChatOpenAI') as mock_chat:
            mock_model = MagicMock()
            mock_chat.return_value = mock_model
            
            from yuntai.models.zhipu_model import get_phone_model
            
            result = get_phone_model()
            
            assert result == mock_model
    
    def test_phone_model_temperature(self, mock_env_vars):
        """测试手机模型温度参数"""
        with patch('yuntai.models.zhipu_model.ChatOpenAI') as mock_chat:
            from yuntai.models.zhipu_model import get_phone_model
            
            get_phone_model()
            
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs['temperature'] == 0.3


class TestZhipuModelConfig:
    """测试智谱模型配置类"""
    
    def test_model_config_attributes(self, mock_env_vars):
        """测试模型配置属性"""
        from yuntai.models.zhipu_model import ZhipuModelConfig
        
        assert ZhipuModelConfig.JUDGEMENT_MODEL is not None
        assert ZhipuModelConfig.CHAT_MODEL is not None
        assert ZhipuModelConfig.PHONE_MODEL is not None
    
    def test_get_model_info(self, mock_env_vars):
        """测试获取模型信息"""
        from yuntai.models.zhipu_model import ZhipuModelConfig
        
        info = ZhipuModelConfig.get_model_info()
        
        assert isinstance(info, dict)
        assert "judgement_model" in info
        assert "chat_model" in info
        assert "phone_model" in info
    
    def test_model_names_correct(self, mock_env_vars):
        """测试模型名称正确"""
        from yuntai.models.zhipu_model import ZhipuModelConfig
        
        assert "glm" in ZhipuModelConfig.CHAT_MODEL.lower() or "autoglm" in ZhipuModelConfig.PHONE_MODEL.lower()


class TestModelExports:
    """测试模块导出"""
    
    def test_exports_from_init(self, mock_env_vars):
        """测试从__init__.py导出"""
        from yuntai.models import (
            get_judgement_model,
            get_chat_model,
            get_phone_model,
            get_zhipu_client,
        )
        
        assert callable(get_judgement_model)
        assert callable(get_chat_model)
        assert callable(get_phone_model)
        assert callable(get_zhipu_client)

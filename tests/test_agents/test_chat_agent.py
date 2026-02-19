"""
Agent模块测试
测试 yuntai.agents 模块
"""
from unittest.mock import patch, MagicMock

import pytest


class TestBaseAgent:
    """测试基础Agent类"""
    
    def test_base_agent_init_without_model(self, mock_env_vars):
        """测试不带模型初始化"""
        from yuntai.agents.base_agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            def invoke(self, input_data):
                return {"result": "test"}
        
        agent = ConcreteAgent()
        assert agent.model is None
    
    def test_base_agent_init_with_model(self, mock_env_vars, mock_chat_model):
        """测试带模型初始化"""
        from yuntai.agents.base_agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            def invoke(self, input_data):
                return {"result": "test"}
        
        agent = ConcreteAgent(model=mock_chat_model)
        assert agent.model == mock_chat_model
    
    def test_base_agent_set_model(self, mock_env_vars, mock_chat_model):
        """测试设置模型"""
        from yuntai.agents.base_agent import BaseAgent
        
        class ConcreteAgent(BaseAgent):
            def invoke(self, input_data):
                return {"result": "test"}
        
        agent = ConcreteAgent()
        agent.set_model(mock_chat_model)
        assert agent.model == mock_chat_model
    
    def test_base_agent_invoke_abstract(self, mock_env_vars):
        """测试invoke是抽象方法"""
        from yuntai.agents.base_agent import BaseAgent
        
        with pytest.raises(TypeError):
            BaseAgent()


class TestChatAgent:
    """测试聊天Agent"""
    
    def test_chat_agent_init(self, mock_env_vars, mock_chat_model):
        """测试初始化"""
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client') as mock_client:
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(model=mock_chat_model)
                assert agent.model == mock_chat_model
    
    def test_chat_agent_chat(self, mock_env_vars, mock_chat_model, mock_file_manager):
        """测试聊天功能"""
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client'):
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(model=mock_chat_model, file_manager=mock_file_manager)
                result = agent.chat("你好")
                
                assert result == "这是测试回复"
    
    def test_chat_agent_chat_without_memory(self, mock_env_vars, mock_chat_model):
        """测试不带记忆的聊天"""
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client'):
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(model=mock_chat_model)
                result = agent.chat("你好", include_memory=False)
                
                assert result == "这是测试回复"
    
    def test_chat_agent_chat_with_history(self, mock_env_vars, mock_chat_model):
        """测试带历史的聊天"""
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client'):
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(model=mock_chat_model)
                history = [
                    {"role": "user", "content": "之前的问题"},
                    {"role": "assistant", "content": "之前的回答"}
                ]
                result = agent.chat_with_history("新问题", history)
                
                assert result == "这是测试回复"
    
    def test_chat_agent_saves_history(self, mock_env_vars, mock_chat_model, mock_file_manager):
        """测试聊天保存历史"""
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client'):
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(model=mock_chat_model, file_manager=mock_file_manager)
                agent.chat("你好")
                
                mock_file_manager.save_conversation_history.assert_called()
    
    def test_chat_agent_with_tts(self, mock_env_vars, mock_chat_model, mock_file_manager, mock_tts_manager):
        """测试带TTS的聊天"""
        mock_tts_manager.tts_enabled = True
        
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client'):
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(
                    model=mock_chat_model,
                    file_manager=mock_file_manager,
                    tts_manager=mock_tts_manager
                )
                result = agent.chat("你好，请详细回答")
                
                assert result == "这是测试回复"
    
    def test_chat_agent_error_handling(self, mock_env_vars, mock_chat_model):
        """测试错误处理"""
        mock_chat_model.invoke.side_effect = Exception("模型错误")
        
        with patch('yuntai.agents.chat_agent.get_chat_model', return_value=mock_chat_model):
            with patch('yuntai.agents.chat_agent.get_zhipu_client'):
                from yuntai.agents.chat_agent import ChatAgent
                
                agent = ChatAgent(model=mock_chat_model)
                result = agent.chat("你好")
                
                assert "失败" in result or "错误" in result

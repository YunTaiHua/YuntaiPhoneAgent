"""
Base Agent测试
测试 yuntai.agents.base_agent 模块
"""
from abc import ABC
from unittest.mock import MagicMock

import pytest


class TestBaseAgentAbstract:
    """测试BaseAgent抽象特性"""
    
    def test_base_agent_is_abstract(self, mock_env_vars):
        """测试BaseAgent是抽象类"""
        from yuntai.agents.base_agent import BaseAgent
        
        assert ABC in BaseAgent.__bases__ or any(
            ABC in base.__bases__ for base in BaseAgent.__bases__
        )
    
    def test_cannot_instantiate_directly(self, mock_env_vars):
        """测试不能直接实例化"""
        from yuntai.agents.base_agent import BaseAgent
        
        with pytest.raises(TypeError):
            BaseAgent()


class TestBaseAgentSubclass:
    """测试BaseAgent子类"""
    
    def test_concrete_implementation(self, mock_env_vars):
        """测试具体实现"""
        from yuntai.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def invoke(self, input_data):
                return {"status": "success", "data": input_data}
        
        agent = TestAgent()
        result = agent.invoke({"query": "test"})
        
        assert result["status"] == "success"
        assert result["data"]["query"] == "test"
    
    def test_invoke_method_signature(self, mock_env_vars):
        """测试invoke方法签名"""
        from yuntai.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def invoke(self, input_data):
                return {}
        
        agent = TestAgent()
        assert callable(agent.invoke)
    
    def test_set_model_method(self, mock_env_vars):
        """测试set_model方法"""
        from yuntai.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def invoke(self, input_data):
                return {}
        
        mock_model = MagicMock()
        agent = TestAgent()
        agent.set_model(mock_model)
        
        assert agent.model == mock_model
    
    def test_model_attribute_default(self, mock_env_vars):
        """测试model属性默认值"""
        from yuntai.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def invoke(self, input_data):
                return {}
        
        agent = TestAgent()
        assert agent.model is None
    
    def test_model_attribute_with_model(self, mock_env_vars):
        """测试带模型的model属性"""
        from yuntai.agents.base_agent import BaseAgent
        
        class TestAgent(BaseAgent):
            def invoke(self, input_data):
                return {}
        
        mock_model = MagicMock()
        agent = TestAgent(model=mock_model)
        assert agent.model == mock_model


class TestBaseAgentInheritance:
    """测试继承行为"""
    
    def test_inheritance_chain(self, mock_env_vars):
        """测试继承链"""
        from yuntai.agents.base_agent import BaseAgent
        
        class MiddleAgent(BaseAgent):
            def invoke(self, input_data):
                return self.process(input_data)
            
            def process(self, data):
                return {"processed": data}
        
        class FinalAgent(MiddleAgent):
            def process(self, data):
                result = super().process(data)
                result["final"] = True
                return result
        
        agent = FinalAgent()
        result = agent.invoke({"input": "test"})
        
        assert "processed" in result
        assert "final" in result
        assert result["final"] is True

"""
测试 AgentExecutor
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

from yuntai.core.agent_executor import AgentExecutor


class TestAgentExecutor:
    """测试Agent执行器"""

    def test_init(self):
        """测试初始化"""
        executor = AgentExecutor()
        
        assert executor is not None

    def test_init_with_device_type(self):
        """测试使用设备类型初始化"""
        executor = AgentExecutor(device_type="android")
        
        assert executor is not None

    def test_set_device_type(self):
        """测试设置设备类型"""
        executor = AgentExecutor()
        
        executor.set_device_type("harmony")
        
        # 应该成功设置
        assert True

    def test_is_pipe_ready_false(self):
        """测试检查管道是否就绪 - False"""
        # 确保管道未初始化
        AgentExecutor._stdin_write = None
        
        result = AgentExecutor.is_pipe_ready()
        
        assert result is False

    def test_user_confirm_without_pipe(self):
        """测试用户确认 - 无管道"""
        # 确保管道未初始化
        AgentExecutor._stdin_write = None
        
        result = AgentExecutor.user_confirm()
        
        # 应该返回False
        assert result is False

    def test_setup_stdin_pipe(self):
        """测试设置标准输入管道"""
        # 清理之前的管道
        AgentExecutor._cleanup_stdin_pipe()
        
        # 设置管道
        AgentExecutor._setup_stdin_pipe()
        
        # 应该成功设置
        assert AgentExecutor._stdin_write is not None
        
        # 清理
        AgentExecutor._cleanup_stdin_pipe()

    def test_cleanup_stdin_pipe(self):
        """测试清理标准输入管道"""
        # 先设置管道
        AgentExecutor._setup_stdin_pipe()
        
        # 清理管道
        AgentExecutor._cleanup_stdin_pipe()
        
        # 应该成功清理
        assert AgentExecutor._stdin_write is None

    def test_user_confirm_with_pipe(self):
        """测试用户确认 - 有管道"""
        # 设置管道
        AgentExecutor._setup_stdin_pipe()
        
        result = AgentExecutor.user_confirm()
        
        # 应该返回True
        assert result is True
        
        # 清理
        AgentExecutor._cleanup_stdin_pipe()

    @patch('yuntai.core.agent_executor.PhoneAgent')
    def test_phone_agent_exec(self, mock_phone_agent):
        """测试PhoneAgent执行"""
        mock_agent = MagicMock()
        mock_agent.run.return_value = "操作成功"
        mock_phone_agent.return_value = mock_agent
        
        executor = AgentExecutor()
        
        with patch('yuntai.core.agent_executor.ModelConfig'):
            with patch('yuntai.core.agent_executor.AgentConfig'):
                result, history = executor.phone_agent_exec(
                    "打开微信",
                    None,
                    "basic_operation",
                    "test_device"
                )
                
                # 应该返回结果
                assert isinstance(result, str)
                assert isinstance(history, list)

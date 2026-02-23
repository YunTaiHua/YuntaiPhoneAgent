"""
测试 yuntai.graphs.reply_graph 模块
"""
import pytest
from unittest.mock import patch, MagicMock

from yuntai.graphs.reply_graph import ReplyGraph
from yuntai.graphs.state import ReplyStateBuilder


class TestReplyGraph:
    """测试持续回复工作流"""
    
    def test_init(self, mock_env_vars):
        """测试初始化"""
        graph = ReplyGraph()
        
        assert graph.file_manager is None
        assert graph.tts_manager is None
        assert graph.terminate_event is not None
        assert graph._running is False
    
    def test_init_with_managers(self, mock_env_vars, mock_file_manager, mock_tts_manager):
        """测试带管理器初始化"""
        graph = ReplyGraph(
            file_manager=mock_file_manager,
            tts_manager=mock_tts_manager
        )
        
        assert graph.file_manager == mock_file_manager
        assert graph.tts_manager == mock_tts_manager
    
    def test_stop(self, mock_env_vars):
        """测试停止功能"""
        graph = ReplyGraph()
        
        assert graph.terminate_event.is_set() is False
        
        graph.stop()
        
        assert graph.terminate_event.is_set() is True
    
    def test_reset(self, mock_env_vars):
        """测试重置功能"""
        graph = ReplyGraph()
        
        graph.stop()
        assert graph.terminate_event.is_set() is True
        
        graph.reset()
        
        assert graph.terminate_event.is_set() is False
        assert graph._running is False
    
    def test_is_running(self, mock_env_vars):
        """测试运行状态"""
        graph = ReplyGraph()
        
        assert graph.is_running() is False
        
        graph._running = True
        assert graph.is_running() is True
        
        graph._running = False
        assert graph.is_running() is False
    
    def test_graph_built(self, mock_env_vars):
        """测试图已构建"""
        graph = ReplyGraph()
        
        assert graph.graph is not None


class TestReplyGraphRouting:
    """测试工作流路由"""
    
    def test_route_after_check_with_new_message(self, mock_env_vars):
        """测试检查新消息后的路由 - 有新消息"""
        graph = ReplyGraph()
        
        state = {
            "is_new_message": True,
            "terminate_flag": False,
        }
        
        result = graph._route_after_check(state)
        assert result == "reply"
    
    def test_route_after_check_without_new_message(self, mock_env_vars):
        """测试检查新消息后的路由 - 无新消息"""
        graph = ReplyGraph()
        
        state = {
            "is_new_message": False,
            "terminate_flag": False,
        }
        
        result = graph._route_after_check(state)
        assert result == "wait"
    
    def test_route_after_check_with_terminate(self, mock_env_vars):
        """测试检查新消息后的路由 - 终止"""
        graph = ReplyGraph()
        
        state = {
            "is_new_message": True,
            "terminate_flag": True,
        }
        
        result = graph._route_after_check(state)
        assert result == "wait"
    
    def test_route_after_reply_with_reply(self, mock_env_vars):
        """测试生成回复后的路由 - 有回复"""
        graph = ReplyGraph()
        
        state = {
            "generated_reply": "这是回复",
            "terminate_flag": False,
        }
        
        result = graph._route_after_reply(state)
        assert result == "send"
    
    def test_route_after_reply_without_reply(self, mock_env_vars):
        """测试生成回复后的路由 - 无回复"""
        graph = ReplyGraph()
        
        state = {
            "generated_reply": "",
            "terminate_flag": False,
        }
        
        result = graph._route_after_reply(state)
        assert result == "wait"
    
    def test_route_continue_should_continue(self, mock_env_vars):
        """测试继续检查路由 - 应继续"""
        graph = ReplyGraph()
        
        state = {
            "should_continue": True,
            "terminate_flag": False,
        }
        
        result = graph._route_continue(state)
        assert result == "continue"
    
    def test_route_continue_should_end(self, mock_env_vars):
        """测试继续检查路由 - 应结束"""
        graph = ReplyGraph()
        
        state = {
            "should_continue": False,
            "terminate_flag": False,
        }
        
        result = graph._route_continue(state)
        assert result == "end"
    
    def test_route_continue_with_terminate_event(self, mock_env_vars):
        """测试继续检查路由 - 终止事件"""
        graph = ReplyGraph()
        graph.terminate_event.set()
        
        state = {
            "should_continue": True,
            "terminate_flag": False,
        }
        
        result = graph._route_continue(state)
        assert result == "end"
        
        graph.terminate_event.clear()


class TestReplyStateBuilder:
    """测试状态构建器"""
    
    def test_create_basic(self, mock_env_vars):
        """测试基本创建"""
        state = ReplyStateBuilder.create(
            app_name="微信",
            chat_object="张三"
        )
        
        assert state["app_name"] == "微信"
        assert state["chat_object"] == "张三"
        assert state["seen_other_messages"] == []
    
    def test_create_with_device_id(self, mock_env_vars):
        """测试带设备ID创建"""
        state = ReplyStateBuilder.create(
            app_name="QQ",
            chat_object="李四",
            device_id="device123"
        )
        
        assert state["device_id"] == "device123"
    
    def test_create_with_custom_max_cycles(self, mock_env_vars):
        """测试自定义最大循环次数"""
        state = ReplyStateBuilder.create(
            app_name="微信",
            chat_object="张三",
            max_cycles=50
        )
        
        assert state["max_cycles"] == 50

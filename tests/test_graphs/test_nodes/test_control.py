"""
测试 yuntai.graphs.nodes.control 模块
"""
import pytest
import threading

from yuntai.graphs.nodes.control import (
    check_continue,
    do_wait,
    check_terminate,
    set_terminate_event,
)
from yuntai.graphs.state import ReplyState


class TestCheckContinue:
    """测试继续检查节点"""
    
    def test_should_continue_under_limit(self, mock_env_vars):
        """测试未达到限制时应继续"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=5,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=[],
        )
        
        result = check_continue(state)
        
        assert result["should_continue"] is True
    
    def test_should_stop_at_limit(self, mock_env_vars):
        """测试达到限制时应停止"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=30,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=[],
        )
        
        result = check_continue(state)
        
        assert result["should_continue"] is False
    
    def test_should_stop_on_terminate_flag(self, mock_env_vars):
        """测试终止标志时应停止"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=5,
            max_cycles=30,
            should_continue=True,
            terminate_flag=True,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=[],
        )
        
        result = check_continue(state)
        
        assert result["should_continue"] is False
        assert result["terminate_flag"] is True


class TestTerminateEvent:
    """测试终止事件"""
    
    def test_set_and_check_terminate_event(self, mock_env_vars):
        """测试设置和检查终止事件"""
        event = threading.Event()
        set_terminate_event(event)
        
        assert check_terminate() is False
        
        event.set()
        assert check_terminate() is True
    
    def test_clear_terminate_event(self, mock_env_vars):
        """测试清除终止事件"""
        event = threading.Event()
        set_terminate_event(event)
        
        event.set()
        assert check_terminate() is True
        
        event.clear()
        assert check_terminate() is False


class TestDoWait:
    """测试等待节点"""
    
    def test_do_wait_basic(self, mock_env_vars):
        """测试基本等待功能"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=1,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=[],
        )
        
        import time
        start = time.time()
        result = do_wait(state)
        elapsed = time.time() - start
        
        assert elapsed >= 1.0
        assert result == {}
    
    def test_do_wait_interrupted_by_terminate(self, mock_env_vars):
        """测试等待被终止信号打断"""
        event = threading.Event()
        set_terminate_event(event)
        
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=1,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=[],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=10,
            result_message="",
            seen_other_messages=[],
        )
        
        import time
        start = time.time()
        
        def set_event_later():
            import time
            time.sleep(0.5)
            event.set()
        
        thread = threading.Thread(target=set_event_later)
        thread.start()
        
        result = do_wait(state)
        elapsed = time.time() - start
        
        thread.join()
        
        assert elapsed < 5

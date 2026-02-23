"""
测试 yuntai.graphs.nodes.check_new 模块
"""
import pytest

from yuntai.graphs.nodes.check_new import check_new_message, is_similar
from yuntai.graphs.state import ReplyState


class TestIsSimilar:
    """测试相似度判断函数"""
    
    def test_identical_messages(self):
        """测试完全相同的消息"""
        assert is_similar("你好", "你好", 0.6) is True
    
    def test_different_messages(self):
        """测试完全不同的消息"""
        assert is_similar("你好", "再见", 0.6) is False
    
    def test_similar_messages(self):
        """测试相似消息"""
        assert is_similar("你好呀", "你好", 0.6) is True
    
    def test_subset_messages(self):
        """测试子串包含关系"""
        assert is_similar("明天要点名", "明天要点名，可千万不能迟到", 0.6) is True
        assert is_similar("明天要点名，可千万不能迟到", "明天要点名", 0.6) is True
    
    def test_empty_messages(self):
        """测试空消息"""
        assert is_similar("", "", 0.6) is False
        assert is_similar("你好", "", 0.6) is False
        assert is_similar("", "你好", 0.6) is False
    
    def test_messages_with_punctuation(self):
        """测试带标点的消息"""
        assert is_similar("你好！", "你好", 0.6) is True
        assert is_similar("带上笔", "带上笔。", 0.7) is True
    
    def test_threshold_sensitivity(self):
        """测试阈值敏感性"""
        msg1 = "明天要点名，可千万不能迟到"
        msg2 = "明天要点名"
        
        assert is_similar(msg1, msg2, 0.3) is True
        assert is_similar(msg1, msg2, 0.9) is False


class TestCheckNewMessage:
    """测试检查新消息节点"""
    
    def test_no_messages(self, mock_env_vars):
        """测试没有对方消息"""
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
        
        result = check_new_message(state)
        
        assert result["is_new_message"] is False
        assert result["latest_message"] == ""
    
    def test_first_time_seeing_message(self, mock_env_vars):
        """测试首次看到消息"""
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
            current_other_messages=["明天要点名", "带上笔"],
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
        
        result = check_new_message(state)
        
        assert result["is_new_message"] is True
        assert result["latest_message"] == "带上笔"
        assert "明天要点名" in result["seen_other_messages"]
        assert "带上笔" in result["seen_other_messages"]
    
    def test_message_already_seen(self, mock_env_vars):
        """测试已见过的消息（核心修复测试）"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=2,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=["明天要点名"],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="带上笔",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=["我会帮你带早餐的", "明天要点名", "带上笔"],
        )
        
        result = check_new_message(state)
        
        assert result["is_new_message"] is False
        assert result["latest_message"] == ""
    
    def test_new_message_after_seen(self, mock_env_vars):
        """测试已见消息后有新消息"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=2,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=["带上笔", "新消息内容"],
            current_my_messages=[],
            latest_message="",
            previous_latest_message="带上笔",
            is_new_message=False,
            generated_reply="",
            send_success=False,
            last_sent_reply="",
            error=None,
            retry_count=0,
            wait_seconds=1,
            result_message="",
            seen_other_messages=["明天要点名", "带上笔"],
        )
        
        result = check_new_message(state)
        
        assert result["is_new_message"] is True
        assert result["latest_message"] == "新消息内容"
    
    def test_seen_messages_accumulate(self, mock_env_vars):
        """测试已见消息累积"""
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
            current_other_messages=["消息A", "消息B"],
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
            seen_other_messages=["消息C"],
        )
        
        result = check_new_message(state)
        
        assert "消息A" in result["seen_other_messages"]
        assert "消息B" in result["seen_other_messages"]
        assert "消息C" in result["seen_other_messages"]
    
    def test_similar_message_treated_as_seen(self, mock_env_vars):
        """测试相似消息被视为已见"""
        state = ReplyState(
            app_name="微信",
            chat_object="张三",
            device_id="",
            cycle_count=2,
            max_cycles=30,
            should_continue=True,
            terminate_flag=False,
            extracted_records="",
            parse_success=True,
            parsed_messages=[],
            other_messages=[],
            my_messages=[],
            current_other_messages=["明天要点名，可千万不能迟到"],
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
            seen_other_messages=["明天要点名"],
        )
        
        result = check_new_message(state)
        
        assert result["is_new_message"] is False

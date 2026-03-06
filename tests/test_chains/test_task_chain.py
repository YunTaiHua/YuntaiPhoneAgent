"""
测试 TaskChain
"""
import pytest
from unittest.mock import MagicMock, patch, call

from yuntai.chains.task_chain import TaskChain
from yuntai.prompts import (
    TASK_TYPE_FREE_CHAT,
    TASK_TYPE_BASIC_OPERATION,
    TASK_TYPE_SINGLE_REPLY,
    TASK_TYPE_CONTINUOUS_REPLY,
    TASK_TYPE_COMPLEX_OPERATION,
)


class TestTaskChain:
    """测试 TaskChain"""

    def test_init(self):
        """测试初始化"""
        chain = TaskChain(device_id="test_device")
        
        assert chain.device_id == "test_device"
        assert chain.file_manager is None
        assert chain.tts_manager is None
        assert chain.judgement_agent is not None
        assert chain.chat_agent is not None
        assert chain.phone_agent is not None
        assert chain.reply_chain is not None

    def test_init_with_managers(self, mock_file_manager, mock_tts_manager):
        """测试使用管理器初始化"""
        chain = TaskChain(
            device_id="test_device",
            file_manager=mock_file_manager,
            tts_manager=mock_tts_manager
        )
        
        assert chain.file_manager == mock_file_manager
        assert chain.tts_manager == mock_tts_manager
        assert chain.chat_agent.file_manager == mock_file_manager
        assert chain.chat_agent.tts_manager == mock_tts_manager

    def test_set_device_id(self):
        """测试设置设备ID"""
        chain = TaskChain(device_id="old_device")
        
        chain.set_device_id("new_device")
        
        assert chain.device_id == "new_device"
        assert chain.phone_agent.device_id == "new_device"
        assert chain.reply_chain.device_id == "new_device"

    def test_set_tts_manager(self, mock_tts_manager):
        """测试设置TTS管理器"""
        chain = TaskChain(device_id="test_device")
        
        chain.set_tts_manager(mock_tts_manager)
        
        assert chain.tts_manager == mock_tts_manager
        assert chain.chat_agent.tts_manager == mock_tts_manager

    def test_process_empty_input(self):
        """测试处理空输入"""
        chain = TaskChain(device_id="test_device")
        
        result, task_info = chain.process("")
        
        assert result == "输入为空"
        assert task_info == {}

    def test_process_whitespace_input(self):
        """测试处理空白字符输入"""
        chain = TaskChain(device_id="test_device")
        
        result, task_info = chain.process("   \n\t  ")
        
        assert result == "输入为空"
        assert task_info == {}

    @patch('yuntai.chains.task_chain.SHORTCUTS', {'w': '打开微信', 'q': '打开QQ'})
    @patch.object(TaskChain, '_handle_basic_operation')
    def test_process_shortcut(self, mock_handle_basic):
        """测试处理快捷键"""
        mock_handle_basic.return_value = "✅ 操作完成"
        chain = TaskChain(device_id="test_device")
        
        result, task_info = chain.process("w")
        
        mock_handle_basic.assert_called_once_with("打开微信")
        assert result == "✅ 操作完成"
        assert task_info == {}

    @patch('yuntai.chains.task_chain.SHORTCUTS', {'w': '打开微信'})
    def test_process_shortcut_uppercase(self):
        """测试处理大写快捷键"""
        with patch.object(TaskChain, '_handle_basic_operation') as mock_handle:
            mock_handle.return_value = "✅ 操作完成"
            chain = TaskChain(device_id="test_device")
            
            result, task_info = chain.process("W")
            
            mock_handle.assert_called_once_with("打开微信")

    @patch.object(TaskChain, '_handle_free_chat')
    def test_process_free_chat(self, mock_handle_chat):
        """测试处理自由聊天"""
        mock_handle_chat.return_value = "这是聊天回复"
        
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_FREE_CHAT,
                to_dict=lambda: {"task_type": TASK_TYPE_FREE_CHAT}
            )
            chain.chat_agent = MagicMock()
            
            result, task_info = chain.process("今天天气怎么样")
            
            mock_handle_chat.assert_called_once()
            assert result == "这是聊天回复"

    @patch.object(TaskChain, '_handle_basic_operation')
    def test_process_basic_operation(self, mock_handle_basic):
        """测试处理基础操作"""
        mock_handle_basic.return_value = "✅ 操作完成"
        
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_BASIC_OPERATION,
                target_app="微信",
                to_dict=lambda: {"task_type": TASK_TYPE_BASIC_OPERATION}
            )
            
            result, task_info = chain.process("打开微信")
            
            mock_handle_basic.assert_called_once_with("打开微信")
            assert result == "✅ 操作完成"

    @patch.object(TaskChain, '_handle_single_reply')
    def test_process_single_reply(self, mock_handle_single):
        """测试处理单次回复"""
        mock_handle_single.return_value = "✅ 单次回复完成"
        
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_SINGLE_REPLY,
                target_app="微信",
                target_object="张三",
                to_dict=lambda: {"task_type": TASK_TYPE_SINGLE_REPLY}
            )
            
            result, task_info = chain.process("给微信的张三发消息")
            
            mock_handle_single.assert_called_once()
            assert result == "✅ 单次回复完成"

    def test_process_single_reply_missing_info(self):
        """测试处理单次回复 - 缺少信息"""
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_SINGLE_REPLY,
                target_app="",
                target_object="",
                to_dict=lambda: {"task_type": TASK_TYPE_SINGLE_REPLY}
            )
            
            result, task_info = chain.process("发消息")
            
            assert result == "无法识别 APP 或聊天对象"

    @patch.object(TaskChain, '_handle_continuous_reply')
    def test_process_continuous_reply(self, mock_handle_continuous):
        """测试处理持续回复"""
        mock_handle_continuous.return_value = "🔄CONTINUOUS_REPLY:微信:张三"
        
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_CONTINUOUS_REPLY,
                target_app="微信",
                target_object="张三",
                to_dict=lambda: {"task_type": TASK_TYPE_CONTINUOUS_REPLY}
            )
            
            result, task_info = chain.process("auto打开微信给张三发消息")
            
            mock_handle_continuous.assert_called_once_with("微信", "张三")

    def test_process_continuous_reply_missing_info(self):
        """测试处理持续回复 - 缺少信息"""
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_CONTINUOUS_REPLY,
                target_app="",
                target_object="",
                to_dict=lambda: {"task_type": TASK_TYPE_CONTINUOUS_REPLY}
            )
            
            result, task_info = chain.process("auto发消息")
            
            assert result == "无法识别 APP 或聊天对象"

    @patch.object(TaskChain, '_handle_complex_operation')
    def test_process_complex_operation(self, mock_handle_complex):
        """测试处理复杂操作"""
        mock_handle_complex.return_value = "✅ 复杂操作完成"
        
        with patch.object(TaskChain, '__init__', lambda self, **kwargs: None):
            chain = TaskChain()
            chain.callback_manager = MagicMock()
            chain.callback_manager.get_callbacks.return_value = []
            chain.judgement_agent = MagicMock()
            chain.judgement_agent.judge.return_value = MagicMock(
                task_type=TASK_TYPE_COMPLEX_OPERATION,
                to_dict=lambda: {"task_type": TASK_TYPE_COMPLEX_OPERATION}
            )
            
            result, task_info = chain.process('打开微信给张三发消息："你好"')
            
            mock_handle_complex.assert_called_once_with('打开微信给张三发消息："你好"')
            assert result == "✅ 复杂操作完成"

    def test_handle_free_chat(self):
        """测试处理自由聊天"""
        chain = TaskChain(device_id="test_device")
        chain.callback_manager = MagicMock()
        chain.callback_manager.get_callbacks.return_value = []
        chain.chat_agent = MagicMock()
        chain.chat_agent.chat.return_value = "这是聊天回复"
        
        result = chain._handle_free_chat("你好")
        
        # chat 方法现在接受 callbacks 参数
        chain.chat_agent.chat.assert_called_once()
        assert result == "这是聊天回复"

    def test_handle_basic_operation_success(self):
        """测试处理基础操作 - 成功"""
        chain = TaskChain(device_id="test_device")
        chain.phone_agent = MagicMock()
        chain.phone_agent.execute_operation.return_value = (True, "操作成功")
        chain.tts_manager = None
        
        result = chain._handle_basic_operation("打开微信")
        
        chain.phone_agent.execute_operation.assert_called_once_with("打开微信")
        assert "✅" in result

    def test_handle_basic_operation_failure(self):
        """测试处理基础操作 - 失败"""
        chain = TaskChain(device_id="test_device")
        chain.phone_agent = MagicMock()
        chain.phone_agent.execute_operation.return_value = (False, "操作失败")
        
        result = chain._handle_basic_operation("打开未知应用")
        
        assert "❌" in result
        assert "操作失败" in result

    def test_handle_basic_operation_with_tts(self, mock_tts_manager):
        """测试处理基础操作 - 带TTS"""
        chain = TaskChain(device_id="test_device")
        chain.phone_agent = MagicMock()
        chain.phone_agent.execute_operation.return_value = (True, "操作成功")
        chain.tts_manager = mock_tts_manager
        mock_tts_manager.tts_enabled = True
        
        result = chain._handle_basic_operation("打开微信")
        
        # TTS应该被调用（通过Timer）
        assert "✅" in result

    def test_handle_single_reply(self):
        """测试处理单次回复"""
        chain = TaskChain(device_id="test_device")
        chain.callback_manager = MagicMock()
        chain.callback_manager.get_callbacks.return_value = []
        chain.reply_chain = MagicMock()
        chain.reply_chain.single_reply.return_value = (True, "回复已发送")
        
        result = chain._handle_single_reply("微信", "张三")
        
        # single_reply 方法现在接受 callbacks 参数
        chain.reply_chain.single_reply.assert_called_once()
        assert result == "回复已发送"

    def test_handle_continuous_reply_with_device(self):
        """测试处理持续回复 - 有设备"""
        chain = TaskChain(device_id="test_device")
        
        result = chain._handle_continuous_reply("微信", "张三")
        
        assert "CONTINUOUS_REPLY" in result
        assert "微信" in result
        assert "张三" in result

    def test_handle_continuous_reply_without_device(self):
        """测试处理持续回复 - 无设备"""
        chain = TaskChain(device_id="")
        
        result = chain._handle_continuous_reply("微信", "张三")
        
        assert "设备未连接" in result

    def test_handle_complex_operation_success(self):
        """测试处理复杂操作 - 成功"""
        chain = TaskChain(device_id="test_device")
        chain.phone_agent = MagicMock()
        chain.phone_agent.execute_operation.return_value = (True, "操作成功")
        chain.tts_manager = None
        
        result = chain._handle_complex_operation("打开微信并发送消息")
        
        chain.phone_agent.execute_operation.assert_called_once_with("打开微信并发送消息")
        assert "✅" in result

    def test_handle_complex_operation_failure(self):
        """测试处理复杂操作 - 失败"""
        chain = TaskChain(device_id="test_device")
        chain.phone_agent = MagicMock()
        chain.phone_agent.execute_operation.return_value = (False, "操作失败")
        
        result = chain._handle_complex_operation("执行复杂任务")
        
        assert "❌" in result

    def test_stop_continuous_reply(self):
        """测试停止持续回复"""
        chain = TaskChain(device_id="test_device")
        chain.reply_chain = MagicMock()
        
        chain.stop_continuous_reply()
        
        chain.reply_chain.stop.assert_called_once()

    def test_stop_continuous_reply_no_chain(self):
        """测试停止持续回复 - 无chain"""
        chain = TaskChain(device_id="test_device")
        chain.reply_chain = None
        
        # 不应该抛出异常
        chain.stop_continuous_reply()

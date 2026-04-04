"""
GUI 控制器覆盖率缺口补充测试
============================

针对以下模块的未覆盖行编写定向测试：
- core.py: __init__, _setup_callbacks, _on_streaming_complete, get_callbacks, show_dashboard
- command.py: terminate_flag, multimodal 标签, CONTINUOUS_REPLY 解析, 音频转写, TTS播报, 终止分支
- tts_integration.py: _synthesize_welcome_message 各分支, _wait_audio_then_hide 循环
- file_ops.py: 大量错误文件 toast, 懒加载 processor, 不支持类型, 文件过大, 执行中清空/移除, 历史异常
- ui_state.py: show_toast, _do_reset_button_states, _do_clear_attached_files
"""
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from yuntai.gui.controller.command import CommandMixin
from yuntai.gui.controller.core import ControllerCore
from yuntai.gui.controller.file_ops import FileOpsMixin
from yuntai.gui.controller.tts_integration import TTSIntegrationMixin
from yuntai.gui.controller.ui_state import UIStateMixin


# ============ 辅助类 ============

class _Signal:
    """模拟 PyQt6 信号"""
    def __init__(self):
        self.calls = []

    def emit(self, *args):
        self.calls.append(args)

    def connect(self, fn):
        pass


class _Btn:
    """模拟按钮组件"""
    def __init__(self):
        self.enabled = True
        self.shown = False

    def setEnabled(self, value):
        self.enabled = value

    def show(self):
        self.shown = True


class _Text:
    """模拟文本组件"""
    def __init__(self, value=""):
        self.value = value
        self.readonly = True

    def toPlainText(self):
        return self.value

    def clear(self):
        self.value = ""

    def setText(self, value):
        self.value = value

    def setStyleSheet(self, _style):
        pass

    def setReadOnly(self, val):
        self.readonly = val

    def insertPlainText(self, txt):
        self.value += txt

    def ensureCursorVisible(self):
        pass

    def setFixedHeight(self, h):
        pass


class _Input:
    """模拟输入框组件"""
    def __init__(self, text=""):
        self._text = text

    def toPlainText(self):
        return self._text

    def clear(self):
        self._text = ""

    def setFixedHeight(self, h):
        pass


class _ImmediateThread:
    """立即执行线程，用于测试"""
    def __init__(self, target=None, daemon=None):
        self._target = target

    def start(self):
        if self._target:
            self._target()

    def is_alive(self):
        return False


# ============ core.py 未覆盖行测试 ============

class TestCoreInitAndCallbacks:
    """测试 core.py 中 __init__, _setup_callbacks, _on_streaming_complete, get_callbacks, show_dashboard"""

    def test_on_streaming_complete_logs_response_length(self):
        """覆盖 core.py:269 - _on_streaming_complete 日志输出"""
        core = ControllerCore.__new__(ControllerCore)
        # _on_streaming_complete 只是记录日志，不返回值
        core._on_streaming_complete("这是一段测试回复内容")
        # 验证不抛异常即可（纯日志方法）

    def test_get_callbacks_returns_list(self):
        """覆盖 core.py:278 - get_callbacks 调用 callback_manager"""
        core = ControllerCore.__new__(ControllerCore)
        callbacks = [MagicMock(), MagicMock()]
        core.callback_manager = MagicMock()
        core.callback_manager.get_callbacks.return_value = callbacks

        result = core.get_callbacks()
        assert result == callbacks
        core.callback_manager.get_callbacks.assert_called_once_with(include_global=True)

    def test_show_dashboard_creates_page_and_rebinds(self):
        """覆盖 core.py:390-392 - show_dashboard 调用 view.create_dashboard_page 和 _bind_dashboard_events"""
        core = ControllerCore.__new__(ControllerCore)
        calls = []
        core.view = SimpleNamespace(create_dashboard_page=lambda: calls.append("create_page"))
        core._bind_dashboard_events = lambda: calls.append("bind_events")

        core.show_dashboard()
        assert calls == ["create_page", "bind_events"]

    def test_setup_callbacks_registers_all_handlers(self):
        """覆盖 core.py:220-260 - _setup_callbacks 注册流式、日志、性能处理器"""
        core = ControllerCore.__new__(ControllerCore)
        core._streaming_output_signal = MagicMock()
        core._streaming_complete_signal = MagicMock()

        registered = []
        core.callback_manager = MagicMock()
        core.callback_manager.register_handler = lambda name, handler, is_global=False: registered.append(name)

        # 模拟 Callback 类
        import yuntai.gui.controller.core as core_mod

        with patch.object(core_mod, 'QtStreamingCallbackHandler', return_value=MagicMock()) as mock_streaming, \
             patch.object(core_mod, 'LoggingCallbackHandler', return_value=MagicMock()) as mock_logging, \
             patch.object(core_mod, 'PerformanceCallbackHandler', return_value=MagicMock()) as mock_perf:
            core._setup_callbacks()

        assert len(registered) == 3
        assert "gui_streaming" in registered
        assert "gui_logging" in registered
        assert "gui_performance" in registered


# ============ command.py 未覆盖行测试 ============

class TestCommandMixinCoverageGaps:
    """测试 command.py 中的未覆盖行"""

    def test_execute_command_clears_terminate_flag(self, monkeypatch):
        """覆盖 command.py:76 - terminate_flag.clear() 调用"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        flag_set = threading.Event()
        flag_set.set()  # 先设置为 True

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("do") if name == "command_input" else None)
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda *_a, **_k: None
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = flag_set
        obj.task_manager = SimpleNamespace(is_connected=True)
        obj._sync_device_to_task_chain = lambda: None
        obj.task_chain = SimpleNamespace(process=lambda _cmd: ("result", {"task_type": "free_chat"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="free_chat"))

        obj.execute_command()
        assert not flag_set.is_set()  # 验证 clear() 被调用

    def test_execute_command_with_output_text_appends(self, monkeypatch):
        """覆盖 command.py:80 - output_text 存在时调用 _append_output"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        output = _Text("")
        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(
            get_component=lambda name: _Input("test") if name == "command_input" else output if name == "output_text" else None
        )
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=True)
        obj._sync_device_to_task_chain = lambda: None
        obj.task_chain = SimpleNamespace(process=lambda _cmd: ("ok", {"task_type": "free_chat"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="free_chat"))

        obj.execute_command()
        # _append_output 应在 run_command 线程中被调用
        assert len(outputs) > 0

    def test_execute_command_multimodal_labels(self, monkeypatch):
        """覆盖 command.py:91-92, 106 - 附件模式下多模态标签输出和 _handle_multimodal_chat 调用"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = ["/fake/file.txt"]
        obj.view = SimpleNamespace(get_component=lambda name: _Input("看文件") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj._handle_multimodal_chat = lambda text, files: "多模态结果"

        obj.execute_command()
        assert any("多模态指令" in o for o in outputs)
        assert any("附件数量" in o for o in outputs)

    def test_execute_command_continuous_reply_parse_success(self, monkeypatch):
        """覆盖 command.py:114-128 - CONTINUOUS_REPLY 解析成功路径"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("reply") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=True, task_args={}, device_id="dev")
        obj._sync_device_to_task_chain = lambda: None
        obj.task_chain = SimpleNamespace(process=lambda _cmd: ("🔄CONTINUOUS_REPLY:微信:张三", {"task_type": "auto_reply"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj.start_continuous_reply_thread = lambda *args: outputs.append("started_continuous")

        obj.execute_command()
        assert "started_continuous" in outputs

    def test_execute_command_continuous_reply_parse_fail(self, monkeypatch):
        """覆盖 command.py:114-128 - CONTINUOUS_REPLY 解析失败路径"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("reply") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=True)
        obj._sync_device_to_task_chain = lambda: None
        # 返回一个格式错误的 CONTINUOUS_REPLY（只有1个部分，不是2个）
        obj.task_chain = SimpleNamespace(process=lambda _cmd: ("🔄CONTINUOUS_REPLY:onlyonepart", {"task_type": "auto_reply"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []

        obj.execute_command()
        # len(parts) != 2，不会走启动路径，result 会被当作普通结果显示

    def test_execute_command_continuous_reply_device_not_connected(self, monkeypatch):
        """覆盖 command.py:118-120 - CONTINUOUS_REPLY 解析成功但设备未连接"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("reply") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=False, task_args={}, device_id="dev")
        obj._sync_device_to_task_chain = lambda: None
        obj.task_chain = SimpleNamespace(process=lambda _cmd: ("🔄CONTINUOUS_REPLY:微信:张三", {"task_type": "auto_reply"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="auto_reply"))

        obj.execute_command()
        assert any("设备未连接" in o for o in outputs)

    def test_execute_command_continuous_reply_exception_in_parsing(self, monkeypatch):
        """覆盖 command.py:125-128 - CONTINUOUS_REPLY 解析抛异常"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("reply") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=True, task_args={}, device_id="dev")
        obj._sync_device_to_task_chain = lambda: None

        # 返回包含 CONTINUOUS_REPLY 但属性访问会失败的结果
        class _BadResult:
            def __contains__(self, item):
                if item == "🔄CONTINUOUS_REPLY:":
                    return True
                raise RuntimeError("bad contains")

            def __str__(self):
                return "🔄CONTINUOUS_REPLY:app:obj"

            def isinstance_check(self):
                return True

        obj.task_chain = SimpleNamespace(process=lambda _cmd: (_BadResult(), {"task_type": "auto_reply"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []

        obj.execute_command()

    def test_execute_command_non_free_chat_result_display(self, monkeypatch):
        """覆盖 command.py:133-134 - 非 free_chat 时的结果输出"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("do") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=True)
        obj._sync_device_to_task_chain = lambda: None
        obj.task_chain = SimpleNamespace(process=lambda _cmd: ("普通任务结果", {"task_type": "device_task"}))
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="device_task"))

        obj.execute_command()
        # 非 free_chat，非附件，不会输出 "🎉 结果" 前缀

    def test_execute_command_continuous_mode_detection(self, monkeypatch):
        """覆盖 command.py:136-143 - 检测持续回复模式字符串"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

        obj = CommandMixin.__new__(CommandMixin)
        obj.is_executing = False
        obj.attached_files = []
        obj.view = SimpleNamespace(get_component=lambda name: _Input("auto") if name == "command_input" else None)
        outputs = []
        obj.show_toast = lambda *_a, **_k: None
        obj._append_output = lambda text: outputs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._enable_execute_button_signal = _Signal()
        obj._disable_terminate_button_signal = _Signal()
        obj._clear_attached_files_signal = _Signal()
        obj.terminate_flag = threading.Event()
        obj.task_manager = SimpleNamespace(is_connected=True)
        obj._sync_device_to_task_chain = lambda: None
        obj.task_chain = SimpleNamespace(
            process=lambda _cmd: ("已进入持续回复模式", {"task_type": "auto_reply"})
        )
        obj.message_queue = SimpleNamespace(put=lambda *_a: None)
        obj.is_continuous_mode = False
        obj.active_threads = []
        obj.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="auto_reply"))

        obj.execute_command()
        assert any("持续回复模式" in o for o in outputs)

    def test_handle_multimodal_chat_audio_transcription(self, tmp_path):
        """覆盖 command.py:204-206 - 多模态处理成功时检查 audio_transcription"""
        f = tmp_path / "audio.wav"
        f.write_text("audio", encoding="utf-8")

        obj = CommandMixin.__new__(CommandMixin)
        logs = []
        obj._append_output = lambda text: logs.append(text)
        obj._get_chat_history_for_multimodal = lambda: []
        obj._save_multimodal_chat_history = lambda *_args: None
        obj.task_manager = SimpleNamespace(tts_manager=SimpleNamespace(tts_enabled=False))

        class _MMWithAudio:
            def process_with_files(self, **kwargs):
                return True, "response", {"audio_transcription": "你好世界"}

        obj.multimodal_processor = _MMWithAudio()
        result = obj._handle_multimodal_chat("听这个", [str(f)])
        assert result == "response"
        assert any("多模态分析完成" in l for l in logs)

    def test_handle_multimodal_chat_tts_speak(self, tmp_path):
        """覆盖 command.py:210-218 - 多模态成功后 TTS 播报"""
        f = tmp_path / "doc.txt"
        f.write_text("x", encoding="utf-8")

        speak_logs = []

        class _TTSManager:
            tts_enabled = True
            def speak_text_intelligently(self, text):
                speak_logs.append(text)

        obj = CommandMixin.__new__(CommandMixin)
        logs = []
        obj._append_output = lambda text: logs.append(text)
        obj._get_chat_history_for_multimodal = lambda: []
        obj._save_multimodal_chat_history = lambda *_args: None
        obj.task_manager = SimpleNamespace(tts_manager=_TTSManager())

        class _MM:
            def process_with_files(self, **kwargs):
                return True, "这是一段很长的多模态回复内容，用于触发 TTS", {}

        obj.multimodal_processor = _MM()

        # Timer 会在子线程中延迟执行，mock threading.Timer
        import yuntai.gui.controller.command as mod
        original_timer = mod.threading.Timer

        def fake_timer(delay, fn):
            fn()  # 立即执行
            return SimpleNamespace(start=lambda: None)

        mod.threading.Timer = fake_timer
        try:
            result = obj._handle_multimodal_chat("看看", [str(f)])
            assert result == "这是一段很长的多模态回复内容，用于触发 TTS"
            assert speak_logs  # TTS 播报被调用
        finally:
            mod.threading.Timer = original_timer

    def test_handle_multimodal_chat_tts_speak_failure(self, tmp_path):
        """覆盖 command.py:214-216 - TTS 播报失败"""
        f = tmp_path / "doc.txt"
        f.write_text("x", encoding="utf-8")

        class _BadTTS:
            tts_enabled = True
            def speak_text_intelligently(self, text):
                raise RuntimeError("TTS引擎故障")

        obj = CommandMixin.__new__(CommandMixin)
        logs = []
        obj._append_output = lambda text: logs.append(text)
        obj._get_chat_history_for_multimodal = lambda: []
        obj._save_multimodal_chat_history = lambda *_args: None
        obj.task_manager = SimpleNamespace(tts_manager=_BadTTS())

        class _MM:
            def process_with_files(self, **kwargs):
                return True, "这是一段长回复内容来触发TTS播报测试", {}

        obj.multimodal_processor = _MM()

        import yuntai.gui.controller.command as mod
        original_timer = mod.threading.Timer

        def fake_timer(delay, fn):
            fn()
            return SimpleNamespace(start=lambda: None)

        mod.threading.Timer = fake_timer
        try:
            result = obj._handle_multimodal_chat("test", [str(f)])
            assert any("语音播报失败" in l for l in logs)
        finally:
            mod.threading.Timer = original_timer

    def test_continuous_reply_thread_failure_path(self, monkeypatch):
        """覆盖 command.py:281-285 - 持续回复线程执行失败"""
        import yuntai.gui.controller.command as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

        class _FailReply:
            def __init__(self, **kwargs):
                pass
            def continuous_reply(self, *_args):
                return False, "回复失败: 超时"

        monkeypatch.setattr(mod, "ReplyChain", _FailReply)

        obj = CommandMixin.__new__(CommandMixin)
        logs = []
        obj._append_output = lambda text: logs.append(text)
        obj._disable_execute_button = lambda: None
        obj._enable_terminate_button = lambda: None
        obj._reset_button_states_signal = _Signal()
        obj.task_manager = SimpleNamespace(file_manager=object(), tts_manager=object())
        obj.active_threads = []
        obj.terminate_flag = threading.Event()
        obj.is_continuous_mode = False

        obj.start_continuous_reply_thread({}, "微信", "张三", "dev")
        assert any("⏹️" in l for l in logs)

    def test_terminate_operation_no_active_threads(self):
        """覆盖 command.py:321-322 - 终止时没有活跃线程"""
        obj = CommandMixin.__new__(CommandMixin)
        toasts = []
        logs = []
        obj._append_output = lambda text: logs.append(text)
        obj._cleanup_active_threads = lambda: None
        obj.show_toast = lambda msg, level: toasts.append((msg, level))
        obj._disable_terminate_button = lambda: None
        obj.is_executing = True
        obj.terminate_flag = threading.Event()
        obj.terminating = threading.Event()
        obj.active_threads = []
        obj.is_continuous_mode = False
        obj.task_chain = SimpleNamespace(stop_continuous_reply=lambda: None)
        obj._current_reply_chain = None

        obj.terminate_operation()
        assert any("没有正在执行的操作" in t[0] for t in toasts)

    def test_terminate_operation_continuous_mode(self):
        """覆盖 command.py:329 - 终止持续回复模式"""
        obj = CommandMixin.__new__(CommandMixin)
        toasts = []
        logs = []
        obj._append_output = lambda text: logs.append(text)
        obj._cleanup_active_threads = lambda: None
        obj.show_toast = lambda msg, level: toasts.append((msg, level))
        obj._disable_terminate_button = lambda: None
        obj.is_executing = True
        obj.terminate_flag = threading.Event()
        obj.terminating = threading.Event()
        obj.active_threads = [SimpleNamespace(is_alive=lambda: True)]
        obj.is_continuous_mode = True
        obj.task_chain = SimpleNamespace(stop_continuous_reply=lambda: None)
        obj._current_reply_chain = SimpleNamespace(stop=lambda: None)

        obj.terminate_operation()
        assert any("持续回复模式" in l for l in logs)


# ============ tts_integration.py 未覆盖行测试 ============

class TestTTSIntegrationCoverageGaps:
    """测试 tts_integration.py 中的未覆盖行"""

    def test_synthesize_welcome_message_all_models_set(self, monkeypatch):
        """覆盖 tts_integration.py:73-75 - 所有模型设置成功后合成欢迎语"""
        import yuntai.gui.controller.tts_integration as mod
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

        hide_sig = _Signal()
        show_sig = _Signal()

        tts = SimpleNamespace(
            tts_files_database={
                "gpt": {"gpt_model": 1},
                "sovits": {"sovits_model": 1},
                "audio": {"/tmp/audio.wav": 1},
                "text": {"audio.txt": 1},
            },
            get_current_model=lambda kind: {
                "gpt": "gpt_model",
                "sovits": "sovits_model",
                "audio": "/tmp/audio.wav",
                "text": "audio.txt",
            }.get(kind),
            set_current_model=lambda *_a: None,
            speak_text_intelligently=lambda *_a: None,
            is_playing_audio=False,
        )

        obj = TTSIntegrationMixin.__new__(TTSIntegrationMixin)
        obj.task_manager = SimpleNamespace(tts_manager=tts)
        obj._hide_tts_loading_signal = hide_sig
        obj._show_tts_loading_signal = show_sig

        obj._synthesize_welcome_message()
        # 验证发出了 "正在合成欢迎语..." 信号
        assert any("正在合成欢迎语" in str(c) for c in show_sig.calls)
        # 验证发出了隐藏信号
        assert len(hide_sig.calls) > 0

    def test_synthesize_welcome_message_attribute_error(self):
        """覆盖 tts_integration.py:76-78 - AttributeError 异常分支"""
        tts = SimpleNamespace(
            tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}},
            get_current_model=lambda _kind: None,
        )
        # 没有设置 set_current_model，触发 AttributeError

        hide_sig = _Signal()
        obj = TTSIntegrationMixin.__new__(TTSIntegrationMixin)
        obj.task_manager = SimpleNamespace(tts_manager=tts)
        obj._hide_tts_loading_signal = hide_sig
        obj._show_tts_loading_signal = _Signal()

        obj._synthesize_welcome_message()
        assert hide_sig.calls

    def test_synthesize_welcome_message_runtime_error(self):
        """覆盖 tts_integration.py:79-82 - RuntimeError 异常分支"""
        class _BadTTS:
            tts_files_database = {"gpt": {}, "sovits": {}, "audio": {}, "text": {}}

            def get_current_model(self, kind):
                raise RuntimeError("widget destroyed")

        hide_sig = _Signal()
        obj = TTSIntegrationMixin.__new__(TTSIntegrationMixin)
        obj.task_manager = SimpleNamespace(tts_manager=_BadTTS())
        obj._hide_tts_loading_signal = hide_sig
        obj._show_tts_loading_signal = _Signal()

        obj._synthesize_welcome_message()
        assert hide_sig.calls

    def test_synthesize_welcome_message_generic_exception(self):
        """覆盖 tts_integration.py:83-85 - 通用 Exception 异常分支"""
        class _BadTTS:
            tts_files_database = {"gpt": {}, "sovits": {}, "audio": {}, "text": {}}

            def get_current_model(self, kind):
                raise ValueError("unexpected error")

        hide_sig = _Signal()
        obj = TTSIntegrationMixin.__new__(TTSIntegrationMixin)
        obj.task_manager = SimpleNamespace(tts_manager=_BadTTS())
        obj._hide_tts_loading_signal = hide_sig
        obj._show_tts_loading_signal = _Signal()

        obj._synthesize_welcome_message()
        assert hide_sig.calls

    def test_wait_audio_then_hide_loops_while_playing(self, monkeypatch):
        """覆盖 tts_integration.py:95-96 - 音频播放中循环等待"""
        import yuntai.gui.controller.tts_integration as mod

        call_count = [0]
        original_sleep = time.sleep

        def counting_sleep(duration):
            call_count[0] += 1

        # 模拟先播放2次再停止
        play_count = [0]
        class _PlayingTTS:
            @property
            def is_playing_audio(self):
                play_count[0] += 1
                return play_count[0] <= 2  # 前两次 True，之后 False

        hide_sig = _Signal()
        obj = TTSIntegrationMixin.__new__(TTSIntegrationMixin)
        obj.task_manager = SimpleNamespace(tts_manager=_PlayingTTS())
        obj._hide_tts_loading_signal = hide_sig

        monkeypatch.setattr(mod.time, "sleep", counting_sleep)
        monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
        obj._wait_audio_then_hide()

        assert call_count[0] >= 2  # 至少 sleep 了 2 次
        assert hide_sig.calls


# ============ file_ops.py 未覆盖行测试 ============

class TestFileOpsCoverageGaps:
    """测试 file_ops.py 中的未覆盖行"""

    def test_show_file_upload_many_unsupported_files(self):
        """覆盖 file_ops.py:76 - 不支持文件超过3个时的 toast"""
        obj = FileOpsMixin.__new__(FileOpsMixin)
        toasts = []
        obj.show_toast = lambda msg, level: toasts.append((msg, level))
        obj.attached_files = []
        obj.is_executing = False

        # 返回5个文件，全部不支持
        obj.view = SimpleNamespace(
            show_file_upload_dialog=lambda: ["a.bin", "b.bin", "c.bin", "d.bin", "e.bin"],
            show_attached_files=lambda *_a: None,
        )
        obj._check_file_supported = lambda p: (False, "不支持的格式")

        obj.show_file_upload()
        assert any("跳过 5 个不支持的文件" in t[0] for t in toasts)

    def test_show_file_upload_exception_handler(self):
        """覆盖 file_ops.py:78-80 - 文件选择异常处理"""
        obj = FileOpsMixin.__new__(FileOpsMixin)
        toasts = []
        obj.show_toast = lambda msg, level: toasts.append((msg, level))
        obj.attached_files = []
        obj.is_executing = False

        obj.view = SimpleNamespace(
            show_file_upload_dialog=lambda: (_ for _ in ()).throw(RuntimeError("dialog error")),
            show_attached_files=lambda *_a: None,
        )

        obj.show_file_upload()
        assert any("文件选择失败" in t[0] for t in toasts)

    def test_check_file_supported_lazy_init_processor(self, monkeypatch, tmp_path):
        """覆盖 file_ops.py:93-94 - multimodal_processor 懒加载"""
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")

        fake_processor = MagicMock()
        fake_processor.is_file_supported = lambda p: True
        fake_processor.check_file_size = lambda p: (True, "ok")

        fake_mod = SimpleNamespace(MultimodalProcessor=lambda: fake_processor)
        monkeypatch.setitem(__import__("sys").modules, "yuntai.processors.multimodal_processor", fake_mod)

        obj = FileOpsMixin.__new__(FileOpsMixin)
        obj.multimodal_processor = None  # 强制懒加载

        result, msg = obj._check_file_supported(str(f))
        assert result is True
        assert obj.multimodal_processor is fake_processor

    def test_check_file_supported_unsupported_type(self, tmp_path):
        """覆盖 file_ops.py:100-101 - 不支持的文件类型"""
        f = tmp_path / "test.xyz"
        f.write_text("data", encoding="utf-8")

        obj = FileOpsMixin.__new__(FileOpsMixin)
        obj.multimodal_processor = MagicMock()
        obj.multimodal_processor.is_file_supported = lambda p: False

        result, msg = obj._check_file_supported(str(f))
        assert result is False
        assert ".xyz" in msg

    def test_check_file_supported_file_too_large(self, tmp_path):
        """覆盖 file_ops.py:105 - 文件过大"""
        f = tmp_path / "big.pdf"
        f.write_text("big", encoding="utf-8")

        obj = FileOpsMixin.__new__(FileOpsMixin)
        obj.multimodal_processor = MagicMock()
        obj.multimodal_processor.is_file_supported = lambda p: True
        obj.multimodal_processor.check_file_size = lambda p: (False, "超过10MB")

        result, msg = obj._check_file_supported(str(f))
        assert result is False
        assert "文件过大" in msg

    def test_clear_attached_files_while_executing(self):
        """覆盖 file_ops.py:113-114 - 执行中清空文件"""
        obj = FileOpsMixin.__new__(FileOpsMixin)
        toasts = []
        obj.show_toast = lambda msg, level: toasts.append((msg, level))
        obj.is_executing = True

        obj.clear_attached_files()
        assert any("任务执行中" in t[0] for t in toasts)

    def test_remove_attached_file_while_executing(self):
        """覆盖 file_ops.py:133-134 - 执行中移除文件"""
        obj = FileOpsMixin.__new__(FileOpsMixin)
        toasts = []
        obj.show_toast = lambda msg, level: toasts.append((msg, level))
        obj.is_executing = True

        obj.remove_attached_file("/some/file.txt")
        assert any("任务执行中" in t[0] for t in toasts)

    def test_get_chat_history_exception(self):
        """覆盖 file_ops.py:165-167 - 获取历史记录异常"""
        obj = FileOpsMixin.__new__(FileOpsMixin)
        obj.task_manager = SimpleNamespace(
            file_manager=SimpleNamespace(
                safe_read_json_file=lambda *_a, **_k: (_ for _ in ()).throw(IOError("disk error"))
            )
        )

        result = obj._get_chat_history_for_multimodal()
        assert result == []

    def test_save_multimodal_chat_history_exception(self):
        """覆盖 file_ops.py:189-190 - 保存聊天历史异常"""
        obj = FileOpsMixin.__new__(FileOpsMixin)
        obj.task_manager = SimpleNamespace(
            file_manager=SimpleNamespace(
                save_conversation_history=lambda _data: (_ for _ in ()).throw(IOError("write error"))
            )
        )

        # 不应抛出异常，只记录日志
        obj._save_multimodal_chat_history("text", ["/f.txt"], "reply")


# ============ ui_state.py 未覆盖行测试 ============

class TestUIStateCoverageGaps:
    """测试 ui_state.py 中的未覆盖行"""

    def test_show_toast_with_widget(self):
        """覆盖 ui_state.py:44-45 - view 有 toast_widget 时显示 toast"""
        toast_calls = []
        toast_widget = SimpleNamespace(show_toast=lambda msg, level, duration=2000: toast_calls.append((msg, level, duration)))

        obj = UIStateMixin.__new__(UIStateMixin)
        obj.view = SimpleNamespace(toast_widget=toast_widget)

        obj.show_toast("测试消息", "info")
        assert toast_calls == [("测试消息", "info", 2000)]

        obj.show_toast("成功", "success")
        assert len(toast_calls) == 2

    def test_do_reset_button_states(self):
        """覆盖 ui_state.py:95-97 - _do_reset_button_states 发射信号并重置状态"""
        enable_exec_sig = _Signal()
        disable_term_sig = _Signal()

        obj = UIStateMixin.__new__(UIStateMixin)
        obj._enable_execute_button_signal = enable_exec_sig
        obj._disable_terminate_button_signal = disable_term_sig
        obj.is_executing = True

        obj._do_reset_button_states()
        assert enable_exec_sig.calls == [()]
        assert disable_term_sig.calls == [()]
        assert obj.is_executing is False

    def test_do_clear_attached_files_success(self):
        """覆盖 ui_state.py:101-102 - _do_clear_attached_files 正常清理"""
        obj = UIStateMixin.__new__(UIStateMixin)
        cleared = []
        obj.clear_attached_files = lambda: cleared.append(True)
        obj.is_executing = False

        obj._do_clear_attached_files()
        assert cleared == [True]

    def test_do_clear_attached_files_exception(self):
        """覆盖 ui_state.py:103-104 - _do_clear_attached_files 异常处理"""
        obj = UIStateMixin.__new__(UIStateMixin)
        obj.clear_attached_files = lambda: (_ for _ in ()).throw(RuntimeError("clear failed"))

        # 不应抛出异常
        obj._do_clear_attached_files()

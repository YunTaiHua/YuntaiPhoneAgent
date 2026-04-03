import threading
from types import SimpleNamespace

from yuntai.gui.controller.command import CommandMixin
from yuntai.gui.controller.core import ControllerCore


class _Signal:
    def __init__(self):
        self.calls = []

    def emit(self, *args):
        self.calls.append(args)


class _Btn:
    def __init__(self):
        self.enabled = True
        self.shown = False

    def setEnabled(self, enabled):
        self.enabled = enabled

    def show(self):
        self.shown = True


class _Out:
    def __init__(self):
        self.readonly = True
        self.value = ""
        self.cursor_visible = False

    def setReadOnly(self, val):
        self.readonly = val

    def insertPlainText(self, txt):
        self.value += txt

    def ensureCursorVisible(self):
        self.cursor_visible = True


def test_command_multimodal_failure_and_exception_paths(monkeypatch, tmp_path):
    obj = CommandMixin.__new__(CommandMixin)
    logs = []
    obj._append_output = lambda text: logs.append(text)
    obj._get_chat_history_for_multimodal = lambda: []
    obj._save_multimodal_chat_history = lambda *_args: None
    obj.task_manager = SimpleNamespace(tts_manager=SimpleNamespace(tts_enabled=False))

    f = tmp_path / "a.txt"
    f.write_text("x", encoding="utf-8")

    class _FailMM:
        def process_with_files(self, **_kwargs):
            return False, "bad", {}

    obj.multimodal_processor = _FailMM()
    assert "多模态分析失败" in obj._handle_multimodal_chat("hi", [str(f)])

    class _BoomMM:
        def process_with_files(self, **_kwargs):
            raise RuntimeError("boom")

    obj.multimodal_processor = _BoomMM()
    assert "多模态处理失败" in obj._handle_multimodal_chat("hi", [str(f)])

    # lazy init processor path
    class _OkMM:
        def process_with_files(self, **_kwargs):
            return True, "ok", {}

    fake_mod = SimpleNamespace(MultimodalProcessor=lambda: _OkMM())
    monkeypatch.setitem(__import__("sys").modules, "yuntai.processors.multimodal_processor", fake_mod)
    obj.multimodal_processor = None
    assert obj._handle_multimodal_chat("hello", [str(f)]) == "ok"


def test_command_start_continuous_reply_thread_branches(monkeypatch):
    obj = CommandMixin.__new__(CommandMixin)
    logs = []
    obj._append_output = lambda text: logs.append(text)
    obj._disable_execute_button = lambda: logs.append("disable_exec")
    obj._enable_terminate_button = lambda: logs.append("enable_term")
    obj._reset_button_states_signal = _Signal()
    obj.task_manager = SimpleNamespace(
        file_manager=object(),
        tts_manager=object(),
        device_id="dev",
        task_args={"a": 1},
    )
    obj.active_threads = []
    obj.terminate_flag = threading.Event()
    obj.is_continuous_mode = True

    obj.start_continuous_reply_thread({}, "app", "target", "dev")
    assert any("已经有持续回复" in x for x in logs)

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            self._target()

        def is_alive(self):
            return False

    class _FakeReply:
        def __init__(self, **_kwargs):
            pass

        def continuous_reply(self, *_args):
            return True, "done"

    import yuntai.gui.controller.command as mod

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(mod, "ReplyChain", _FakeReply)

    logs.clear()
    obj.is_continuous_mode = False
    obj.start_continuous_reply_thread({}, "app", "target", "dev")
    assert any("启动持续回复模式" in x for x in logs)
    assert obj._reset_button_states_signal.calls


def test_command_terminate_operation_full_and_execute_no_input():
    obj = CommandMixin.__new__(CommandMixin)
    logs = []
    toasts = []
    obj._append_output = lambda text: logs.append(text)
    obj._cleanup_active_threads = lambda: None
    obj.show_toast = lambda msg, level: toasts.append((msg, level))
    obj._disable_terminate_button = lambda: logs.append("disable_term")
    obj._enable_execute_button_signal = _Signal()
    obj._disable_terminate_button_signal = _Signal()
    obj._clear_attached_files_signal = _Signal()
    obj.message_queue = SimpleNamespace(put=lambda *_args: None)
    obj.active_threads = [SimpleNamespace(is_alive=lambda: True)]
    obj.is_continuous_mode = False
    obj.is_executing = True
    obj.terminate_flag = threading.Event()
    obj.terminating = threading.Event()
    obj.task_chain = SimpleNamespace(stop_continuous_reply=lambda: logs.append("stop_chain"))
    obj._current_reply_chain = SimpleNamespace(stop=lambda: logs.append("stop_reply"))

    obj.terminate_operation()
    assert obj.terminate_flag.is_set()
    assert obj.terminating.is_set()
    assert any("已发送终止信号" in x[0] for x in toasts)

    obj2 = CommandMixin.__new__(CommandMixin)
    obj2.is_executing = False
    obj2.view = SimpleNamespace(get_component=lambda _name: None)
    obj2.execute_command()


def test_command_execute_command_short_circuits_and_sync_and_simulate_enter(monkeypatch):
    # already executing
    c0 = CommandMixin.__new__(CommandMixin)
    toasts0 = []
    c0.is_executing = True
    c0.show_toast = lambda msg, level: toasts0.append((msg, level))
    c0.execute_command()
    assert toasts0 and toasts0[0][1] == "warning"

    # empty command and no attachments
    class _Input:
        def __init__(self):
            self.height = None

        def toPlainText(self):
            return "   "

        def clear(self):
            return None

        def setFixedHeight(self, h):
            self.height = h

    c1 = CommandMixin.__new__(CommandMixin)
    toasts1 = []
    c1.is_executing = False
    c1.attached_files = []
    c1.view = SimpleNamespace(get_component=lambda name: _Input() if name == "command_input" else None)
    c1.show_toast = lambda msg, level: toasts1.append((msg, level))
    c1.execute_command()
    assert toasts1 and "请输入命令或选择文件" in toasts1[0][0]

    # sync only when connected
    c2 = CommandMixin.__new__(CommandMixin)
    c2.task_manager = SimpleNamespace(is_connected=False, device_id="d", task_args={})
    c2.task_chain = SimpleNamespace(device_id="", task_args=None)
    c2._sync_device_to_task_chain()
    assert c2.task_chain.device_id == ""

    c2.task_manager.is_connected = True
    c2._sync_device_to_task_chain()
    assert c2.task_chain.device_id == "d"

    # simulate_enter success and failure
    import yuntai.core.agent_executor as exec_mod

    c3 = CommandMixin.__new__(CommandMixin)
    logs = []
    c3._append_output = lambda text: logs.append(text)
    monkeypatch.setattr(exec_mod.AgentExecutor, "user_confirm", staticmethod(lambda: None))
    c3.simulate_enter()
    assert any("用户已确认" in x for x in logs)

    c4 = CommandMixin.__new__(CommandMixin)
    logs2 = []
    c4._append_output = lambda text: logs2.append(text)
    monkeypatch.setattr(
        exec_mod.AgentExecutor,
        "user_confirm",
        staticmethod(lambda: (_ for _ in ()).throw(RuntimeError("x"))),
    )
    c4.simulate_enter()
    assert any("发送确认信号失败" in x for x in logs2)


def test_command_execute_command_thread_paths(monkeypatch):
    import yuntai.gui.controller.command as mod

    class _ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

        def is_alive(self):
            return False

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(mod.QTimer, "singleShot", lambda _ms, cb: cb())

    class _Input:
        def __init__(self, text):
            self._text = text

        def toPlainText(self):
            return self._text

        def clear(self):
            self._text = ""

        def setFixedHeight(self, _h):
            return None

    class _TermFlag:
        def __init__(self):
            self._set = False

        def is_set(self):
            return self._set

        def clear(self):
            self._set = False

    # not connected, non-free task -> early return
    inputs = {"command_input": _Input("do")}
    c = CommandMixin.__new__(CommandMixin)
    c.is_executing = False
    c.attached_files = []
    c.view = SimpleNamespace(get_component=lambda name: inputs.get(name))
    c.show_toast = lambda *_a, **_k: None
    c._append_output = lambda *_a, **_k: None
    c._disable_execute_button = lambda: None
    c._enable_terminate_button = lambda: None
    c._enable_execute_button_signal = _Signal()
    c._disable_terminate_button_signal = _Signal()
    c._clear_attached_files_signal = _Signal()
    c.terminate_flag = _TermFlag()
    c.task_manager = SimpleNamespace(is_connected=False)
    c.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="device_task"))
    c.message_queue = SimpleNamespace(put=lambda *_a: None)
    c.is_continuous_mode = False
    c.active_threads = []
    c.execute_command()
    assert c.is_executing is False

    # connected free_chat result path
    c2 = CommandMixin.__new__(CommandMixin)
    c2.is_executing = False
    c2.attached_files = []
    c2.view = SimpleNamespace(get_component=lambda name: {"command_input": _Input("chat")}.get(name))
    outputs = []
    c2.show_toast = lambda *_a, **_k: None
    c2._append_output = lambda text: outputs.append(text)
    c2._disable_execute_button = lambda: None
    c2._enable_terminate_button = lambda: None
    c2._enable_execute_button_signal = _Signal()
    c2._disable_terminate_button_signal = _Signal()
    c2._clear_attached_files_signal = _Signal()
    c2.terminate_flag = _TermFlag()
    c2.task_manager = SimpleNamespace(is_connected=True)
    c2._sync_device_to_task_chain = lambda: None
    c2.task_chain = SimpleNamespace(process=lambda _cmd: ("answer", {"task_type": "free_chat"}))
    c2.judgement_agent = SimpleNamespace(judge=lambda _cmd: SimpleNamespace(task_type="free_chat"))
    c2.message_queue = SimpleNamespace(put=lambda *_a: None)
    c2.is_continuous_mode = False
    c2.active_threads = []
    c2.execute_command()
    assert any("🎉 结果" in t for t in outputs)


def test_command_clear_output_and_connected_guard_branches():
    class _Output:
        def __init__(self):
            self.read_only = True
            self.cleared = 0

        def setReadOnly(self, v):
            self.read_only = v

        def clear(self):
            self.cleared += 1

    out = _Output()
    c = CommandMixin.__new__(CommandMixin)
    msgs = []
    c.view = SimpleNamespace(get_component=lambda name: out if name == "output_text" else None)
    c.show_toast = lambda msg, level: msgs.append((msg, level))
    c.clear_output()
    assert out.cleared == 1 and out.read_only is True
    assert msgs and msgs[-1][1] == "info"

    c2 = CommandMixin.__new__(CommandMixin)
    c2.task_manager = SimpleNamespace(is_connected=False)
    c2.task_chain = SimpleNamespace(device_id="x", task_args={"a": 1})
    c2._sync_device_to_task_chain()
    assert c2.task_chain.device_id == "x"


def test_core_output_helpers_and_theme_toggle_and_connection_paths():
    out = _Out()
    enter_btn = _Btn()
    comps = {"output_text": out, "enter_button": enter_btn}
    calls = []

    core = ControllerCore.__new__(ControllerCore)
    core.view = SimpleNamespace(
        get_component=lambda name: comps.get(name),
        current_page_index=0,
        is_dark_theme=False,
        toggle_theme=lambda: calls.append("toggle") or setattr(core.view, "is_dark_theme", True),
    )
    core._output_signal = _Signal()
    core._bind_dashboard_events = lambda: calls.append("bind_dashboard")
    core.connection_handler = SimpleNamespace(_bind_events=lambda: calls.append("bind_conn"), _update_connection_status_gui=lambda ok: calls.append(("conn", ok)))
    core.tts_handler = SimpleNamespace(_events_bound=True, _events_bound_success=True, _bind_events=lambda: calls.append("bind_tts"))
    core.system_handler = SimpleNamespace(_bind_history_events=lambda: calls.append("bind_history"), _bind_settings_events=lambda: calls.append("bind_settings"))
    core.dynamic_handler = SimpleNamespace(_bind_events=lambda: calls.append("bind_dynamic"))
    core.show_toast = lambda msg, level: calls.append((msg, level))

    core._append_output("abc")
    assert core._output_signal.calls == [("abc",)]
    core._do_append_output_from_signal("xyz")
    assert out.value.endswith("xyz")
    core._highlight_enter_button()
    assert enter_btn.shown is True

    core._enable_execute_button = lambda: calls.append("enable_exec")
    core._disable_terminate_button = lambda: calls.append("disable_term")
    core.is_executing = True
    core._reset_button_states()
    assert core.is_executing is False

    core.toggle_theme()
    assert core.tts_handler._events_bound is False
    assert core.tts_handler._events_bound_success is False

    core.task_manager = SimpleNamespace(check_initial_connection=lambda: None, is_connected=True, device_id="d1")
    core.check_initial_connection()
    assert ("conn", True) in calls

    core.task_manager = SimpleNamespace(check_initial_connection=lambda: (_ for _ in ()).throw(RuntimeError("x")))
    core.check_initial_connection()


def test_core_rebind_events_process_messages_and_helpers():
    calls = []
    core = ControllerCore.__new__(ControllerCore)
    core._bind_dashboard_events = lambda: calls.append("dashboard")
    core.connection_handler = SimpleNamespace(_bind_events=lambda: calls.append("conn"))
    core.tts_handler = SimpleNamespace(_bind_events=lambda: calls.append("tts"))
    core.system_handler = SimpleNamespace(
        _bind_history_events=lambda: calls.append("history"),
        _bind_settings_events=lambda: calls.append("settings"),
    )
    core.dynamic_handler = SimpleNamespace(_bind_events=lambda: calls.append("dynamic"))
    for idx in range(7):
        core._rebind_current_page_events(idx)
    assert calls[:6] == ["dashboard", "conn", "tts", "history", "dynamic", "settings"]

    # process_messages success and exception
    toasts = []
    core2 = ControllerCore.__new__(ControllerCore)
    items = [("info", "a"), ("success", "b")]

    class _Q:
        def empty(self):
            return len(items) == 0

        def get_nowait(self):
            return items.pop(0)

    core2.message_queue = _Q()
    core2.show_toast = lambda msg, level: toasts.append((msg, level))
    core2.process_messages()
    assert len(toasts) == 2

    class _QBad:
        def empty(self):
            return False

        def get_nowait(self):
            raise RuntimeError("boom")

    core2.message_queue = _QBad()
    core2.process_messages()

    # cleanup active threads and setup callback
    core3 = ControllerCore.__new__(ControllerCore)

    class _T:
        def __init__(self, alive):
            self._alive = alive

        def is_alive(self):
            return self._alive

    core3.active_threads = [_T(True), _T(False)]
    core3._cleanup_active_threads()
    assert len(core3.active_threads) == 1
    core3.view = SimpleNamespace(_device_type_callback=None)
    core3._on_device_type_changed = lambda *_a, **_k: None
    core3._setup_device_type_callback()
    assert callable(core3.view._device_type_callback)


def test_core_format_agent_event_text_branches_and_handler_emit():
    core = ControllerCore.__new__(ControllerCore)
    core._output_signal = _Signal()

    assert core._format_agent_event_text({"type": "run_started", "payload": {}}) == ""
    assert "任务类型" in core._format_agent_event_text({"type": "task_type", "payload": {"task_type": "free_chat"}})
    assert "思考过程" in core._format_agent_event_text({"type": "task_type", "payload": {"task_type": "device"}})
    assert core._format_agent_event_text({"type": "thinking_chunk", "payload": {"text": "abc"}}) == "abc"
    assert core._format_agent_event_text({"type": "thinking_complete", "payload": {}}) == "\n"
    assert "动作" in core._format_agent_event_text({"type": "action_decoded", "payload": {"action": {"k": "v"}}})
    assert core._format_agent_event_text({"type": "action_executed", "payload": {}}) == ""
    assert "性能指标" in core._format_agent_event_text({"type": "performance_metric", "payload": {"name": "label"}})
    assert "latency" in core._format_agent_event_text({"type": "performance_metric", "payload": {"name": "latency", "value": 1, "unit": "ms"}})
    assert "🎉" in core._format_agent_event_text({"type": "result", "payload": {"message": "ok"}})
    assert core._format_agent_event_text({"type": "result", "payload": {"message": ""}}) == ""
    assert "错误" in core._format_agent_event_text({"type": "error", "payload": {"message": "bad"}})
    assert core._format_agent_event_text({"type": "status", "payload": {"message": "hi"}}) == "hi\n"
    assert core._format_agent_event_text({"type": "run_finished", "payload": {}}) == ""
    assert core._format_agent_event_text({"type": "other", "payload": {}}) == ""

    core._handle_agent_event({"type": "status", "payload": {"message": "m"}})
    assert core._output_signal.calls == [("m\n",)]


def test_core_on_closing_and_run():
    core = ControllerCore.__new__(ControllerCore)
    calls = []
    core.terminate_operation = lambda: calls.append("terminate")
    core.agent_event_emitter = SimpleNamespace(off=lambda fn: calls.append(("off", fn)))
    core._handle_agent_event = lambda *_args, **_kwargs: None
    core.message_timer = SimpleNamespace(stop=lambda: calls.append("stop_timer"))
    core.view = SimpleNamespace(show=lambda: calls.append("show"))
    core.app = SimpleNamespace(exec=lambda: 123)

    evt = SimpleNamespace(accept=lambda: calls.append("accept"))
    core.on_closing(evt)
    assert "terminate" in calls and "accept" in calls

    assert core.run() == 123
    assert "show" in calls

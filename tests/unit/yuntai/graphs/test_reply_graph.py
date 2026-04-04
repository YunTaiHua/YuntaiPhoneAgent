import threading
from types import SimpleNamespace

from yuntai.graphs import reply_graph as mod


class TestReplyGraphDeepBranches:
    def test_reply_graph_init(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph._running = False
        assert graph._running is False
        assert graph.terminate_event.is_set() is False

    def test_reply_graph_stop(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.clear()
        graph.stop()
        assert graph.terminate_event.is_set() is True

    def test_reply_graph_is_running(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph._running = True
        assert graph.is_running() is True

    def test_reply_graph_reset(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.set()
        graph._running = True
        graph.reset()
        assert graph.terminate_event.is_set() is False
        assert graph._running is False

    def test_route_after_check_with_terminate(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.set()
        state = {"terminate_flag": False}
        result = graph._route_after_check(state)
        assert result == "wait"

    def test_route_after_check_with_new_message(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.clear()
        state = {"is_new_message": True}
        result = graph._route_after_check(state)
        assert result == "reply"

    def test_route_after_reply_with_terminate(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.set()
        state = {"terminate_flag": False}
        result = graph._route_after_reply(state)
        assert result == "wait"

    def test_route_after_reply_with_generated(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.clear()
        state = {"generated_reply": "test reply"}
        result = graph._route_after_reply(state)
        assert result == "send"

    def test_route_continue_with_terminate(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.set()
        state = {"terminate_flag": False}
        result = graph._route_continue(state)
        assert result == "end"

    def test_route_continue_should_continue(self):
        graph = mod.ReplyGraph.__new__(mod.ReplyGraph)
        graph.terminate_event = threading.Event()
        graph.terminate_event.clear()
        state = {"should_continue": True}
        result = graph._route_continue(state)
        assert result == "continue"

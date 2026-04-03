from types import SimpleNamespace

from yuntai.callbacks.logging_handler import (
    LoggingCallbackHandler,
    PerformanceCallbackHandler,
    _get_default_log_file,
)


def test_default_log_file_path_and_dir_exists():
    log_file = _get_default_log_file()
    assert "temp" in log_file
    assert "langchain_callbacks_" in log_file


def test_logging_handler_main_callbacks_and_statistics(tmp_path):
    log_file = tmp_path / "cb.log"
    h = LoggingCallbackHandler(log_file=str(log_file), enable_console=False, enable_detailed=True)

    h.on_llm_start({}, ["p1", "p2"], invocation_params={"model": "m1"})
    h.on_llm_end(
        SimpleNamespace(
            llm_output={"token_usage": {"total_tokens": 42}},
            generations=[[SimpleNamespace(text="reply")]],
        )
    )
    h.on_llm_error(RuntimeError("llm"))

    h.on_chain_start({"name": "c"}, {"x": "y"})
    h.on_chain_end({"out": "z"})
    h.on_chain_error(RuntimeError("chain"))

    h.on_tool_start({"name": "t"}, "input")
    h.on_tool_end("output")
    h.on_tool_error(RuntimeError("tool"))

    h.on_agent_action(SimpleNamespace(tool="calc", tool_input={"k": "v"}))
    h.on_agent_finish(SimpleNamespace(return_values={"result": "ok"}))

    stats = h.get_statistics()
    assert stats["llm_calls"] == 1
    assert stats["chain_calls"] == 1
    assert stats["tool_calls"] == 1
    assert stats["agent_actions"] == 1
    assert stats["total_tokens"] == 42

    h.print_summary()
    text = log_file.read_text(encoding="utf-8")
    assert "LLM 调用 #1" in text
    assert "Tool 调用结束" in text
    assert "执行统计摘要" in text

    h.reset_statistics()
    assert h.get_statistics()["total_tokens"] == 0


def test_logging_handler_console_and_write_error(capsys):
    h = LoggingCallbackHandler(log_file="Z:/invalid/path/cb.log", enable_console=True, enable_detailed=False)
    h._log("hello")
    out = capsys.readouterr().out
    assert "hello" in out


def test_logging_handler_non_detailed_and_missing_token_usage(tmp_path):
    log_file = tmp_path / "nodetail.log"
    h = LoggingCallbackHandler(log_file=str(log_file), enable_console=False, enable_detailed=False)

    h.on_llm_start({}, ["prompt"], invocation_params={})
    h.on_llm_end(SimpleNamespace(llm_output=None, generations=[]))
    h.on_chain_start({}, {"k": "v"})
    h.on_chain_end({"ok": True})
    h.on_tool_start({}, "input")
    h.on_tool_end("output")
    h.on_agent_finish(SimpleNamespace(return_values={"r": 1}))

    text = log_file.read_text(encoding="utf-8")
    assert "LLM 调用 #1" in text
    assert "生成内容" not in text
    assert h.get_statistics()["total_tokens"] == 0


def test_performance_handler_timings_and_summary(monkeypatch, tmp_path):
    log_file = tmp_path / "perf.log"
    h = PerformanceCallbackHandler(log_file=str(log_file), enable_console=False, enable_detailed=False)

    times = iter([1.0, 1.4, 2.0, 2.6, 3.0, 3.7])
    monkeypatch.setattr("yuntai.callbacks.logging_handler.time.time", lambda: next(times))

    h.on_llm_start({}, ["p"], invocation_params={"model": "m"})
    h.on_llm_end(SimpleNamespace(llm_output={"token_usage": {"total_tokens": 1}}, generations=[[SimpleNamespace(text="x")]]))

    h.on_chain_start({"name": "c"}, {"in": "v"})
    h.on_chain_end({"out": "v"})

    h.on_tool_start({"name": "t"}, "i")
    h.on_tool_end("o")

    perf = h.get_performance_stats()
    assert perf["llm"]["count"] == 1
    assert perf["chain"]["count"] == 1
    assert perf["tool"]["count"] == 1
    assert perf["llm"]["avg"] > 0

    h.print_performance_summary()
    text = log_file.read_text(encoding="utf-8")
    assert "性能统计摘要" in text
    assert "平均耗时" in text


def test_performance_handler_handles_missing_start_times(tmp_path):
    log_file = tmp_path / "perf_empty.log"
    h = PerformanceCallbackHandler(log_file=str(log_file), enable_console=False, enable_detailed=False)

    h.on_llm_end(SimpleNamespace(llm_output=None, generations=[]))
    h.on_chain_end({})
    h.on_tool_end("x")

    stats = h.get_performance_stats()
    assert stats["llm"]["count"] == 0
    assert stats["chain"]["avg"] == 0
    assert stats["tool"]["max"] == 0

from types import SimpleNamespace

import yuntai.handlers.dynamic_handler as mod
from yuntai.handlers.dynamic_handler import DynamicHandler


class _Text:
    def __init__(self, value=""):
        self._value = value
        self.logs = []

    def toPlainText(self):
        return self._value

    def append(self, msg):
        self.logs.append(msg)

    def clear(self):
        self.logs.clear()

    def textCursor(self):
        return SimpleNamespace(movePosition=lambda *_: None, MoveOperation=SimpleNamespace(End=1))

    def setTextCursor(self, _):
        return None


def _make_handler(components=None):
    h = DynamicHandler.__new__(DynamicHandler)
    components = components or {}
    h.view = SimpleNamespace(get_component=lambda name: components.get(name))
    h.controller = SimpleNamespace(show_toast=lambda *args, **kwargs: None)
    h.image_log_signal = SimpleNamespace(emit=lambda msg: None)
    h.video_log_signal = SimpleNamespace(emit=lambda msg: None)
    h.start_video_result_polling = lambda *args, **kwargs: None
    return h


def test_on_image_update_success_sets_latest_path():
    downloaded = []
    h = _make_handler()
    h.controller = SimpleNamespace(
        media_generator=SimpleNamespace(download_image=lambda url, fn: downloaded.append((url, fn)) or "img.png"),
        show_toast=lambda *args, **kwargs: None,
        latest_image_path=None,
    )

    h._on_image_update({"success": True, "data": {"data": [{"url": "http://u"}]}, "size": "1024", "quality": "hd"})
    assert downloaded and downloaded[0][0] == "http://u"
    assert h.controller.latest_image_path == "img.png"


def test_on_image_update_failure_branch_does_not_raise():
    toasts = []
    log_msgs = []
    h = _make_handler()
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.image_log_signal = SimpleNamespace(emit=lambda msg: log_msgs.append(msg))
    h._on_image_update({"success": False, "message": "bad request"})
    assert toasts and toasts[0][1] == "error"
    assert any("图像生成失败" in x for x in log_msgs)


def test_generate_image_requires_tab_and_prompt():
    toasts = []
    components = {
        "dynamic_tabview": None,
    }
    h = _make_handler(components)
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.generate_image()
    assert toasts and toasts[0][1] == "warning"

    toasts.clear()
    components = {
        "dynamic_tabview": object(),
        "image_prompt_text": _Text(""),
        "image_size_menu": SimpleNamespace(currentText=lambda: "1024x1024"),
        "image_quality_menu": SimpleNamespace(currentText=lambda: "hd"),
        "image_log_text": _Text(),
    }
    h = _make_handler(components)
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.generate_image()
    assert toasts and "图像描述" in toasts[0][0]


def test_on_video_update_fail_and_submit_paths(monkeypatch):
    calls = []
    h = _make_handler()
    h.controller = SimpleNamespace(show_toast=lambda msg, level: calls.append((msg, level)), current_video_task_id=None)
    h.start_video_result_polling = lambda task_id, image_count=0: calls.append((task_id, image_count))

    h._on_video_update({"success": True, "task_status": "FAIL", "message": "image broken"})
    assert calls and calls[0][1] == "error"

    calls.clear()
    h._on_video_update({"success": True, "task_id": "tid-1", "task_status": "PROCESSING", "image_count": 1})
    assert ("tid-1", 1) in calls


class _LineInput:
    def __init__(self, text=""):
        self._text = text

    def text(self):
        return self._text


class _Menu:
    def __init__(self, value):
        self._value = value

    def currentText(self):
        return self._value


class _Check:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self._target = target

    def start(self):
        if self._target:
            self._target()


class _Clicked:
    def __init__(self):
        self.connected = []

    def disconnect(self):
        raise TypeError()

    def connect(self, fn):
        self.connected.append(fn)


class _Btn:
    def __init__(self):
        self.clicked = _Clicked()


def test_generate_video_invalid_fps_and_submit_success(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    toasts = []
    logs = []
    video_log = _Text()
    components = {
        "dynamic_tabview": object(),
        "video_prompt_text": _Text("prompt"),
        "image_url1_entry": _LineInput("http://img1"),
        "image_url2_entry": _LineInput(""),
        "video_size_menu": _Menu("1920x1080"),
        "video_fps_menu": _Menu("oops"),
        "video_quality_menu": _Menu("quality"),
        "video_audio_check": _Check(True),
        "video_log_text": video_log,
    }
    h = _make_handler(components)
    h.video_update_signal = SimpleNamespace(emit=lambda payload: logs.append(payload))
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        media_generator=SimpleNamespace(generate_video=lambda *args: {"success": True, "task_id": "t"}),
    )
    h.generate_video()
    assert video_log.logs and "提交视频生成任务" in video_log.logs[0]
    assert logs and logs[0]["image_count"] == 1


def test_show_panel_and_bind_events_paths(monkeypatch):
    buttons = {
        "generate_image_btn": _Btn(),
        "preview_image_btn": _Btn(),
        "generate_video_btn": _Btn(),
        "preview_video_btn": _Btn(),
    }
    calls = []
    h = _make_handler(buttons)
    h.view = SimpleNamespace(
        get_component=lambda name: buttons.get(name),
        create_dynamic_page=lambda: calls.append("create"),
    )
    h.controller = SimpleNamespace(show_toast=lambda *_a, **_k: None)

    monkeypatch.setattr(mod, "MediaGenerator", lambda *_a, **_k: "mg")

    h.show_panel()
    assert calls == ["create"]
    assert h.controller.media_generator == "mg"
    assert buttons["generate_image_btn"].clicked.connected
    assert buttons["preview_video_btn"].clicked.connected


def test_show_panel_exception_and_generate_image_missing_components(monkeypatch):
    toasts = []
    h = _make_handler()
    h.view = SimpleNamespace(
        create_dynamic_page=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        get_component=lambda _name: None,
    )
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.show_panel()
    assert toasts and toasts[-1][1] == "error"

    toasts.clear()
    comps = {
        "dynamic_tabview": object(),
        "image_prompt_text": _Text("prompt"),
        # missing image_size_menu/image_quality_menu/image_log_text
    }
    h2 = _make_handler(comps)
    h2.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h2.generate_image()
    assert toasts and toasts[-1][1] == "error"


def test_generate_image_exception_in_worker(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    toasts = []
    logs = []
    comps = {
        "dynamic_tabview": object(),
        "image_prompt_text": _Text("prompt"),
        "image_size_menu": _Menu("1024x1024"),
        "image_quality_menu": _Menu("hd"),
        "image_log_text": _Text(),
    }
    h = _make_handler(comps)
    h.image_log_signal = SimpleNamespace(emit=lambda msg: logs.append(msg))
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        media_generator=SimpleNamespace(generate_image=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("img boom"))),
    )

    h.generate_image()
    assert logs and "图像生成出错" in logs[-1]
    assert toasts and toasts[-1][1] == "error"


def test_generate_video_missing_components_and_worker_error(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    toasts = []
    # missing components
    h = _make_handler({"dynamic_tabview": object(), "video_prompt_text": _Text("x")})
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.generate_video()
    assert toasts and toasts[-1][1] == "error"

    # worker error path -> video_error_signal emit
    emitted = []
    toasts.clear()
    comps = {
        "dynamic_tabview": object(),
        "video_prompt_text": _Text("prompt"),
        "image_url1_entry": _LineInput("http://img1"),
        "image_url2_entry": _LineInput(""),
        "video_size_menu": _Menu("1920x1080"),
        "video_fps_menu": _Menu("30"),
        "video_quality_menu": _Menu("quality"),
        "video_audio_check": _Check(True),
        "video_log_text": _Text(),
    }
    h2 = _make_handler(comps)
    h2.video_error_signal = SimpleNamespace(emit=lambda msg: emitted.append(msg))
    h2.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        media_generator=SimpleNamespace(generate_video=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("video boom"))),
    )
    h2.generate_video()
    assert emitted and "video boom" in emitted[-1]


def test_start_video_result_polling_failure_and_timeout(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    emitted = []
    h = _make_handler()
    h.start_video_result_polling = DynamicHandler.start_video_result_polling.__get__(h, DynamicHandler)
    h.video_log_signal = SimpleNamespace(emit=lambda msg: emitted.append(msg))
    h.controller = SimpleNamespace(
        show_toast=lambda *_a, **_k: None,
        latest_video_path=None,
        latest_video_cover_path=None,
        media_generator=SimpleNamespace(
            wait_for_video_completion=lambda *_a, callback=None, **_k: (
                callback and callback("FAIL", 1, "task", "FAIL", 10),
                {"success": False, "status": "FAIL", "message": "bad"},
            )[1],
        ),
    )
    h.start_video_result_polling("task-2", image_count=1)
    assert emitted

    emitted.clear()
    h.controller.media_generator.wait_for_video_completion = lambda *_a, callback=None, **_k: (
        callback and callback("TIMEOUT", 1, "task", "PROCESSING", 10),
        {"success": False, "status": "PROCESSING", "message": "wait"},
    )[1]
    h.start_video_result_polling("task-3", image_count=1)
    assert emitted


def test_log_signal_slots_handle_component_errors(monkeypatch):
    h = _make_handler({"image_log_text": object(), "video_log_text": object()})
    h._on_image_log_message("x")
    h._on_video_log_message("y")


def test_on_image_update_parse_failure_branch():
    logs = []
    toasts = []
    h = _make_handler()
    h.image_log_signal = SimpleNamespace(emit=lambda msg: logs.append(msg))
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        media_generator=SimpleNamespace(download_image=lambda *_a, **_k: "x"),
    )
    h._on_image_update({"success": True, "data": {}})
    assert logs
    assert any(level == "error" for _, level in toasts)


def test_generate_image_success_and_preview_paths(monkeypatch):
    h = _make_handler()
    toasts = []
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        media_generator=SimpleNamespace(download_image=lambda *_a, **_k: "img.png"),
        latest_image_path=None,
        latest_video_path="video.mp4",
    )

    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    monkeypatch.setattr(mod, "ImagePreviewWindow", lambda _parent, _path: SimpleNamespace(exec=lambda: opened.append("img")))

    h._on_image_update(
        {
            "success": True,
            "data": {"data": [{"url": "http://img"}]},
            "size": "1024",
            "quality": "hd",
        }
    )
    assert h.controller.latest_image_path == "img.png"
    assert any(level == "success" for _, level in toasts)

    h.preview_latest_image()
    h.preview_latest_video()
    assert "img" in opened
    assert any(x.startswith("file:///") for x in opened if isinstance(x, str))


def test_start_video_result_polling_success_download_fail_and_exception(monkeypatch):
    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)

    # success + download success
    logs = []
    toasts = []
    h = _make_handler()
    h.start_video_result_polling = DynamicHandler.start_video_result_polling.__get__(h, DynamicHandler)
    h.video_log_signal = SimpleNamespace(emit=lambda msg: logs.append(msg))
    h.controller = SimpleNamespace(
        show_toast=lambda msg, level: toasts.append((msg, level)),
        latest_video_path=None,
        latest_video_cover_path=None,
        media_generator=SimpleNamespace(
            wait_for_video_completion=lambda *_a, callback=None, **_k: (
                callback and callback("SUCCESS", 1, "task", "SUCCESS", 10),
                {"success": True, "status": "SUCCESS", "video_url": "v", "cover_url": "c"},
            )[1],
            download_video=lambda *_a, **_k: {
                "success": True,
                "video_path": "video.mp4",
                "cover_path": "cover.jpg",
                "video_size": 1.5,
            },
        ),
    )
    h.start_video_result_polling("ok-task", image_count=1)
    assert h.controller.latest_video_path == "video.mp4"
    assert any(level == "success" for _, level in toasts)
    assert logs

    # success + download failure
    logs.clear()
    h.controller.media_generator.download_video = lambda *_a, **_k: {"success": False, "message": "download bad"}
    h.start_video_result_polling("bad-download", image_count=1)
    assert any("下载失败" in x for x in logs)

    # exception in polling
    logs.clear()
    h.controller.media_generator.wait_for_video_completion = lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("poll boom"))
    h.start_video_result_polling("boom", image_count=1)
    assert any("轮询检查出错" in x for x in logs)


def test_on_video_update_failure_hint_and_video_error_and_preview_warnings(monkeypatch):
    logs = []
    toasts = []
    h = _make_handler()
    h.video_log_signal = SimpleNamespace(emit=lambda msg: logs.append(msg))
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))

    h._on_video_update(
        {
            "success": False,
            "message": "1210 参数错误",
            "response_text": "resp" * 100,
        }
    )
    assert any("可能的原因" in x for x in logs)
    assert any("API响应" in x for x in logs)
    assert any(level == "error" for _, level in toasts)

    # video error method
    logs.clear()
    h._on_video_error("bad")
    assert any("视频生成出错" in x for x in logs)

    # preview warning paths
    toasts.clear()
    h.controller = SimpleNamespace(show_toast=lambda msg, level: toasts.append((msg, level)))
    h.preview_latest_image()
    h.preview_latest_video()
    assert len(toasts) >= 2

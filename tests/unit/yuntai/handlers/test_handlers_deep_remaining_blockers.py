from pathlib import Path
from types import SimpleNamespace

import pytest

from yuntai.handlers.connection_handler import ConnectionHandler
from yuntai.handlers.dynamic_handler import DynamicHandler
from yuntai.handlers.tts_handler import TTSHandler


class _ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self._target = target

    def start(self):
        if self._target:
            self._target()


class _Lock:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def test_tts_update_list_delete_and_model_loading_paths(monkeypatch, tmp_path):
    import yuntai.handlers.tts_handler as tts_mod

    monkeypatch.setattr(tts_mod.threading, "Thread", _ImmediateThread)

    output_dir = tmp_path / "tts"
    tts_manager = SimpleNamespace(
        default_tts_config={"output_path": str(output_dir)},
        tts_synthesized_files=[],
        tts_synthesized_files_lock=_Lock(),
        tts_modules_loaded=False,
        tts_modules={},
        get_current_model=lambda k: {"gpt": "g.ckpt", "sovits": "s.pth"}.get(k),
        load_tts_modules=lambda: (True, "ok"),
    )

    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(components={})
    h.task_manager = SimpleNamespace(tts_manager=tts_manager)
    h.update_audio_list_signal = SimpleNamespace(emit=lambda files: setattr(h, "_files", files))
    logs = []
    h.tts_add_log = lambda m: logs.append(m)

    h.tts_update_synthesized_list()
    assert h._files == []

    (output_dir / "a.wav").write_bytes(b"a")
    (output_dir / "b.wav").write_bytes(b"b")
    h.tts_update_synthesized_list()
    assert [item[1] for item in h._files] == ["b.wav", "a.wav"]

    monkeypatch.setattr(tts_mod, "show_confirm_dialog", lambda *a, **k: False)
    h.tts_delete_audio_files()
    assert any("取消" in m for m in logs)

    logs.clear()
    refreshed = []
    h.tts_update_synthesized_list = lambda: refreshed.append(True)
    monkeypatch.setattr(tts_mod, "show_confirm_dialog", lambda *a, **k: True)
    h.tts_delete_audio_files()
    assert refreshed == [True]
    assert any("已删除" in m for m in logs)

    calls = []
    tts_manager.tts_modules = {
        "change_gpt_weights": lambda p: calls.append(("gpt", p)),
        "change_sovits_weights": lambda p: calls.append(("sovits", p)),
    }
    h.tts_load_selected_models()
    assert ("gpt", "g.ckpt") in calls
    assert ("sovits", "s.pth") in calls


def test_tts_start_synthesis_thread_success_and_failure(monkeypatch):
    import yuntai.handlers.tts_handler as tts_mod

    monkeypatch.setattr(tts_mod.threading, "Thread", _ImmediateThread)

    text_box = SimpleNamespace(toPlainText=lambda: "hello")
    tts_manager = SimpleNamespace(
        is_tts_synthesizing=False,
        get_current_model=lambda k: {"gpt": "g", "sovits": "s", "audio": "a.wav", "text": "a.txt"}.get(k),
    )
    logs = []
    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(get_component=lambda name: text_box if name == "tts_text_input" else None)
    h.task_manager = SimpleNamespace(
        tts_manager=tts_manager,
        tts_synthesize_text=lambda *a, **k: (True, "ok.wav"),
    )
    h.tts_add_log = lambda m: logs.append(m)
    h.tts_update_synthesized_list = lambda: logs.append("refresh")
    h.tts_start_synthesis()
    assert "refresh" in logs

    logs.clear()
    h.task_manager.tts_synthesize_text = lambda *a, **k: (False, "bad")
    h.tts_start_synthesis()
    assert any("合成失败" in m for m in logs)


def test_connection_connect_and_detect_paths(monkeypatch):
    import yuntai.handlers.connection_handler as conn_mod

    monkeypatch.setattr(conn_mod.threading, "Thread", _ImmediateThread)

    queue_calls = []
    status_calls = []
    sync_calls = []
    h = ConnectionHandler.__new__(ConnectionHandler)
    h.view = SimpleNamespace(get_component=lambda _name: None)
    h.controller = SimpleNamespace(
        message_queue=SimpleNamespace(put=lambda msg: queue_calls.append(msg)),
        _sync_device_to_task_chain=lambda: sync_calls.append(True),
        show_toast=lambda *_a, **_k: None,
    )
    h.task_manager = SimpleNamespace(connect_device=lambda _cfg: (True, "id", "ok"), detect_devices=lambda _t: ["d1"])
    h._get_connection_config_from_ui = lambda: {"connection_type": "usb"}
    h._update_connection_status_gui = lambda connected: status_calls.append(connected)
    h.connect_device_gui()
    assert status_calls == [True]
    assert sync_calls == [True]
    assert queue_calls and queue_calls[0][0] == "success"

    queue_calls.clear()
    status_calls.clear()
    h.task_manager.connect_device = lambda _cfg: (False, "", "no")
    h.connect_device_gui()
    assert status_calls == [False]
    assert queue_calls and queue_calls[0][0] == "error"

    dialog_calls = []

    class _Dialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def show_result(self, devices, device_type, display):
            dialog_calls.append((devices, device_type, display))

        def exec(self):
            dialog_calls.append(("exec",))

    monkeypatch.setattr(conn_mod, "DeviceDetectDialog", _Dialog)
    h._get_device_type = lambda: "android"
    h._get_device_type_display = lambda: "Android"
    h.detect_devices_gui()
    assert (["d1"], "android", "Android") in dialog_calls


def test_dynamic_video_polling_and_generate_video_paths(monkeypatch):
    import yuntai.handlers.dynamic_handler as dyn_mod

    monkeypatch.setattr(dyn_mod.threading, "Thread", _ImmediateThread)

    logs = []
    toasts = []
    h = DynamicHandler.__new__(DynamicHandler)
    h.video_log_signal = SimpleNamespace(emit=lambda m: logs.append(m))

    media_generator = SimpleNamespace(
        wait_for_video_completion=lambda *a, **k: {
            "success": True,
            "status": "SUCCESS",
            "video_url": "http://v",
            "cover_url": "http://c",
        },
        download_video=lambda *a, **k: {
            "success": True,
            "video_path": "video.mp4",
            "cover_path": "cover.jpg",
            "video_size": 1.2,
        },
        generate_video=lambda *a, **k: {"success": True, "task_id": "tid", "task_status": "PROCESSING"},
    )
    h.controller = SimpleNamespace(
        media_generator=media_generator,
        show_toast=lambda msg, level: toasts.append((msg, level)),
        latest_video_path=None,
        latest_video_cover_path=None,
    )

    h.start_video_result_polling("tid", image_count=1)
    assert h.controller.latest_video_path == "video.mp4"
    assert any("视频生成完成" in m for m in logs)

    logs.clear()
    h.controller.media_generator.wait_for_video_completion = lambda *a, **k: {"success": False, "status": "FAIL", "message": "bad"}
    h.start_video_result_polling("tid")
    assert any("视频生成失败" in m for m in logs)

    logs.clear()
    h.controller.media_generator.wait_for_video_completion = lambda *a, **k: {"success": False, "status": "PROCESSING"}
    h.start_video_result_polling("tid")
    assert any("超时" in m for m in logs)

    emitted = []
    h.video_update_signal = SimpleNamespace(emit=lambda data: emitted.append(data))
    components = {
        "dynamic_tabview": object(),
        "video_prompt_text": SimpleNamespace(toPlainText=lambda: "prompt"),
        "image_url1_entry": SimpleNamespace(text=lambda: "u1"),
        "image_url2_entry": SimpleNamespace(text=lambda: ""),
        "video_size_menu": SimpleNamespace(currentText=lambda: "720p"),
        "video_fps_menu": SimpleNamespace(currentText=lambda: "not-int"),
        "video_quality_menu": SimpleNamespace(currentText=lambda: "std"),
        "video_audio_check": SimpleNamespace(isChecked=lambda: True),
        "video_log_text": SimpleNamespace(clear=lambda: None, append=lambda _m: None),
    }
    h.view = SimpleNamespace(get_component=lambda name: components.get(name))
    h.generate_video()
    assert emitted and emitted[0]["image_count"] == 1


def test_tts_select_callbacks_and_synthesis_guards(monkeypatch):
    import yuntai.handlers.tts_handler as tts_mod

    logs = []
    labels = {
        "tts_gpt_label": SimpleNamespace(text="", setText=lambda v: setattr(labels["tts_gpt_label"], "text", v)),
        "tts_sovits_label": SimpleNamespace(text="", setText=lambda v: setattr(labels["tts_sovits_label"], "text", v)),
        "tts_audio_label": SimpleNamespace(text="", setText=lambda v: setattr(labels["tts_audio_label"], "text", v)),
        "tts_text_label": SimpleNamespace(text="", setText=lambda v: setattr(labels["tts_text_label"], "text", v)),
        "tts_text_input": SimpleNamespace(toPlainText=lambda: "x"),
    }

    class _Mgr:
        def __init__(self):
            self.is_tts_synthesizing = True
            self.tts_files_database = {
                "gpt": {},
                "sovits": {},
                "audio": {},
                "text": {},
            }
            self._cur = {}

        def set_current_model(self, key, value):
            self._cur[key] = value
            return True

        def get_current_model(self, key):
            return self._cur.get(key)

    mgr = _Mgr()
    h = TTSHandler.__new__(TTSHandler)
    h.view = SimpleNamespace(get_component=lambda name: labels.get(name), components={})
    h.task_manager = SimpleNamespace(tts_manager=mgr, tts_synthesize_text=lambda *_a, **_k: (True, "ok"))
    h.tts_add_log = lambda m: logs.append(m)

    h.tts_start_synthesis()
    assert any("合成中" in m for m in logs)

    logs.clear()
    mgr.tts_files_database["gpt"] = {"m.ckpt": "m.ckpt"}
    mgr.tts_files_database["sovits"] = {"s.pth": "s.pth"}
    mgr.tts_files_database["audio"] = {"ref.wav": "ref.wav"}
    mgr.tts_files_database["text"] = {"ref.txt": "ref.txt"}

    monkeypatch.setattr(tts_mod.TTSHandler, "_create_file_selection_popup", lambda _self, _t, d, cb: cb(next(iter(d.keys()))))

    h.tts_select_gpt_model()
    h.tts_select_sovits_model()
    h.tts_select_ref_audio()
    assert labels["tts_gpt_label"].text == "m.ckpt"
    assert labels["tts_sovits_label"].text == "s.pth"
    assert labels["tts_audio_label"].text == "ref.wav"
    assert labels["tts_text_label"].text == "ref.txt"


def test_dynamic_update_error_and_polling_download_failure(monkeypatch):
    import yuntai.handlers.dynamic_handler as dyn_mod

    monkeypatch.setattr(dyn_mod.threading, "Thread", _ImmediateThread)

    logs = []
    toasts = []
    h = DynamicHandler.__new__(DynamicHandler)
    h.video_log_signal = SimpleNamespace(emit=lambda m: logs.append(m))
    h.image_log_signal = SimpleNamespace(emit=lambda m: logs.append(m))
    h.controller = SimpleNamespace(show_toast=lambda m, t: toasts.append((m, t)))

    h._on_video_error("boom")
    assert any("出错" in m for m in logs)
    assert toasts and toasts[-1][1] == "error"

    logs.clear()
    toasts.clear()
    h._on_image_update({"success": True, "data": {}})
    assert any("解析图像数据失败" in m for m in logs)
    assert toasts and toasts[-1][1] == "error"

    logs.clear()
    h.controller = SimpleNamespace(
        media_generator=SimpleNamespace(
            wait_for_video_completion=lambda *_a, **kwargs: (
                kwargs["callback"]("START", 0, "tid", "INIT", 1),
                kwargs["callback"]("WAIT", 1, "tid", "PROCESSING", 10),
                kwargs["callback"]("CHECK", 2, "tid", "PROCESSING", 10),
                kwargs["callback"]("SUCCESS", 3, "tid", "SUCCESS", 10),
                {"success": True, "status": "SUCCESS", "video_url": "u", "cover_url": "c"},
            )[-1],
            download_video=lambda *_a, **_k: {"success": False, "message": "dl bad"},
        ),
        show_toast=lambda m, t: toasts.append((m, t)),
        latest_video_path=None,
        latest_video_cover_path=None,
    )
    h.start_video_result_polling("tid", image_count=0)
    assert any("首次检查" in m for m in logs)
    assert any("第2次检查" in m for m in logs)
    assert any("视频下载失败" in m for m in logs)

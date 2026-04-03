from pathlib import Path
from types import SimpleNamespace

import pytest

from yuntai.processors.media_generator import MediaGenerator


class _Resp:
    def __init__(self, status_code=200, json_data=None, text="", content=b"", headers=None, chunks=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.content = content
        self.headers = headers or {}
        self._chunks = chunks or []

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size=8192):
        del chunk_size
        for c in self._chunks:
            yield c


def test_generate_image_success_and_api_error(monkeypatch, tmp_path):
    mg = MediaGenerator(api_key="k", project_root=tmp_path)

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=200, json_data={"data": [{"url": "u"}]})
    )
    ok = mg.generate_image("cat")
    assert ok["success"] is True

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=500, text="boom")
    )
    bad = mg.generate_image("cat")
    assert bad["success"] is False
    assert "API请求失败" in bad["message"]


def test_download_image_success_and_failure(monkeypatch, tmp_path):
    mg = MediaGenerator(api_key="k", project_root=tmp_path)

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.get",
        lambda *args, **kwargs: _Resp(status_code=200, content=b"img")
    )
    out = mg.download_image("https://img", filename="a")
    assert out.endswith("a.png")
    assert Path(out).exists()

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.get",
        lambda *args, **kwargs: _Resp(status_code=404)
    )
    with pytest.raises(Exception, match="下载图像失败"):
        mg.download_image("https://img", filename="b")


def test_generate_video_validation_and_status_branches(monkeypatch, tmp_path):
    mg = MediaGenerator(api_key="k", project_root=tmp_path)

    too_many = mg.generate_video("p", image_urls=["u1", "u2", "u3"])
    assert too_many["success"] is False

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=200, json_data={"id": "t1", "task_status": "PROCESSING"})
    )
    ok = mg.generate_video("p", image_urls=["http://a", "bad-url"])
    assert ok["success"] is True
    assert ok["task_id"] == "t1"

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=200, json_data={"id": "t2", "task_status": "FAIL", "error": {"message": "m", "code": "c"}})
    )
    fail = mg.generate_video("p")
    assert fail["success"] is False
    assert "任务失败" in fail["message"]

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=200, json_data={"foo": "bar"})
    )
    no_task = mg.generate_video("p")
    assert no_task["success"] is False
    assert "任务ID" in no_task["message"]


def test_check_video_result_and_wait_for_completion(monkeypatch, tmp_path):
    mg = MediaGenerator(api_key="k", project_root=tmp_path)

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.get",
        lambda *args, **kwargs: _Resp(status_code=200, json_data={
            "task_status": "SUCCESS",
            "video_result": [{"cover_image_url": "c", "url": "v"}],
        })
    )
    done = mg.check_video_result("t")
    assert done["success"] is True
    assert done["video_url"] == "v"

    statuses = iter([
        {"success": False, "status": "PROCESSING", "message": "wait"},
        {"success": True, "status": "SUCCESS", "video_url": "v", "cover_url": "c"},
    ])
    monkeypatch.setattr(mg, "check_video_result", lambda *_args: next(statuses))
    monkeypatch.setattr("yuntai.processors.media_generator.time.sleep", lambda *_args: None)
    events = []
    result = mg.wait_for_video_completion("task", image_count=0, interval=0, max_attempts=2, callback=lambda *e: events.append(e))
    assert result["success"] is True
    assert any(e[0] == "SUCCESS" for e in events)


def test_download_video_success_and_failure(monkeypatch, tmp_path):
    mg = MediaGenerator(api_key="k", project_root=tmp_path)

    def _fake_get(url, *args, **kwargs):
        if "cover" in url:
            return _Resp(status_code=200, content=b"cover")
        return _Resp(
            status_code=200,
            headers={"content-length": "4"},
            chunks=[b"ab", b"cd"],
        )

    monkeypatch.setattr("yuntai.processors.media_generator.requests.get", _fake_get)
    ok = mg.download_video("https://video", cover_url="https://cover", filename="v1")
    assert ok["success"] is True
    assert ok["video_path"].endswith("v1.mp4")

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.get",
        lambda *args, **kwargs: _Resp(status_code=500)
    )
    bad = mg.download_video("https://video")
    assert bad["success"] is False


def test_generate_video_error_text_json_and_check_unknown(monkeypatch, tmp_path):
    import json

    mg = MediaGenerator(api_key="k", project_root=tmp_path)

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=400, text=json.dumps({"error": {"message": "bad req"}})),
    )
    bad_json = mg.generate_video("p")
    assert bad_json["success"] is False
    assert "bad req" in bad_json["message"]

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.post",
        lambda *args, **kwargs: _Resp(status_code=400, text="plain"),
    )
    bad_text = mg.generate_video("p")
    assert bad_text["success"] is False
    assert bad_text["message"].startswith("API请求失败")

    monkeypatch.setattr(
        "yuntai.processors.media_generator.requests.get",
        lambda *args, **kwargs: _Resp(status_code=200, json_data={"task_status": "UNKNOWN"}),
    )
    unknown = mg.check_video_result("t")
    assert unknown["success"] is False and "未知状态" in unknown["message"]

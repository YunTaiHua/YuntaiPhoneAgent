"""
测试 yuntai/__init__.py 的动态导入
"""
import pytest


def test_dynamic_import_gui_view():
    """测试动态导入 GUIView"""
    from yuntai import GUIView
    assert GUIView is not None


def test_dynamic_import_gui_controller():
    """测试动态导入 GUIController"""
    from yuntai import GUIController
    assert GUIController is not None


def test_dynamic_import_task_manager():
    """测试动态导入 TaskManager"""
    from yuntai import TaskManager
    assert TaskManager is not None


def test_dynamic_import_main_app():
    """测试动态导入 MainApp"""
    from yuntai import MainApp
    assert MainApp is not None


def test_dynamic_import_simple_output_capture():
    """测试动态导入 SimpleOutputCapture"""
    from yuntai import SimpleOutputCapture
    assert SimpleOutputCapture is not None


def test_dynamic_import_multimodal_processor():
    """测试动态导入 MultimodalProcessor"""
    from yuntai import MultimodalProcessor
    assert MultimodalProcessor is not None


def test_dynamic_import_media_generator():
    """测试动态导入 MediaGenerator"""
    from yuntai import MediaGenerator
    assert MediaGenerator is not None


def test_dynamic_import_image_preview_window():
    """测试动态导入 ImagePreviewWindow"""
    from yuntai import ImagePreviewWindow
    assert ImagePreviewWindow is not None


def test_dynamic_import_video_preview_window():
    """测试动态导入 VideoPreviewWindow"""
    from yuntai import VideoPreviewWindow
    assert VideoPreviewWindow is not None


def test_dynamic_import_audio_processor():
    """测试动态导入 AudioProcessor"""
    from yuntai import AudioProcessor
    assert AudioProcessor is not None


def test_dynamic_import_invalid():
    """测试动态导入不存在的属性"""
    import yuntai
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = yuntai.InvalidClass

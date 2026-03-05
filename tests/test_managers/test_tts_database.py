"""
测试 tts_database.py - TTS数据库管理器
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')

from yuntai.managers.tts_database import TTSDatabaseManager


class TestTTSDatabaseManager:
    """测试 TTSDatabaseManager 类"""

    @pytest.fixture
    def temp_tts_config(self, temp_dir):
        """创建临时TTS配置"""
        return {
            "gpt_model_dir": os.path.join(temp_dir, "gpt_models"),
            "sovits_model_dir": os.path.join(temp_dir, "sovits_models"),
            "ref_audio_root": os.path.join(temp_dir, "ref_audio"),
            "ref_text_root": os.path.join(temp_dir, "ref_text"),
            "output_path": os.path.join(temp_dir, "output"),
        }

    @pytest.fixture
    def database_manager(self, temp_tts_config):
        """创建数据库管理器fixture"""
        return TTSDatabaseManager(temp_tts_config)

    def test_init(self, database_manager, temp_tts_config):
        """测试初始化"""
        assert database_manager.default_tts_config == temp_tts_config
        assert database_manager.tts_files_database is not None
        assert "gpt" in database_manager.tts_files_database
        assert "sovits" in database_manager.tts_files_database
        assert "audio" in database_manager.tts_files_database
        assert "text" in database_manager.tts_files_database

    def test_init_database_structure(self, database_manager):
        """测试数据库结构初始化"""
        assert database_manager.tts_files_database["gpt"] == {}
        assert database_manager.tts_files_database["sovits"] == {}
        assert database_manager.tts_files_database["audio"] == {}
        assert database_manager.tts_files_database["text"] == {}

    def test_init_cache(self, database_manager):
        """测试缓存初始化"""
        assert database_manager._text_cache == {}
        assert database_manager._cache_lock is not None

    def test_init_current_models(self, database_manager):
        """测试当前模型初始化"""
        assert database_manager.current_gpt_model is None
        assert database_manager.current_sovits_model is None
        assert database_manager.current_ref_audio is None
        assert database_manager.current_ref_text is None

    def test_init_synthesized_files(self, database_manager):
        """测试合成文件列表初始化"""
        assert database_manager.tts_synthesized_files == []
        assert database_manager.tts_synthesized_files_lock is not None

    def test_init_tts_files_database_creates_dirs(self, database_manager, temp_tts_config):
        """测试初始化创建目录"""
        database_manager.init_tts_files_database()
        
        for dir_path in [
            temp_tts_config["gpt_model_dir"],
            temp_tts_config["sovits_model_dir"],
            temp_tts_config["ref_audio_root"],
            temp_tts_config["output_path"],
        ]:
            assert os.path.exists(dir_path)

    def test_init_tts_files_database_scans_gpt(self, database_manager, temp_tts_config):
        """测试扫描GPT模型"""
        # 创建测试文件
        os.makedirs(temp_tts_config["gpt_model_dir"], exist_ok=True)
        test_file = os.path.join(temp_tts_config["gpt_model_dir"], "test.ckpt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        database_manager.init_tts_files_database()
        
        assert "test.ckpt" in database_manager.tts_files_database["gpt"]

    def test_init_tts_files_database_scans_sovits(self, database_manager, temp_tts_config):
        """测试扫描SoVITS模型"""
        # 创建测试文件
        os.makedirs(temp_tts_config["sovits_model_dir"], exist_ok=True)
        test_file = os.path.join(temp_tts_config["sovits_model_dir"], "test.pth")
        with open(test_file, 'w') as f:
            f.write("test")
        
        database_manager.init_tts_files_database()
        
        assert "test.pth" in database_manager.tts_files_database["sovits"]

    def test_init_tts_files_database_scans_audio(self, database_manager, temp_tts_config):
        """测试扫描参考音频"""
        # 创建测试文件
        os.makedirs(temp_tts_config["ref_audio_root"], exist_ok=True)
        test_file = os.path.join(temp_tts_config["ref_audio_root"], "test.wav")
        with open(test_file, 'w') as f:
            f.write("test")
        
        database_manager.init_tts_files_database()
        
        assert "test.wav" in database_manager.tts_files_database["audio"]

    def test_init_tts_files_database_scans_text(self, database_manager, temp_tts_config):
        """测试扫描参考文本"""
        # 创建测试文件
        os.makedirs(temp_tts_config["ref_text_root"], exist_ok=True)
        test_file = os.path.join(temp_tts_config["ref_text_root"], "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        database_manager.init_tts_files_database()
        
        assert "test.txt" in database_manager.tts_files_database["text"]

    def test_init_tts_files_database_handles_missing_dirs(self, database_manager):
        """测试处理缺失目录"""
        # 不应该抛出异常
        result = database_manager.init_tts_files_database()
        
        assert result is not None


class TestTTSDatabaseManagerMethods:
    """测试 TTSDatabaseManager 方法"""

    @pytest.fixture
    def database_manager(self, temp_dir):
        """创建数据库管理器fixture"""
        config = {
            "gpt_model_dir": os.path.join(temp_dir, "gpt"),
            "sovits_model_dir": os.path.join(temp_dir, "sovits"),
            "ref_audio_root": os.path.join(temp_dir, "audio"),
            "ref_text_root": os.path.join(temp_dir, "text"),
            "output_path": os.path.join(temp_dir, "output"),
        }
        return TTSDatabaseManager(config)

    def test_set_current_model_gpt(self, database_manager, temp_dir):
        """测试设置GPT模型"""
        # 先创建文件并扫描
        gpt_dir = os.path.join(temp_dir, "gpt")
        os.makedirs(gpt_dir, exist_ok=True)
        test_file = os.path.join(gpt_dir, "model1.ckpt")
        with open(test_file, 'w') as f:
            f.write("test")
        database_manager.init_tts_files_database()
        
        result = database_manager.set_current_model("gpt", "model1.ckpt")
        
        assert result is True
        assert database_manager.current_gpt_model is not None

    def test_set_current_model_sovits(self, database_manager, temp_dir):
        """测试设置SoVITS模型"""
        sovits_dir = os.path.join(temp_dir, "sovits")
        os.makedirs(sovits_dir, exist_ok=True)
        test_file = os.path.join(sovits_dir, "model1.pth")
        with open(test_file, 'w') as f:
            f.write("test")
        database_manager.init_tts_files_database()
        
        result = database_manager.set_current_model("sovits", "model1.pth")
        
        assert result is True
        assert database_manager.current_sovits_model is not None

    def test_set_current_model_audio(self, database_manager, temp_dir):
        """测试设置参考音频"""
        audio_dir = os.path.join(temp_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        test_file = os.path.join(audio_dir, "ref.wav")
        with open(test_file, 'w') as f:
            f.write("test")
        database_manager.init_tts_files_database()
        
        result = database_manager.set_current_model("audio", "ref.wav")
        
        assert result is True
        assert database_manager.current_ref_audio is not None

    def test_set_current_model_text(self, database_manager, temp_dir):
        """测试设置参考文本"""
        text_dir = os.path.join(temp_dir, "text")
        os.makedirs(text_dir, exist_ok=True)
        test_file = os.path.join(text_dir, "ref.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        database_manager.init_tts_files_database()
        
        result = database_manager.set_current_model("text", "ref.txt")
        
        assert result is True
        assert database_manager.current_ref_text is not None

    def test_set_current_model_not_in_database(self, database_manager):
        """测试设置不存在的模型"""
        result = database_manager.set_current_model("gpt", "nonexistent.ckpt")
        
        assert result is False

    def test_get_current_model(self, database_manager, temp_dir):
        """测试获取当前模型"""
        gpt_dir = os.path.join(temp_dir, "gpt")
        os.makedirs(gpt_dir, exist_ok=True)
        test_file = os.path.join(gpt_dir, "test.ckpt")
        with open(test_file, 'w') as f:
            f.write("test")
        database_manager.init_tts_files_database()
        database_manager.set_current_model("gpt", "test.ckpt")
        
        result = database_manager.get_current_model("gpt")
        
        assert result is not None

    def test_get_current_model_none(self, database_manager):
        """测试获取未设置的模型"""
        result = database_manager.get_current_model("gpt")
        
        assert result is None

    def test_add_synthesized_file(self, database_manager):
        """测试添加合成文件"""
        database_manager.add_synthesized_file("/path/to/output.wav")
        
        assert len(database_manager.tts_synthesized_files) == 1
        assert database_manager.tts_synthesized_files[0][0] == "/path/to/output.wav"
        assert database_manager.tts_synthesized_files[0][1] == "output.wav"

    def test_load_synthesized_files(self, database_manager, temp_dir):
        """测试加载合成文件"""
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建测试文件
        with open(os.path.join(output_dir, "test1.wav"), 'w') as f:
            f.write("test")
        with open(os.path.join(output_dir, "test2.wav"), 'w') as f:
            f.write("test")
        
        result = database_manager.load_synthesized_files()
        
        assert len(result) == 2

    def test_get_cached_text(self, database_manager, temp_dir):
        """测试获取缓存的文本内容"""
        text_dir = os.path.join(temp_dir, "text")
        os.makedirs(text_dir, exist_ok=True)
        test_file = os.path.join(text_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试内容")
        
        result = database_manager.get_cached_text(test_file)
        
        assert result == "测试内容"

    def test_get_cached_text_cached(self, database_manager, temp_dir):
        """测试获取缓存的文本内容 - 从缓存"""
        text_dir = os.path.join(temp_dir, "text")
        os.makedirs(text_dir, exist_ok=True)
        test_file = os.path.join(text_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试内容")
        
        # 第一次获取
        database_manager.get_cached_text(test_file)
        
        # 修改文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("新内容")
        
        # 第二次应该从缓存获取
        result = database_manager.get_cached_text(test_file)
        
        assert result == "测试内容"

    def test_get_model_filename(self, database_manager, temp_dir):
        """测试获取模型文件名"""
        gpt_dir = os.path.join(temp_dir, "gpt")
        os.makedirs(gpt_dir, exist_ok=True)
        test_file = os.path.join(gpt_dir, "test.ckpt")
        with open(test_file, 'w') as f:
            f.write("test")
        database_manager.init_tts_files_database()
        database_manager.set_current_model("gpt", "test.ckpt")
        
        result = database_manager.get_model_filename("gpt")
        
        assert result == "test.ckpt"

    def test_get_model_filename_not_set(self, database_manager):
        """测试获取未设置模型的文件名"""
        result = database_manager.get_model_filename("gpt")
        
        assert result == "未选择"


class TestTTSDatabaseManagerEdgeCases:
    """测试 TTSDatabaseManager 边界情况"""

    @pytest.fixture
    def database_manager(self, temp_dir):
        """创建数据库管理器fixture"""
        config = {
            "gpt_model_dir": os.path.join(temp_dir, "gpt"),
            "sovits_model_dir": os.path.join(temp_dir, "sovits"),
            "ref_audio_root": os.path.join(temp_dir, "audio"),
            "ref_text_root": os.path.join(temp_dir, "text"),
            "output_path": os.path.join(temp_dir, "output"),
        }
        return TTSDatabaseManager(config)

    def test_scan_empty_directory(self, database_manager, temp_dir):
        """测试扫描空目录"""
        os.makedirs(os.path.join(temp_dir, "gpt"), exist_ok=True)
        
        database_manager.init_tts_files_database()
        
        assert database_manager.tts_files_database["gpt"] == {}

    def test_scan_nested_directories(self, database_manager, temp_dir):
        """测试扫描嵌套目录"""
        gpt_dir = os.path.join(temp_dir, "gpt")
        nested_dir = os.path.join(gpt_dir, "nested")
        os.makedirs(nested_dir, exist_ok=True)
        
        test_file = os.path.join(nested_dir, "test.ckpt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        database_manager.init_tts_files_database()
        
        assert "test.ckpt" in database_manager.tts_files_database["gpt"]

    def test_scan_ignores_wrong_extensions(self, database_manager, temp_dir):
        """测试忽略错误扩展名"""
        gpt_dir = os.path.join(temp_dir, "gpt")
        os.makedirs(gpt_dir, exist_ok=True)
        
        # 创建错误扩展名的文件
        wrong_file = os.path.join(gpt_dir, "test.txt")
        with open(wrong_file, 'w') as f:
            f.write("test")
        
        database_manager.init_tts_files_database()
        
        assert "test.txt" not in database_manager.tts_files_database["gpt"]

    def test_multiple_audio_formats(self, database_manager, temp_dir):
        """测试多种音频格式"""
        audio_dir = os.path.join(temp_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        
        # 创建不同格式的音频文件
        for ext in ['.wav', '.mp3', '.flac']:
            test_file = os.path.join(audio_dir, f"test{ext}")
            with open(test_file, 'w') as f:
                f.write("test")
        
        database_manager.init_tts_files_database()
        
        assert "test.wav" in database_manager.tts_files_database["audio"]
        assert "test.mp3" in database_manager.tts_files_database["audio"]
        assert "test.flac" in database_manager.tts_files_database["audio"]

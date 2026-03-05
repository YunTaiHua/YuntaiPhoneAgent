"""
测试 task_manager.py - 任务管理器
"""
import pytest
import os
from unittest.mock import MagicMock, patch, PropertyMock

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')


class TestTTSManager:
    """测试 TTSManager"""

    @pytest.fixture
    def mock_tts_manager(self):
        """创建模拟TTS管理器"""
        with patch('yuntai.services.task_manager.TTSDatabaseManager') as MockDB, \
             patch('yuntai.services.task_manager.TTSTextProcessor') as MockText, \
             patch('yuntai.services.task_manager.TTSAudioPlayer') as MockAudio, \
             patch('yuntai.services.task_manager.TTSEngine') as MockEngine:
            
            mock_db = MagicMock()
            mock_text = MagicMock()
            mock_audio = MagicMock()
            mock_engine = MagicMock()
            
            MockDB.return_value = mock_db
            MockText.return_value = mock_text
            MockAudio.return_value = mock_audio
            MockEngine.return_value = mock_engine
            
            from yuntai.services.task_manager import TTSManager
            manager = TTSManager("/fake/project")
            
            manager.database_manager = mock_db
            manager.text_processor = mock_text
            manager.audio_player = mock_audio
            manager.engine = mock_engine
            
            return manager

    def test_tts_manager_init(self, mock_tts_manager):
        """测试TTS管理器初始化"""
        assert mock_tts_manager is not None
        assert mock_tts_manager.project_root == "/fake/project"
        assert mock_tts_manager.tts_enabled is False

    def test_tts_files_database_property(self, mock_tts_manager):
        """测试tts_files_database属性"""
        mock_tts_manager.database_manager.tts_files_database = {}
        result = mock_tts_manager.tts_files_database
        
        assert result == {}

    def test_tts_synthesized_files_property(self, mock_tts_manager):
        """测试tts_synthesized_files属性"""
        mock_tts_manager.database_manager.tts_synthesized_files = []
        result = mock_tts_manager.tts_synthesized_files
        
        assert result == []

    def test_tts_synthesized_files_setter(self, mock_tts_manager):
        """测试tts_synthesized_files设置器"""
        mock_tts_manager.tts_synthesized_files = ["file1.wav"]
        
        mock_tts_manager.database_manager.tts_synthesized_files = ["file1.wav"]

    def test_current_gpt_model_property(self, mock_tts_manager):
        """测试current_gpt_model属性"""
        mock_tts_manager.database_manager.current_gpt_model = "gpt_model.ckpt"
        result = mock_tts_manager.current_gpt_model
        
        assert result == "gpt_model.ckpt"

    def test_current_sovits_model_property(self, mock_tts_manager):
        """测试current_sovits_model属性"""
        mock_tts_manager.database_manager.current_sovits_model = "sovits_model.ckpt"
        result = mock_tts_manager.current_sovits_model
        
        assert result == "sovits_model.ckpt"

    def test_current_ref_audio_property(self, mock_tts_manager):
        """测试current_ref_audio属性"""
        mock_tts_manager.database_manager.current_ref_audio = "ref_audio.wav"
        result = mock_tts_manager.current_ref_audio
        
        assert result == "ref_audio.wav"

    def test_current_ref_text_property(self, mock_tts_manager):
        """测试current_ref_text属性"""
        mock_tts_manager.database_manager.current_ref_text = "ref_text.txt"
        result = mock_tts_manager.current_ref_text
        
        assert result == "ref_text.txt"

    def test_tts_synthesized_files_lock_property(self, mock_tts_manager):
        """测试tts_synthesized_files_lock属性"""
        import threading
        mock_tts_manager.database_manager.tts_synthesized_files_lock = threading.Lock()
        result = mock_tts_manager.tts_synthesized_files_lock
        
        assert result is not None

    def test_is_playing_audio_property(self, mock_tts_manager):
        """测试is_playing_audio属性"""
        mock_tts_manager.audio_player.is_playing_audio = False
        result = mock_tts_manager.is_playing_audio
        
        assert result is False

    def test_tts_modules_property(self, mock_tts_manager):
        """测试tts_modules属性"""
        mock_tts_manager.engine.tts_modules = {}
        result = mock_tts_manager.tts_modules
        
        assert result == {}

    def test_tts_modules_setter(self, mock_tts_manager):
        """测试tts_modules设置器"""
        mock_tts_manager.tts_modules = {"module": "test"}
        
        mock_tts_manager.engine.tts_modules = {"module": "test"}

    def test_is_tts_synthesizing_property(self, mock_tts_manager):
        """测试is_tts_synthesizing属性"""
        mock_tts_manager.engine.is_tts_synthesizing = False
        result = mock_tts_manager.is_tts_synthesizing
        
        assert result is False

    def test_is_tts_synthesizing_setter(self, mock_tts_manager):
        """测试is_tts_synthesizing设置器"""
        mock_tts_manager.is_tts_synthesizing = True
        
        mock_tts_manager.engine.is_tts_synthesizing = True

    def test_init_tts_files_database(self, mock_tts_manager):
        """测试初始化TTS文件数据库"""
        mock_tts_manager.database_manager.init_tts_files_database.return_value = True
        result = mock_tts_manager.init_tts_files_database()
        
        assert result is True

    def test_load_tts_modules(self, mock_tts_manager):
        """测试加载TTS模块"""
        mock_tts_manager.engine.load_tts_modules.return_value = (True, "")
        mock_tts_manager.engine.tts_modules_loaded = True
        mock_tts_manager.engine.tts_available = True
        
        success, message = mock_tts_manager.load_tts_modules()
        
        assert success is True

    def test_load_tts_modules_failure(self, mock_tts_manager):
        """测试加载TTS模块失败"""
        mock_tts_manager.engine.load_tts_modules.return_value = (False, "加载失败")
        mock_tts_manager.engine.tts_modules_loaded = False
        mock_tts_manager.engine.tts_available = False
        
        success, message = mock_tts_manager.load_tts_modules()
        
        assert success is False

    def test_synthesize_text(self, mock_tts_manager):
        """测试合成文本"""
        mock_tts_manager.engine.synthesize_text.return_value = (True, "/output/audio.wav")
        
        success, output = mock_tts_manager.synthesize_text(
            "测试文本", "/ref/audio.wav", "/ref/text.txt", auto_play=False
        )
        
        assert success is True
        assert output == "/output/audio.wav"

    def test_synthesize_text_with_auto_play(self, mock_tts_manager):
        """测试合成文本带自动播放"""
        mock_tts_manager.engine.synthesize_text.return_value = (True, "/output/audio.wav")
        
        success, output = mock_tts_manager.synthesize_text(
            "测试文本", "/ref/audio.wav", "/ref/text.txt", auto_play=True
        )
        
        assert success is True

    def test_clean_text_for_tts(self, mock_tts_manager):
        """测试清理TTS文本"""
        mock_tts_manager.text_processor.clean_text_for_tts.return_value = "清理后文本"
        
        result = mock_tts_manager._clean_text_for_tts("测试文本")
        
        assert result == "清理后文本"

    def test_should_use_segmented_synthesis(self, mock_tts_manager):
        """测试是否使用分段合成"""
        mock_tts_manager.text_processor.should_use_segmented_synthesis.return_value = False
        
        result = mock_tts_manager.should_use_segmented_synthesis("短文本")
        
        assert result is False

    def test_should_use_segmented_synthesis_long(self, mock_tts_manager):
        """测试是否使用分段合成 - 长文本"""
        mock_tts_manager.text_processor.should_use_segmented_synthesis.return_value = True
        
        result = mock_tts_manager.should_use_segmented_synthesis("长文本" * 100)
        
        assert result is True

    def test_play_audio_file(self, mock_tts_manager):
        """测试播放音频文件"""
        mock_tts_manager.play_audio_file("/path/to/audio.wav")
        
        mock_tts_manager.audio_player.play_audio_file.assert_called_once_with("/path/to/audio.wav")

    def test_stop_current_audio_playback(self, mock_tts_manager):
        """测试停止音频播放"""
        mock_tts_manager.audio_player.stop_current_audio_playback.return_value = True
        
        result = mock_tts_manager.stop_current_audio_playback()
        
        assert result is True

    def test_load_synthesized_files(self, mock_tts_manager):
        """测试加载已合成文件"""
        mock_tts_manager.database_manager.load_synthesized_files.return_value = []
        
        result = mock_tts_manager.load_synthesized_files()
        
        assert result == []

    def test_set_current_model(self, mock_tts_manager):
        """测试设置当前模型"""
        mock_tts_manager.database_manager.set_current_model.return_value = True
        
        result = mock_tts_manager.set_current_model("gpt", "model.ckpt")
        
        assert result is True

    def test_get_current_model(self, mock_tts_manager):
        """测试获取当前模型"""
        mock_tts_manager.database_manager.get_current_model.return_value = "model.ckpt"
        
        result = mock_tts_manager.get_current_model("gpt")
        
        assert result == "model.ckpt"

    def test_get_model_filename(self, mock_tts_manager):
        """测试获取模型文件名"""
        mock_tts_manager.database_manager.get_model_filename.return_value = "model.ckpt"
        
        result = mock_tts_manager.get_model_filename("gpt")
        
        assert result == "model.ckpt"

    def test_cleanup(self, mock_tts_manager):
        """测试清理资源"""
        mock_tts_manager.cleanup()
        
        mock_tts_manager.audio_player.cleanup.assert_called_once()


class TestTTSManagerSynthesizeLongText:
    """测试 TTSManager 分段合成"""

    @pytest.fixture
    def mock_tts_manager(self):
        """创建模拟TTS管理器"""
        with patch('yuntai.services.task_manager.TTSDatabaseManager') as MockDB, \
             patch('yuntai.services.task_manager.TTSTextProcessor') as MockText, \
             patch('yuntai.services.task_manager.TTSAudioPlayer') as MockAudio, \
             patch('yuntai.services.task_manager.TTSEngine') as MockEngine:
            
            mock_db = MagicMock()
            mock_text = MagicMock()
            mock_audio = MagicMock()
            mock_engine = MagicMock()
            
            MockDB.return_value = mock_db
            MockText.return_value = mock_text
            MockAudio.return_value = mock_audio
            MockEngine.return_value = mock_engine
            
            from yuntai.services.task_manager import TTSManager
            manager = TTSManager("/fake/project")
            
            manager.database_manager = mock_db
            manager.text_processor = mock_text
            manager.audio_player = mock_audio
            manager.engine = mock_engine
            
            return manager

    def test_synthesize_long_text_serial_single_segment(self, mock_tts_manager):
        """测试分段合成 - 单段"""
        mock_tts_manager.text_processor.clean_text_for_tts.return_value = "测试文本"
        mock_tts_manager.text_processor.split_text_by_numbered_sections.return_value = ["测试文本"]
        mock_tts_manager.engine.synthesize_text.return_value = (True, "/output/audio.wav")
        
        success, output = mock_tts_manager.synthesize_long_text_serial(
            "测试文本", "/ref/audio.wav", "/ref/text.txt"
        )
        
        assert success is True

    def test_synthesize_long_text_serial_multiple_segments(self, mock_tts_manager):
        """测试分段合成 - 多段"""
        mock_tts_manager.text_processor.clean_text_for_tts.return_value = "1. 第一段\n2. 第二段"
        mock_tts_manager.text_processor.split_text_by_numbered_sections.return_value = ["第一段", "第二段"]
        mock_tts_manager.engine.synthesize_text_with_retry.return_value = (True, "/output/segment.wav")
        mock_tts_manager.audio_player.merge_audio_segments.return_value = "/output/merged.wav"
        
        success, output = mock_tts_manager.synthesize_long_text_serial(
            "长文本", "/ref/audio.wav", "/ref/text.txt"
        )
        
        assert success is True

    def test_synthesize_long_text_serial_all_failed(self, mock_tts_manager):
        """测试分段合成 - 全部失败"""
        mock_tts_manager.text_processor.clean_text_for_tts.return_value = "1. 第一段\n2. 第二段"
        mock_tts_manager.text_processor.split_text_by_numbered_sections.return_value = ["第一段", "第二段"]
        mock_tts_manager.engine.synthesize_text_with_retry.return_value = (False, "合成失败")
        
        success, output = mock_tts_manager.synthesize_long_text_serial(
            "长文本", "/ref/audio.wav", "/ref/text.txt"
        )
        
        assert success is False

    def test_synthesize_long_text_serial_exception(self, mock_tts_manager):
        """测试分段合成 - 异常"""
        mock_tts_manager.text_processor.clean_text_for_tts.side_effect = Exception("处理错误")
        
        success, output = mock_tts_manager.synthesize_long_text_serial(
            "长文本", "/ref/audio.wav", "/ref/text.txt"
        )
        
        assert success is False


class TestTTSManagerSpeakTextIntelligently:
    """测试 TTSManager 智能语音合成"""

    @pytest.fixture
    def mock_tts_manager(self):
        """创建模拟TTS管理器"""
        with patch('yuntai.services.task_manager.TTSDatabaseManager') as MockDB, \
             patch('yuntai.services.task_manager.TTSTextProcessor') as MockText, \
             patch('yuntai.services.task_manager.TTSAudioPlayer') as MockAudio, \
             patch('yuntai.services.task_manager.TTSEngine') as MockEngine:
            
            mock_db = MagicMock()
            mock_text = MagicMock()
            mock_audio = MagicMock()
            mock_engine = MagicMock()
            
            MockDB.return_value = mock_db
            MockText.return_value = mock_text
            MockAudio.return_value = mock_audio
            MockEngine.return_value = mock_engine
            
            from yuntai.services.task_manager import TTSManager
            manager = TTSManager("/fake/project")
            
            manager.database_manager = mock_db
            manager.text_processor = mock_text
            manager.audio_player = mock_audio
            manager.engine = mock_engine
            
            return manager

    def test_speak_text_intelligently_no_ref_audio(self, mock_tts_manager):
        """测试智能语音合成 - 无参考音频"""
        mock_tts_manager.get_current_model = MagicMock(side_effect=lambda x: None if x == "audio" else "text")
        
        result = mock_tts_manager.speak_text_intelligently("测试文本")
        
        assert result is False

    def test_speak_text_intelligently_no_ref_text(self, mock_tts_manager):
        """测试智能语音合成 - 无参考文本"""
        mock_tts_manager.get_current_model = MagicMock(side_effect=lambda x: "audio.wav" if x == "audio" else None)
        
        result = mock_tts_manager.speak_text_intelligently("测试文本")
        
        assert result is False

    def test_speak_text_intelligently_tts_disabled(self, mock_tts_manager):
        """测试智能语音合成 - TTS未启用"""
        mock_tts_manager.get_current_model = MagicMock(return_value="model")
        mock_tts_manager.tts_enabled = False
        
        result = mock_tts_manager.speak_text_intelligently("测试文本")
        
        assert result is False

    def test_speak_text_intelligently_short_text(self, mock_tts_manager):
        """测试智能语音合成 - 短文本"""
        mock_tts_manager.get_current_model = MagicMock(return_value="model")
        mock_tts_manager.tts_enabled = True
        mock_tts_manager.should_use_segmented_synthesis = MagicMock(return_value=False)
        mock_tts_manager.synthesize_text = MagicMock(return_value=(True, "/output/audio.wav"))
        
        result = mock_tts_manager.speak_text_intelligently("短文本")
        
        assert result is True

    def test_speak_text_intelligently_long_text(self, mock_tts_manager):
        """测试智能语音合成 - 长文本"""
        mock_tts_manager.get_current_model = MagicMock(return_value="model")
        mock_tts_manager.tts_enabled = True
        mock_tts_manager.should_use_segmented_synthesis = MagicMock(return_value=True)
        mock_tts_manager.synthesize_long_text_serial = MagicMock(return_value=(True, "/output/audio.wav"))
        mock_tts_manager.audio_player.play_audio_file = MagicMock()
        
        result = mock_tts_manager.speak_text_intelligently("长文本" * 100)
        
        assert result is True


class TestTaskManager:
    """测试 TaskManager"""

    @pytest.fixture
    def mock_task_manager(self):
        """创建模拟任务管理器"""
        with patch('yuntai.services.task_manager.ConnectionManager') as MockConn, \
             patch('yuntai.services.task_manager.FileManager') as MockFile, \
             patch('yuntai.services.task_manager.AgentExecutor') as MockAgent, \
             patch('yuntai.services.task_manager.Utils') as MockUtils, \
             patch('yuntai.services.task_manager.ZhipuAI') as MockZhipu, \
             patch('yuntai.services.task_manager.TTSManager') as MockTTS:
            
            mock_conn = MagicMock()
            mock_file = MagicMock()
            mock_agent = MagicMock()
            mock_utils = MagicMock()
            mock_tts = MagicMock()
            
            MockConn.return_value = mock_conn
            MockFile.return_value = mock_file
            MockAgent.return_value = mock_agent
            MockUtils.return_value = mock_utils
            MockTTS.return_value = mock_tts
            
            from yuntai.services.task_manager import TaskManager
            manager = TaskManager("/fake/project", "/fake/scrcpy")
            
            manager.connection_manager = mock_conn
            manager.file_manager = mock_file
            manager.tts_manager = mock_tts
            manager.utils = mock_utils
            
            return manager

    def test_task_manager_init(self, mock_task_manager):
        """测试任务管理器初始化"""
        assert mock_task_manager is not None
        assert mock_task_manager.project_root == "/fake/project"
        assert mock_task_manager.scrcpy_path == "/fake/scrcpy"

    def test_set_device_type(self, mock_task_manager):
        """测试设置设备类型"""
        mock_task_manager.set_device_type("harmony")
        
        mock_task_manager.connection_manager.set_device_type.assert_called_once_with("harmony")

    def test_check_initial_connection_usb(self, mock_task_manager):
        """测试检查初始连接 - USB"""
        mock_task_manager.config = {
            "connection_type": "usb",
            "usb_device_id": "device123"
        }
        mock_task_manager.connection_manager.load_connection_config.return_value = mock_task_manager.config
        mock_task_manager.connection_manager.connect_to_device.return_value = (True, "device123", "连接成功")
        
        mock_task_manager.check_initial_connection()
        
        mock_task_manager.connection_manager.load_connection_config.assert_called()

    def test_check_initial_connection_wireless(self, mock_task_manager):
        """测试检查初始连接 - 无线"""
        mock_task_manager.config = {
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.100"
        }
        mock_task_manager.connection_manager.load_connection_config.return_value = mock_task_manager.config
        mock_task_manager.connection_manager.connect_to_device.return_value = (True, "192.168.1.100:5555", "连接成功")
        
        mock_task_manager.check_initial_connection()
        
        mock_task_manager.connection_manager.load_connection_config.assert_called()

    def test_check_initial_connection_no_config(self, mock_task_manager):
        """测试检查初始连接 - 无配置"""
        mock_task_manager.config = {}
        mock_task_manager.connection_manager.load_connection_config.return_value = {}
        
        mock_task_manager.check_initial_connection()
        
        mock_task_manager.connection_manager.load_connection_config.assert_called()

    def test_try_connect_success(self, mock_task_manager):
        """测试尝试连接 - 成功"""
        mock_task_manager.config = {"device_id": "device123"}
        mock_task_manager.connection_manager.connect_to_device.return_value = (True, "device123", "连接成功")
        
        mock_task_manager.try_connect()
        
        assert mock_task_manager.is_connected is True
        assert mock_task_manager.device_id == "device123"

    def test_try_connect_failure(self, mock_task_manager):
        """测试尝试连接 - 失败"""
        mock_task_manager.config = {"device_id": "device123"}
        mock_task_manager.connection_manager.connect_to_device.return_value = (False, "", "连接失败")
        
        mock_task_manager.try_connect()
        
        assert mock_task_manager.is_connected is False

    def test_connect_device_success(self, mock_task_manager):
        """测试连接设备 - 成功"""
        config = {"device_id": "device123"}
        mock_task_manager.connection_manager.connect_to_device.return_value = (True, "device123", "连接成功")
        
        success, device_id, message = mock_task_manager.connect_device(config)
        
        assert success is True
        assert device_id == "device123"

    def test_connect_device_failure(self, mock_task_manager):
        """测试连接设备 - 失败"""
        config = {"device_id": "device123"}
        mock_task_manager.connection_manager.connect_to_device.return_value = (False, "", "连接失败")
        
        success, device_id, message = mock_task_manager.connect_device(config)
        
        assert success is False

    def test_detect_devices(self, mock_task_manager):
        """测试检测设备"""
        mock_task_manager.connection_manager.get_available_devices.return_value = ["device1", "device2"]
        
        devices = mock_task_manager.detect_devices("android")
        
        assert len(devices) == 2
        mock_task_manager.connection_manager.set_device_type.assert_called_with("android")

    def test_disconnect_device(self, mock_task_manager):
        """测试断开设备"""
        mock_task_manager.is_connected = True
        mock_task_manager.device_id = "device123"
        
        mock_task_manager.disconnect_device()
        
        assert mock_task_manager.is_connected is False
        assert mock_task_manager.device_id is None

    def test_preload_tts_modules_success(self, mock_task_manager):
        """测试预加载TTS模块 - 成功"""
        mock_task_manager.tts_manager.load_tts_modules.return_value = (True, "")
        
        result = mock_task_manager.preload_tts_modules()
        
        assert result is True
        assert mock_task_manager.tts_manager.tts_enabled is True

    def test_preload_tts_modules_failure(self, mock_task_manager):
        """测试预加载TTS模块 - 失败"""
        mock_task_manager.tts_manager.load_tts_modules.return_value = (False, "加载失败")
        
        result = mock_task_manager.preload_tts_modules()
        
        assert result is False
        assert mock_task_manager.tts_manager.tts_enabled is False

    def test_preload_tts_modules_exception(self, mock_task_manager):
        """测试预加载TTS模块 - 异常"""
        mock_task_manager.tts_manager.load_tts_modules.side_effect = Exception("加载异常")
        
        result = mock_task_manager.preload_tts_modules()
        
        assert result is False
        assert mock_task_manager.tts_manager.tts_enabled is False

    def test_tts_synthesize_text(self, mock_task_manager):
        """测试TTS合成文本"""
        mock_task_manager.tts_manager.synthesize_text.return_value = (True, "/output/audio.wav")
        
        success, output = mock_task_manager.tts_synthesize_text(
            "测试文本", "/ref/audio.wav", "/ref/text.txt"
        )
        
        assert success is True

    def test_play_audio_file(self, mock_task_manager):
        """测试播放音频文件"""
        mock_task_manager.play_audio_file("/path/to/audio.wav")
        
        mock_task_manager.tts_manager.play_audio_file.assert_called_once()

    def test_stop_audio_playback(self, mock_task_manager):
        """测试停止音频播放"""
        mock_task_manager.tts_manager.stop_current_audio_playback.return_value = True
        
        result = mock_task_manager.stop_audio_playback()
        
        assert result is True

    def test_cleanup(self, mock_task_manager):
        """测试清理资源"""
        mock_task_manager.stop_audio_playback = MagicMock(return_value=True)
        
        mock_task_manager.cleanup()
        
        mock_task_manager.stop_audio_playback.assert_called()

    def test_setup_connection(self, mock_task_manager):
        """测试设置连接"""
        # setup_connection只是打印消息，不应该抛出异常
        mock_task_manager.setup_connection()


class TestTaskManagerArgs:
    """测试 TaskManager Args"""

    def test_args_init(self):
        """测试Args初始化"""
        with patch('yuntai.services.task_manager.ConnectionManager'), \
             patch('yuntai.services.task_manager.FileManager'), \
             patch('yuntai.services.task_manager.AgentExecutor'), \
             patch('yuntai.services.task_manager.Utils'), \
             patch('yuntai.services.task_manager.ZhipuAI'), \
             patch('yuntai.services.task_manager.TTSManager'):
            
            from yuntai.services.task_manager import TaskManager
            manager = TaskManager("/fake/project", "/fake/scrcpy")
            
            assert manager.task_args is not None
            assert hasattr(manager.task_args, 'device_id')
            assert hasattr(manager.task_args, 'model')
            assert hasattr(manager.task_args, 'apikey')

    def test_args_default_values(self):
        """测试Args默认值"""
        with patch('yuntai.services.task_manager.ConnectionManager'), \
             patch('yuntai.services.task_manager.FileManager'), \
             patch('yuntai.services.task_manager.AgentExecutor'), \
             patch('yuntai.services.task_manager.Utils'), \
             patch('yuntai.services.task_manager.ZhipuAI'), \
             patch('yuntai.services.task_manager.TTSManager'):
            
            from yuntai.services.task_manager import TaskManager
            manager = TaskManager("/fake/project", "/fake/scrcpy")
            
            assert manager.task_args.device_id is None
            assert manager.task_args.usb is False
            assert manager.task_args.wireless is False

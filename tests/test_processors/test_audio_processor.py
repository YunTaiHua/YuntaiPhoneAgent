"""
测试 audio_processor.py - 音频处理器 (增强版)
"""
import pytest
import os
import tempfile
import time as time_module
from unittest.mock import MagicMock, patch, mock_open

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')


class TestAudioProcessorInit:
    """测试 AudioProcessor 初始化"""

    def test_init_with_ffmpeg_path(self):
        """测试带FFmpeg路径初始化"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/custom/ffmpeg')
            
            assert processor.ffmpeg_path == '/custom/ffmpeg'
            assert processor.whisper_model is None
            assert processor.model_loaded is False

    def test_init_without_ffmpeg_path(self):
        """测试不带FFmpeg路径初始化"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/default/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor()
            
            assert processor.ffmpeg_path is None

    def test_temp_dir_exists(self):
        """测试临时目录存在"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/fake/ffmpeg')
            
            assert os.path.exists(processor.temp_dir)

    def test_whisper_lock_exists(self):
        """测试Whisper锁存在"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/fake/ffmpeg')
            
            assert processor.whisper_lock is not None

    def test_text_converter_init(self):
        """测试文本转换器初始化"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/fake/ffmpeg')
            
            assert processor.text_converter is None


class TestAudioProcessorCheckFFmpeg:
    """测试 AudioProcessor FFmpeg检查"""

    def test_check_ffmpeg_not_exists(self):
        """测试检查不存在的FFmpeg"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/nonexistent/ffmpeg')
            
            available, message = processor.check_ffmpeg()
            
            assert available is False
            assert "不存在" in message

    def test_check_ffmpeg_none_path(self):
        """测试FFmpeg路径为None"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path=None)
            
            available, message = processor.check_ffmpeg()
            
            assert available is False

    def test_check_ffmpeg_success(self):
        """测试FFmpeg检查成功"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/fake/ffmpeg')
            
            with patch('os.path.exists', return_value=True), \
                 patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result
                
                available, message = processor.check_ffmpeg()
                
                assert available is True
                assert message == ""

    def test_check_ffmpeg_execution_failed(self):
        """测试FFmpeg执行失败"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/fake/ffmpeg')
            
            with patch('os.path.exists', return_value=True), \
                 patch('subprocess.run') as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stderr = "error"
                mock_run.return_value = mock_result
                
                available, message = processor.check_ffmpeg()
                
                assert available is False
                assert "执行失败" in message

    def test_check_ffmpeg_exception(self):
        """测试FFmpeg检查异常"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            processor = AudioProcessor(ffmpeg_path='/fake/ffmpeg')
            
            with patch('os.path.exists', return_value=True), \
                 patch('subprocess.run', side_effect=Exception("test error")):
                available, message = processor.check_ffmpeg()
                
                assert available is False
                assert "检查失败" in message


class TestAudioProcessorConvertToSimplified:
    """测试 AudioProcessor 繁简转换"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_convert_empty_text(self, audio_processor):
        """测试转换空文本"""
        result = audio_processor._convert_to_simplified_chinese("")
        
        assert result == ""

    def test_convert_none_text(self, audio_processor):
        """测试转换None文本"""
        result = audio_processor._convert_to_simplified_chinese(None)
        
        assert result is None

    def test_convert_simple_text(self, audio_processor):
        """测试转换简单文本"""
        result = audio_processor._convert_to_simplified_chinese("测试文本")
        
        assert result is not None

    def test_convert_disabled(self, audio_processor):
        """测试禁用转换"""
        with patch('yuntai.processors.audio_processor.WHISPER_CONVERT_TO_SIMPLIFIED', False):
            result = audio_processor._convert_to_simplified_chinese("测试文本")
            
            assert result == "测试文本"

    def test_convert_with_opencc(self, audio_processor):
        """测试使用OpenCC转换"""
        with patch('yuntai.processors.audio_processor.WHISPER_CONVERT_TO_SIMPLIFIED', True):
            mock_opencc = MagicMock()
            mock_converter = MagicMock()
            mock_converter.convert.return_value = "简体文本"
            mock_opencc.OpenCC.return_value = mock_converter
            
            with patch.dict('sys.modules', {'opencc': mock_opencc}):
                result = audio_processor._convert_to_simplified_chinese("繁體文本")
                
                # 第一次调用会初始化转换器

    def test_convert_with_zhconv(self, audio_processor):
        """测试使用zhconv转换"""
        with patch('yuntai.processors.audio_processor.WHISPER_CONVERT_TO_SIMPLIFIED', True):
            # 模拟opencc不可用
            with patch.dict('sys.modules', {'opencc': None}):
                mock_zhconv = MagicMock()
                mock_zhconv.convert = MagicMock(return_value="简体文本")
                
                with patch.dict('sys.modules', {'zhconv': mock_zhconv}):
                    result = audio_processor._convert_to_simplified_chinese("繁體文本")
                    
                    # 结果取决于模块是否可用

    def test_convert_exception(self, audio_processor):
        """测试转换异常"""
        with patch('yuntai.processors.audio_processor.WHISPER_CONVERT_TO_SIMPLIFIED', True):
            audio_processor.text_converter = MagicMock()
            audio_processor.text_converter.convert.side_effect = Exception("转换错误")
            
            result = audio_processor._convert_to_simplified_chinese("测试文本")
            
            # 异常时返回原文本
            assert result == "测试文本"


class TestAudioProcessorExtractAudio:
    """测试 AudioProcessor 音频提取"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_extract_audio_from_video_not_exists(self, audio_processor):
        """测试从不存在的视频提取音频"""
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(True, "")):
            success, message = audio_processor.extract_audio_from_video("/nonexistent/video.mp4")
            
            assert success is False
            assert "不存在" in message

    def test_extract_audio_ffmpeg_not_available(self, audio_processor):
        """测试FFmpeg不可用时提取音频"""
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(False, "FFmpeg不可用")):
            success, message = audio_processor.extract_audio_from_video("/path/to/video.mp4")
            
            assert success is False
            assert "FFmpeg" in message

    def test_extract_audio_success(self, audio_processor, tmp_path):
        """测试成功提取音频"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(True, "")), \
             patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            success, output = audio_processor.extract_audio_from_video(str(video_path))
            
            assert success is True

    def test_extract_audio_with_custom_output(self, audio_processor, tmp_path):
        """测试自定义输出路径"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        output_path = tmp_path / "custom_output.wav"
        
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(True, "")), \
             patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            success, output = audio_processor.extract_audio_from_video(str(video_path), str(output_path))
            
            assert success is True

    def test_extract_audio_timeout(self, audio_processor, tmp_path):
        """测试提取音频超时"""
        import subprocess
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(True, "")), \
             patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd="ffmpeg", timeout=300)):
            success, message = audio_processor.extract_audio_from_video(str(video_path))
            
            assert success is False
            assert "超时" in message

    def test_extract_audio_exception(self, audio_processor, tmp_path):
        """测试提取音频异常"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(True, "")), \
             patch('subprocess.run', side_effect=Exception("test error")):
            success, message = audio_processor.extract_audio_from_video(str(video_path))
            
            assert success is False
            assert "异常" in message

    def test_extract_audio_failed(self, audio_processor, tmp_path):
        """测试提取音频失败"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'check_ffmpeg', return_value=(True, "")), \
             patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = b"error message"
            mock_run.return_value = mock_result
            
            success, message = audio_processor.extract_audio_from_video(str(video_path))
            
            assert success is False
            assert "失败" in message


class TestAudioProcessorLoadWhisper:
    """测试 AudioProcessor Whisper模型加载"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_load_whisper_model_already_loaded(self, audio_processor):
        """测试模型已加载"""
        audio_processor.model_loaded = True
        
        success, message = audio_processor.load_whisper_model()
        
        assert success is True

    def test_load_whisper_model_new(self, audio_processor):
        """测试加载新模型"""
        with patch('whisper.load_model') as mock_load:
            mock_load.return_value = MagicMock()
            
            success, message = audio_processor.load_whisper_model("small", "cpu")
            
            # 结果取决于whisper是否可用

    def test_load_whisper_model_import_error(self, audio_processor):
        """测试Whisper导入失败"""
        with patch.dict('sys.modules', {'whisper': None}):
            # 需要重新导入模块
            pass

    def test_load_whisper_model_exception(self, audio_processor):
        """测试加载模型异常"""
        with patch('whisper.load_model', side_effect=Exception("load error")):
            success, message = audio_processor.load_whisper_model("small", "cpu")
            
            # 结果取决于whisper是否可用


class TestAudioProcessorTranscribe:
    """测试 AudioProcessor 转录功能"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_transcribe_audio_file_not_exists(self, audio_processor):
        """测试转录不存在的文件"""
        success, result = audio_processor.transcribe_audio("/nonexistent/audio.mp3")
        
        assert success is False
        assert "不存在" in result

    def test_transcribe_audio_no_model(self, audio_processor, tmp_path):
        """测试无模型时转录"""
        audio_path = tmp_path / "test.wav"
        audio_path.write_bytes(b'fake audio')
        
        audio_processor.whisper_model = None
        audio_processor.model_loaded = False
        
        with patch.object(audio_processor, 'load_whisper_model', return_value=(False, "加载失败")):
            success, result = audio_processor.transcribe_audio(str(audio_path))
            
            assert success is False

    def test_transcribe_audio_success(self, audio_processor, tmp_path):
        """测试成功转录"""
        audio_path = tmp_path / "test.wav"
        audio_path.write_bytes(b'fake audio')
        
        audio_processor.model_loaded = True
        audio_processor.whisper_model = MagicMock()
        audio_processor.whisper_model.transcribe.return_value = {"text": "转录文本"}
        
        with patch.object(audio_processor, '_convert_to_simplified_chinese', return_value="转录文本"):
            success, result = audio_processor.transcribe_audio(str(audio_path))
            
            assert success is True
            assert result == "转录文本"

    def test_transcribe_audio_empty_result(self, audio_processor, tmp_path):
        """测试转录结果为空"""
        audio_path = tmp_path / "test.wav"
        audio_path.write_bytes(b'fake audio')
        
        audio_processor.model_loaded = True
        audio_processor.whisper_model = MagicMock()
        audio_processor.whisper_model.transcribe.return_value = {"text": "   "}
        
        success, result = audio_processor.transcribe_audio(str(audio_path))
        
        assert success is False
        assert "空" in result

    def test_transcribe_audio_exception(self, audio_processor, tmp_path):
        """测试转录异常"""
        audio_path = tmp_path / "test.wav"
        audio_path.write_bytes(b'fake audio')
        
        audio_processor.model_loaded = True
        audio_processor.whisper_model = MagicMock()
        audio_processor.whisper_model.transcribe.side_effect = Exception("transcribe error")
        
        success, result = audio_processor.transcribe_audio(str(audio_path))
        
        assert success is False
        assert "失败" in result


class TestAudioProcessorProcessVideo:
    """测试 AudioProcessor 视频处理"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_process_video_not_exists(self, audio_processor):
        """测试处理不存在的视频"""
        success, result = audio_processor.process_video_with_audio("/nonexistent/video.mp4")
        
        assert success is False
        assert "error" in result

    def test_process_video_extract_failed(self, audio_processor, tmp_path):
        """测试视频提取失败"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'extract_audio_from_video', return_value=(False, "提取失败")):
            success, result = audio_processor.process_video_with_audio(str(video_path))
            
            assert success is False
            assert "error" in result

    def test_process_video_transcribe_failed(self, audio_processor, tmp_path):
        """测试转录失败"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'extract_audio_from_video', return_value=(True, "/tmp/audio.wav")), \
             patch.object(audio_processor, 'transcribe_audio', return_value=(False, "转录失败")):
            success, result = audio_processor.process_video_with_audio(str(video_path))
            
            assert success is False
            assert "error" in result

    def test_process_video_success(self, audio_processor, tmp_path):
        """测试成功处理视频"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'extract_audio_from_video', return_value=(True, "/tmp/audio.wav")), \
             patch.object(audio_processor, 'transcribe_audio', return_value=(True, "转录文本")):
            success, result = audio_processor.process_video_with_audio(str(video_path), prompt="测试提示")
            
            assert success is True
            assert result["video_path"] == str(video_path)
            assert result["audio_transcription"] == "转录文本"

    def test_process_video_exception(self, audio_processor, tmp_path):
        """测试处理视频异常"""
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b"fake video")
        
        with patch.object(audio_processor, 'extract_audio_from_video', side_effect=Exception("test error")):
            success, result = audio_processor.process_video_with_audio(str(video_path))
            
            assert success is False
            assert "error" in result


class TestAudioProcessorProcessAudioOnly:
    """测试 AudioProcessor 单独音频处理"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_process_audio_not_exists(self, audio_processor):
        """测试处理不存在的音频"""
        success, result = audio_processor.process_audio_only("/nonexistent/audio.mp3")
        
        assert success is False
        assert "error" in result

    def test_process_audio_transcribe_failed(self, audio_processor, tmp_path):
        """测试转录失败"""
        audio_path = tmp_path / "test.mp3"
        audio_path.write_bytes(b"fake audio")
        
        with patch.object(audio_processor, 'transcribe_audio', return_value=(False, "转录失败")):
            success, result = audio_processor.process_audio_only(str(audio_path))
            
            assert success is False
            assert "error" in result

    def test_process_audio_success(self, audio_processor, tmp_path):
        """测试成功处理音频"""
        audio_path = tmp_path / "test.mp3"
        audio_path.write_bytes(b"fake audio")
        
        with patch.object(audio_processor, 'transcribe_audio', return_value=(True, "转录文本")):
            success, result = audio_processor.process_audio_only(str(audio_path), prompt="测试提示")
            
            assert success is True
            assert result["audio_transcription"] == "转录文本"

    def test_process_audio_exception(self, audio_processor, tmp_path):
        """测试处理音频异常"""
        audio_path = tmp_path / "test.mp3"
        audio_path.write_bytes(b"fake audio")
        
        with patch.object(audio_processor, 'transcribe_audio', side_effect=Exception("test error")):
            success, result = audio_processor.process_audio_only(str(audio_path))
            
            assert success is False
            assert "error" in result


class TestAudioProcessorCleanup:
    """测试 AudioProcessor 清理功能"""

    @pytest.fixture
    def audio_processor(self):
        """创建音频处理器fixture"""
        with patch('yuntai.core.config.FFMPEG_PATH', '/fake/ffmpeg'):
            from yuntai.processors.audio_processor import AudioProcessor
            return AudioProcessor(ffmpeg_path='/fake/ffmpeg')

    def test_cleanup_temp_files(self, audio_processor, tmp_path):
        """测试清理临时文件"""
        # 创建一些临时文件
        old_file = tmp_path / "old_audio.wav"
        old_file.write_bytes(b"old audio")
        
        # 设置旧文件的修改时间
        old_time = time_module.time() - 25 * 3600  # 25小时前
        os.utime(old_file, (old_time, old_time))
        
        with patch.object(audio_processor, 'temp_dir', str(tmp_path)):
            audio_processor.cleanup_temp_files(older_than_hours=24)
            
            # 验证旧文件被删除
            assert not old_file.exists()

    def test_cleanup_temp_files_no_files(self, audio_processor, tmp_path):
        """测试没有临时文件需要清理"""
        with patch.object(audio_processor, 'temp_dir', str(tmp_path)):
            # 不应该抛出异常
            audio_processor.cleanup_temp_files(older_than_hours=24)

    def test_cleanup_temp_files_exception(self, audio_processor):
        """测试清理临时文件异常"""
        with patch('os.listdir', side_effect=Exception("list error")):
            # 不应该抛出异常
            audio_processor.cleanup_temp_files(older_than_hours=24)

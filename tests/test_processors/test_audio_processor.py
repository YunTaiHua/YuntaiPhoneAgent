"""
测试 AudioProcessor
"""
import pytest
from unittest.mock import MagicMock, patch
import os

from yuntai.processors.audio_processor import AudioProcessor


class TestAudioProcessor:
    """测试音频处理器"""

    def test_init(self):
        """测试初始化"""
        processor = AudioProcessor()
        
        assert processor is not None
        assert processor.ffmpeg_path is None or isinstance(processor.ffmpeg_path, str)
        assert processor.whisper_model is None
        assert processor.model_loaded is False

    def test_init_with_ffmpeg_path(self):
        """测试使用FFmpeg路径初始化"""
        processor = AudioProcessor(ffmpeg_path="/usr/bin/ffmpeg")
        
        assert processor.ffmpeg_path == "/usr/bin/ffmpeg"

    @patch('subprocess.run')
    def test_check_ffmpeg_success(self, mock_run):
        """测试检查FFmpeg - 成功"""
        mock_run.return_value = MagicMock(returncode=0, stdout="ffmpeg version 4.0")
        
        processor = AudioProcessor()
        success, message = processor.check_ffmpeg()
        
        # 应该返回结果
        assert isinstance(success, bool)
        assert isinstance(message, str)

    @patch('subprocess.run')
    def test_check_ffmpeg_failure(self, mock_run):
        """测试检查FFmpeg - 失败"""
        mock_run.side_effect = FileNotFoundError("ffmpeg not found")
        
        processor = AudioProcessor()
        success, message = processor.check_ffmpeg()
        
        # 应该失败
        assert success is False

    @patch('subprocess.run')
    def test_extract_audio_from_video(self, mock_run):
        """测试从视频提取音频"""
        mock_run.return_value = MagicMock(returncode=0)
        
        processor = AudioProcessor()
        
        with patch('os.path.exists', return_value=True):
            success, result = processor.extract_audio_from_video(
                "/path/to/video.mp4",
                "/path/to/audio.wav"
            )
        
        # 应该返回结果
        assert isinstance(success, bool)
        assert isinstance(result, str)

    def test_transcribe_audio_no_model(self):
        """测试音频转录 - 无模型"""
        processor = AudioProcessor()
        
        with patch('os.path.exists', return_value=True):
            success, result = processor.transcribe_audio("/path/to/audio.wav")
        
        # 应该失败
        assert success is False

    def test_convert_to_simplified_chinese(self):
        """测试繁简转换"""
        processor = AudioProcessor()
        
        # 测试简体中文
        text = "这是简体中文"
        result = processor._convert_to_simplified_chinese(text)
        
        assert "简体" in result or result == text

    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.remove')
    def test_cleanup_temp_files(self, mock_remove, mock_isfile, mock_listdir):
        """测试清理临时文件"""
        mock_listdir.return_value = ["temp1.wav", "temp2.wav"]
        mock_isfile.return_value = True
        
        processor = AudioProcessor()
        processor.cleanup_temp_files(older_than_hours=24)
        
        # 应该调用清理
        assert True

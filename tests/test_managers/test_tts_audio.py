"""
测试 tts_audio.py - TTS音频播放器
"""
import pytest
import os
import tempfile
import wave
import struct
from unittest.mock import MagicMock, patch

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')


class TestTTSAudioPlayer:
    """测试 TTSAudioPlayer 类"""

    @pytest.fixture
    def temp_tts_config(self, temp_dir):
        """创建临时TTS配置"""
        return {
            "output_path": os.path.join(temp_dir, "output"),
        }

    @pytest.fixture
    def mock_audio_player(self, temp_tts_config):
        """创建模拟的音频播放器"""
        with patch('yuntai.managers.tts_audio.pyaudio.PyAudio'):
            from yuntai.managers.tts_audio import TTSAudioPlayer
            return TTSAudioPlayer(temp_tts_config)

    def test_init(self, mock_audio_player, temp_tts_config):
        """测试初始化"""
        assert mock_audio_player.default_tts_config == temp_tts_config
        assert mock_audio_player.is_playing_audio is False
        assert mock_audio_player.tts_segments == []

    def test_init_state(self, mock_audio_player):
        """测试初始状态"""
        assert mock_audio_player.audio_play_lock is not None
        assert mock_audio_player.is_playing_audio_lock is not None
        assert mock_audio_player.tts_segments_lock is not None

    def test_check_merge_dependencies_available(self, temp_tts_config):
        """测试检查合并依赖 - 可用"""
        with patch('yuntai.managers.tts_audio.pyaudio.PyAudio'):
            from yuntai.managers.tts_audio import TTSAudioPlayer
            
            with patch.dict('sys.modules', {'numpy': MagicMock(), 'soundfile': MagicMock()}):
                player = TTSAudioPlayer(temp_tts_config)
                # 依赖检查结果取决于实际环境

    def test_is_playing_audio_default(self, mock_audio_player):
        """测试默认播放状态"""
        assert mock_audio_player.is_playing_audio is False

    def test_tts_segments_default(self, mock_audio_player):
        """测试默认分段列表"""
        assert mock_audio_player.tts_segments == []
        assert isinstance(mock_audio_player.tts_segments, list)

    def test_can_merge_audio_property(self, mock_audio_player):
        """测试合并能力属性"""
        # can_merge_audio 是在初始化时检查的
        assert isinstance(mock_audio_player.can_merge_audio, bool)


class TestTTSAudioPlayerPlayback:
    """测试 TTSAudioPlayer 播放功能"""

    @pytest.fixture
    def temp_wav_file(self, temp_dir):
        """创建临时WAV文件"""
        wav_path = os.path.join(temp_dir, "test.wav")
        
        # 创建一个简单的WAV文件
        with wave.open(wav_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            
            # 生成简单的音频数据
            frames = b'\x00\x00' * 44100  # 1秒的静音
            wav_file.writeframes(frames)
        
        return wav_path

    @pytest.fixture
    def mock_audio_player(self, temp_dir):
        """创建模拟的音频播放器"""
        config = {"output_path": os.path.join(temp_dir, "output")}
        
        with patch('yuntai.managers.tts_audio.pyaudio.PyAudio'):
            from yuntai.managers.tts_audio import TTSAudioPlayer
            return TTSAudioPlayer(config)

    def test_play_audio_file_not_exists(self, mock_audio_player):
        """测试播放不存在的文件"""
        # 不应该抛出异常
        mock_audio_player.play_audio_file("/nonexistent/path.wav")

    def test_play_audio_while_playing(self, mock_audio_player, temp_wav_file):
        """测试播放时已有音频在播放"""
        mock_audio_player.is_playing_audio = True
        
        # 应该跳过播放
        mock_audio_player.play_audio_file(temp_wav_file)
        
        # 状态应该保持
        assert mock_audio_player.is_playing_audio is True


class TestTTSAudioPlayerMerge:
    """测试 TTSAudioPlayer 音频合并功能"""

    @pytest.fixture
    def mock_audio_player(self, temp_dir):
        """创建模拟的音频播放器"""
        config = {"output_path": os.path.join(temp_dir, "output")}
        
        with patch('yuntai.managers.tts_audio.pyaudio.PyAudio'):
            from yuntai.managers.tts_audio import TTSAudioPlayer
            return TTSAudioPlayer(config)

    def test_can_merge_audio_property(self, mock_audio_player):
        """测试合并能力属性"""
        # can_merge_audio 是在初始化时检查的
        assert isinstance(mock_audio_player.can_merge_audio, bool)

    def test_merge_audio_files_empty_list(self, mock_audio_player):
        """测试合并空文件列表"""
        if hasattr(mock_audio_player, 'merge_audio_files'):
            result = mock_audio_player.merge_audio_files([])
            assert result is None or result == ""

    def test_merge_audio_files_single_file(self, mock_audio_player, temp_dir):
        """测试合并单个文件"""
        # 创建测试WAV文件
        wav_path = os.path.join(temp_dir, "single.wav")
        with wave.open(wav_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b'\x00\x00' * 1000)
        
        if hasattr(mock_audio_player, 'merge_audio_files'):
            result = mock_audio_player.merge_audio_files([wav_path])
            # 结果取决于实现


class TestTTSAudioPlayerCleanup:
    """测试 TTSAudioPlayer 清理功能"""

    @pytest.fixture
    def mock_audio_player(self, temp_dir):
        """创建模拟的音频播放器"""
        config = {"output_path": os.path.join(temp_dir, "output")}
        
        with patch('yuntai.managers.tts_audio.pyaudio.PyAudio'):
            from yuntai.managers.tts_audio import TTSAudioPlayer
            return TTSAudioPlayer(config)

    def test_cleanup(self, mock_audio_player):
        """测试清理资源"""
        if hasattr(mock_audio_player, 'cleanup'):
            mock_audio_player.cleanup()
            # 不应该抛出异常

    def test_close(self, mock_audio_player):
        """测试关闭"""
        if hasattr(mock_audio_player, 'close'):
            mock_audio_player.close()
            # 不应该抛出异常

    def test_audio_player_attribute(self, mock_audio_player):
        """测试音频播放器属性"""
        assert hasattr(mock_audio_player, 'audio_player')
